"""External QA input, failed-run accounting, checkpointing, and CLI checks."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import Mock

from mmcot.benchmark import load_questions, run_benchmark
from mmcot.cli import build_parser, main, validate_experiment
from mmcot.config import DOMAINS
from mmcot.evaluation import evaluate, parse_judgment

class DataTests(unittest.TestCase):
    def test_external_qa_input_preserves_fields(self):
        records = [{"id": 1, "question": "Example question?", "answer": "Example answer",
                    "template_id": 4}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "questions.json"
            path.write_text(json.dumps(records), encoding="utf-8")
            self.assertEqual(load_questions(path), records)

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            path.write_text(json.dumps([{"id": 1, "question": "q", "answer": "a"}] * 2), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_questions(path)


class EvaluationTests(unittest.TestCase):
    def document(self, predictions):
        return {"processed_questions": len(predictions), "total_questions": len(predictions),
                "results": [{"question_id": i, "question": "q", "standard_answer": "42",
                             "query_answer": answer, "status": status}
                            for i, (answer, status) in enumerate(predictions)]}

    def test_incorrect_is_not_correct(self):
        self.assertFalse(parse_judgment("Incorrect"))
        self.assertFalse(parse_judgment("incorrect."))
        self.assertTrue(parse_judgment("Correct"))
        with self.assertRaises(ValueError):
            parse_judgment("Probably Correct, but uncertain")

    def test_failures_remain_in_denominator(self):
        result = evaluate(self.document([("42", "success"), ("42", "step_limit"), ("", "error")]))
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["run_failures"], 2)
        self.assertEqual(result["accuracy"], 1 / 3)

    def test_judge_errors_have_no_final_accuracy(self):
        judge = Mock()
        judge.complete.side_effect = ["Correct", RuntimeError("timeout")]
        result = evaluate(self.document([("42", "success"), ("41", "success")]), judge)
        self.assertIsNone(result["accuracy"])
        self.assertEqual(result["judge_errors"], 1)
        self.assertEqual(result["accuracy_lower_bound"], 0.5)
        self.assertEqual(result["accuracy_upper_bound"], 1)

    def test_incomplete_run_rejected(self):
        document = self.document([("42", "success")])
        document["total_questions"] = 2
        with self.assertRaises(ValueError):
            evaluate(document)

    def test_empty_answer_is_wrong_without_judge_call(self):
        judge = Mock()
        result = evaluate(self.document([("", "success")]), judge)
        self.assertEqual(result["accuracy"], 0)
        judge.complete.assert_not_called()


class ExperimentTests(unittest.TestCase):
    def test_error_checkpoint_is_valid_and_complete(self):
        engine = Mock()
        engine.query.side_effect = [{"status": "success", "query_answer": "42"}, RuntimeError("offline")]
        questions = [{"id": i, "question": "q", "answer": "42"} for i in (1, 2)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "run.json"
            run_benchmark(engine, questions, path, {"method": "base"})
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["processed_questions"], 2)
            self.assertEqual(saved["results"][1]["status"], "error")
            self.assertIn("finished_at", saved)

    def test_cli_inspection_without_dependencies(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder:
            for domain in DOMAINS:
                path = Path(folder) / f"{domain}.json"
                path.write_text(json.dumps([{"id": 1, "question": "Example?", "answer": "Answer"}]),
                                encoding="utf-8")
            with redirect_stdout(output):
                main(["inspect-data", "--data-dir", folder])
        inspection = json.loads(output.getvalue())
        self.assertEqual(inspection["total"], len(DOMAINS))
        self.assertEqual(inspection["domains"], {domain: 1 for domain in DOMAINS})

    def test_cli_defaults_match_supplied_batch_scripts(self):
        parser = build_parser()
        for method, expected in (("mmcot", 10), ("graph-cot", 15)):
            args = parser.parse_args(["run", "--method", method])
            validate_experiment(parser, args)
            self.assertEqual(args.max_steps, expected)

    def test_cli_rejects_unused_experiment_options(self):
        parser = build_parser()
        args = parser.parse_args(["run", "--method", "base", "--zero-shot"])
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            validate_experiment(parser, args)


if __name__ == "__main__":
    unittest.main()
