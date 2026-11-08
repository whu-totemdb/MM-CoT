"""Answer evaluation with explicit failure accounting and scoring denominators."""

import re

JUDGE_PROMPT = """Please compare whether the standard answer and query answer for the following question are semantically equivalent.

Question: {question}
Standard Answer: {reference}
Query Answer: {prediction}

Comparison Rules:
1. If two answers contain the same information but in different order, consider it correct.
2. If two answers contain the same names, institutions, or numbers with slight format differences, consider it correct.
3. If the query answer contains all key information from the standard answer, consider it correct.
4. If the query answer lacks key information or contains incorrect information, consider it incorrect.
5. For numerical answers, require exact matching.
6. For empty answers or "not found" type responses, if the standard answer is not empty, consider it incorrect.
7. For author lists, ignore differences in "and" and commas, as long as they contain the same names.

Please only answer "Correct" or "Incorrect", do not include other explanations.
"""


def exact_match(reference, prediction):
    # A separate diagnostic; this is not the paper's semantic judge metric.
    normalize = lambda value: " ".join(value.casefold().split())
    return normalize(reference) == normalize(prediction)


def parse_judgment(text):
    match = re.fullmatch(r"\s*(correct|incorrect)[.!]?\s*", text, re.IGNORECASE)
    if not match:
        raise ValueError(f"Judge must return Correct or Incorrect, received {text!r}")
    return match.group(1).lower() == "correct"


def evaluate(document, judge=None):
    if document.get("processed_questions") != document.get("total_questions"):
        raise ValueError("The run is incomplete; finish it before evaluation")
    source = document["results"]
    if len(source) != document["total_questions"] or not source:
        raise ValueError("Run counts do not match its result records")
    checked = []
    for record in source:
        item = dict(record)
        reference, prediction = item["standard_answer"], item["query_answer"]
        if item.get("status") != "success":
            item.update(correct=False, evaluation_status="run_failed")
        elif not prediction.strip():
            item.update(correct=not reference.strip(), evaluation_status="empty_answer")
        elif judge is None:
            item.update(correct=exact_match(reference, prediction), evaluation_status="exact")
        else:
            try:
                raw = judge.complete(JUDGE_PROMPT.format(question=item["question"], reference=reference, prediction=prediction))
                item.update(correct=parse_judgment(raw), judge_response=raw, evaluation_status="judged")
            except Exception as exc:
                item.update(correct=None, evaluation_status="judge_error", evaluation_error=str(exc))
        checked.append(item)
    correct = sum(item["correct"] is True for item in checked)
    judge_errors = sum(item["correct"] is None for item in checked)
    total = len(checked)
    return {"source_metadata": document.get("metadata", {}), "mode": "llm" if judge else "exact",
            "total": total, "correct": correct, "run_failures": sum(item["status"] != "success" for item in checked),
            "judge_errors": judge_errors,
            "accuracy": None if judge_errors else correct / total,
            "accuracy_lower_bound": correct / total,
            "accuracy_upper_bound": (correct + judge_errors) / total,
            "results": checked}
