"""Small SQL execution layer shared by graph and relational operations."""

import re


def identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return value.lower()


def rows(conn, statement: str, params=()) -> list[dict]:
    with conn.cursor() as cursor:
        cursor.execute(statement, params)
        names = [column[0] for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]
