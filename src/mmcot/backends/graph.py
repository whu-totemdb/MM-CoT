"""Typed scholarly graph access through its node and edge tables."""

from ..config import TABLES, domain_suffix
from .database import rows

NODE_KEYS = {"Paper": "paperid", "Author": "authorid", "Affiliation": "affiliationid"}
# Endpoint order also defines citation direction and coauthor symmetry.
EDGES = {
    "PaperAuthor": (("Paper", "paperid"), ("Author", "authorid")),
    "PaperAffiliation": (("Paper", "paperid"), ("Affiliation", "affiliationid")),
    "AuthorAffiliation": (("Author", "authorid"), ("Affiliation", "affiliationid")),
    "Reference": (("Paper", "citing_paperid"), ("Paper", "cited_paperid")),
    "Collab": (("Author", "author1_id"), ("Author", "author2_id")),
}


class GraphStore:
    edge_types = tuple(EDGES)

    def __init__(self, conn, domain: str):
        self.conn = conn
        self.suffix = domain_suffix(domain)

    def table(self, label: str) -> str:
        names = {name.lower(): f"{name.lower()}_{self.suffix}" for name in TABLES}
        for table in tuple(names.values()):
            names[table] = table
        try:
            return names[label.lower()]
        except KeyError:
            raise ValueError(f"Unknown scholarly table: {label!r}") from None

    def check_nodes(self, label, node_id):
        key = NODE_KEYS[label]
        result = rows(self.conn, f"SELECT * FROM {self.table(label)} WHERE {key} = %s", (node_id,))
        return result[0] if result else None

    def check_nodes_batch(self, label, node_ids):
        if not node_ids:
            return []
        key = NODE_KEYS[label]
        return rows(self.conn, f"SELECT * FROM {self.table(label)} WHERE {key} = ANY(%s)",
                    (list(node_ids),))

    def find_edges_link_node(self, label, node_id, edge):
        endpoints = EDGES[edge]
        columns = [column for kind, column in endpoints if kind == label]
        if not columns:
            return []
        where = " OR ".join(f"{column} = %s" for column in columns)
        return rows(self.conn, f"SELECT * FROM {self.table(edge)} WHERE {where}",
                    tuple(node_id for _ in columns))

    def find_edge_between_nodes(self, from_label, from_id, to_label, to_id):
        result = []
        for edge, ((left_type, left), (right_type, right)) in EDGES.items():
            if (from_label, to_label) == (left_type, right_type):
                where = f"{left} = %s AND {right} = %s"
                params = (from_id, to_id)
                if edge == "Collab":
                    where = f"({where}) OR ({left} = %s AND {right} = %s)"
                    params += (to_id, from_id)
                result.extend(rows(self.conn, f"SELECT * FROM {self.table(edge)} WHERE {where}", params))
            elif (from_label, to_label) == (right_type, left_type):
                result.extend(rows(self.conn,
                    f"SELECT * FROM {self.table(edge)} WHERE {right} = %s AND {left} = %s",
                    (from_id, to_id)))
        return result

    def get_edges_from_node(self, label, node_id, edge):
        endpoints = EDGES[edge]
        if label not in [kind for kind, _ in endpoints]:
            return [], [], ""
        linked = self.find_edges_link_node(label, node_id, edge)
        ids, annotated = set(), []
        target_type = ""
        for row in linked:
            for i, (kind, column) in enumerate(endpoints):
                if kind == label and str(row[column]) == str(node_id):
                    target_type, target_column = endpoints[1 - i]
                    ids.add(row[target_column])
                    item = dict(row)
                    if edge == "Reference":
                        item["direction"] = "citing" if i == 0 else "cited"
                    annotated.append(item)
        # Keep a known target type even for an empty edge set.
        if not target_type:
            target_type = endpoints[1][0] if endpoints[0][0] == label else endpoints[0][0]
        return annotated, sorted(ids, key=str), target_type

    def check_neighbours(self, label, node_id, target_label):
        ids = set()
        for edge, endpoints in EDGES.items():
            if sorted(kind for kind, _ in endpoints) != sorted((label, target_label)):
                continue
            _, targets, _ = self.get_edges_from_node(label, node_id, edge)
            ids.update(targets)
        return self.check_nodes_batch(target_label, sorted(ids, key=str))
