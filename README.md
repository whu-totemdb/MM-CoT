# MM-CoT

[Repository](https://github.com/whu-totemdb/MM-CoT) · [中文说明](README_zh.md)

Research companion for **MM-CoT: LLM-Guided Coordination of Vector, Graph, and Relational Operations for Scholarly Knowledge Graph Analytics**.

MM-CoT answers scholarly analytical questions by selecting vector retrieval, typed graph traversal, and relational operations in a Thought-Action-Observation loop. This repository contains the controller, four comparison methods, original research prompts and few-shot examples, and a shared experiment/evaluation interface.

Datasets are not distributed in this repository. Supply your own QA files with `--data-dir` when running benchmark experiments or inspecting data. Each `<Domain>.json` file must contain a list of records with `id`, `question`, and `answer` fields; `template_id` is optional.
