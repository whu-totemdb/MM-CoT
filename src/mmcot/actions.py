"""Parse the paper's FunctionName[arguments] interface without evaluating code."""

import ast
import re


def split_arguments(text: str) -> list[str]:
    """Split commas outside quotes/brackets, preserving titles containing commas."""
    parts, start, depth, quote, escaped = [], 0, 0, None, False
    for i, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in "\"'" and not text[start:i].strip():
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0:
                raise ValueError("Unexpected closing bracket in action arguments")
        elif char == "," and depth == 0:
            parts.append(text[start:i].strip())
            start = i + 1
    if quote or depth != 0:
        raise ValueError("Unbalanced quotes or brackets in action arguments")
    parts.append(text[start:].strip())
    return parts


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
    return value


def parse_action(text: str) -> tuple[str, list[str]]:
    match = re.fullmatch(r"\s*(\w+)\[(.*)\]\s*", text, re.DOTALL)
    if not match:
        raise ValueError("Expected exactly one action: FunctionName[arguments]")
    name, body = match.groups()
    if name == "Finish":
        return name, [unquote(body)]
    parts = split_arguments(body)
    if name == "RetrieveNode":
        return name, [unquote(body)]
    name = "NeighbourCheck" if name == "NeighborCheck" else name
    return name, [unquote(part) for part in parts]
