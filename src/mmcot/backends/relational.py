"""Relational operations on domain tables or materialized intermediate records."""

import json
from collections import defaultdict
from decimal import Decimal

from .database import identifier, rows


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def get_field(record, name):
    return {key.lower(): value for key, value in record.items()}.get(name.lower())


def equal(left, right):
    if left is None or right is None:
        return left is right
    if isinstance(left, (int, float, Decimal)) and not isinstance(left, bool):
        try:
            return Decimal(str(left)) == Decimal(str(right))
        except Exception:
            return False
    return left == right


class RelationalStore:
    def __init__(self, conn, graph):
        self.conn = conn
        self.graph = graph

    def filter_by_field(self, source, field, value):
        field = identifier(field)
        if isinstance(source, str):
            return rows(self.conn, f"SELECT * FROM {self.graph.table(source)} WHERE {field} = %s", (value,))
        return [record for record in source if equal(get_field(record, field), value)]

    def filter_by_numeric_range(self, source, field, minimum=None, maximum=None):
        field = identifier(field)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("Minimum exceeds maximum")
        if isinstance(source, str):
            conditions, params = [], []
            for bound, operator in ((minimum, ">="), (maximum, "<=")):
                if bound is not None:
                    conditions.append(f"{field} {operator} %s")
                    params.append(bound)
            where = " WHERE " + " AND ".join(conditions) if conditions else ""
            return rows(self.conn, f"SELECT * FROM {self.graph.table(source)}{where}", params)
        return [record for record in source if (value := get_field(record, field)) is not None
                and (minimum is None or value >= minimum)
                and (maximum is None or value <= maximum)]

    def group_and_aggregate(self, source, group_field, method="count", agg_field=None):
        group_field = identifier(group_field)
        method = method.lower()
        if method not in ("count", "sum", "avg", "min", "max"):
            raise ValueError(f"Unsupported aggregation: {method}")
        if method != "count" and not agg_field:
            raise ValueError(f"{method} requires agg_field")
        agg_field = identifier(agg_field) if agg_field else None
        key = "count" if method == "count" else f"{method}_{agg_field}"
        if isinstance(source, str):
            expression = "COUNT(*)" if method == "count" else f"{method.upper()}({agg_field})"
            return rows(self.conn,
                f"SELECT {group_field}, {expression} AS {key} FROM {self.graph.table(source)} "
                f"GROUP BY {group_field}")
        groups = defaultdict(list)
        for record in source:
            group = get_field(record, group_field)
            if group is not None:
                groups[group].append(record)
        result = []
        for group, records in groups.items():
            values = [value for record in records if (value := get_field(record, agg_field or "")) is not None]
            if method == "count":
                value = len(records)
            elif not values:
                value = 0 if method in ("sum", "avg") else None
            elif method == "avg":
                value = sum(values) / len(values)
            else:
                value = {"sum": sum, "min": min, "max": max}[method](values)
            result.append({group_field: group, key: value})
        return result

    def join(self, source, target, target_field, source_field):
        source_field, target_field = identifier(source_field), identifier(target_field)
        if not source:
            return []
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise ValueError("Join requires a list of source records")
        if isinstance(target, str):
            normalized = [{key.lower(): value for key, value in record.items()} for record in source]
            result = rows(self.conn,
                f"SELECT s.value AS source_record, to_jsonb(t) AS target_record "
                f"FROM jsonb_array_elements(%s::jsonb) AS s(value) "
                f"JOIN {self.graph.table(target)} t ON t.{target_field}::text = s.value ->> %s",
                (json.dumps(normalized, default=json_default), source_field))
            return [dict(item["source_record"], **item["target_record"]) for item in result]
        return [dict(left, **right) for left in source for right in target
                if get_field(left, source_field) is not None
                and str(get_field(left, source_field)) == str(get_field(right, target_field))]

    def sort_docs_by_field(self, source, field, top_k=None, ascending=False):
        field = identifier(field)
        if top_k is not None and (not isinstance(top_k, int) or top_k < 1):
            raise ValueError("top_k must be a positive integer")
        if isinstance(source, str):
            direction = "ASC" if ascending else "DESC"
            limit = " LIMIT %s" if top_k is not None else ""
            return rows(self.conn,
                f"SELECT * FROM {self.graph.table(source)} WHERE {field} IS NOT NULL "
                f"ORDER BY {field} {direction}{limit}", (top_k,) if top_k is not None else ())
        result = sorted((record for record in source if get_field(record, field) is not None),
                        key=lambda record: get_field(record, field), reverse=not ascending)
        return result[:top_k] if top_k is not None else result
