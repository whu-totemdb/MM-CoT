"""Validate benchmark inputs and write per-question checkpoints."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .backends.relational import json_default


def load_questions(path):
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError(f"Expected a nonempty QA list: {path}")
    ids = set()
    for item in records:
        if not isinstance(item, dict) or not {"id", "question", "answer"} <= item.keys():
            raise ValueError("Every QA item requires id, question, and answer")
        if not isinstance(item["question"], str) or not item["question"].strip() or not isinstance(item["answer"], str):
            raise ValueError("Questions must be nonempty strings and answers must be strings")
        if item["id"] in ids:
            raise ValueError(f"Duplicate QA id: {item['id']}")
        ids.add(item["id"])
    return records


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=json_default) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_benchmark(engine, questions, output, metadata):
    document = {"metadata": metadata, "started_at": datetime.now(timezone.utc).isoformat(),
                "total_questions": len(questions), "results": []}
    write_json(output, document)
    for item in questions:
        started = time.perf_counter()
        try:
            result = engine.query(item["question"])
        except Exception as exc:
            result = {"query_answer": "", "status": "error", "error": str(exc)}
        document["results"].append({"question_id": item["id"], "question": item["question"],
            "standard_answer": item["answer"], "template_id": item.get("template_id"),
            "query_time": time.perf_counter() - started, **result})
        document["processed_questions"] = len(document["results"])
        write_json(output, document)
    document["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_json(output, document)
    return document


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
