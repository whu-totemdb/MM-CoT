"""One entry point for inspection, individual queries, experiments, and judging."""

import argparse
import json
import logging
import os
from contextlib import ExitStack
from pathlib import Path

from . import __version__
from .benchmark import fingerprint, load_questions, run_benchmark, write_json
from .config import DOMAINS, LLMConfig, connect_database

METHODS = ("mmcot", "graph-cot", "text-rag", "graph-rag", "base")


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Value must be a positive integer")
    return number


def make_engine(args, domain, resources):
    from .llm import ChatModel

    model = ChatModel(LLMConfig.from_env())
    resources.callback(model.close)
    if args.method == "base":
        from .baselines import BaseLLM
        return BaseLLM(model, domain)
    from .backends.graph import GraphStore
    from .backends.vector import NodeRetriever

    conn = connect_database()
    resources.callback(conn.close)
    graph = GraphStore(conn, domain)
    retriever = NodeRetriever(conn, graph)
    if args.method in ("text-rag", "graph-rag"):
        from .baselines import GraphRAG, TextRAG
        return (TextRAG if args.method == "text-rag" else GraphRAG)(model, graph, retriever, args.top_k)
    from .agent import ReasoningAgent
    from .backends.relational import RelationalStore

    relation = RelationalStore(conn, graph) if args.method == "mmcot" else None
    return ReasoningAgent(model, graph, retriever, relation, zero_shot=args.zero_shot,
                          max_steps=args.max_steps, max_prompt_tokens=args.max_prompt_tokens)


def experiment_options(parser):
    parser.add_argument("--method", choices=METHODS, default="mmcot")
    parser.add_argument("--zero-shot", action="store_true")
    parser.add_argument("--max-steps", type=positive, help="Default: 10 for mmcot, 15 for graph-cot")
    parser.add_argument("--max-prompt-tokens", type=positive)
    parser.add_argument("--top-k", type=positive, default=1)


def build_parser():
    parser = argparse.ArgumentParser(description="MM-CoT scholarly knowledge graph research companion")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect-data", help="Validate QA files without API or database access")
    inspect.add_argument("--data-dir", type=Path, default=Path("data/mrbench"))
    query = commands.add_parser("query", help="Answer one question")
    experiment_options(query)
    query.add_argument("--domain", choices=DOMAINS, required=True)
    query.add_argument("--question", required=True)
    query.add_argument("--output", type=Path)
    run = commands.add_parser("run", help="Run benchmark questions and checkpoint every answer")
    experiment_options(run)
    run.add_argument("--domains", nargs="+", choices=(*DOMAINS, "all"), default=["all"])
    run.add_argument("--data-dir", type=Path, default=Path("data/mrbench"))
    run.add_argument("--output-dir", type=Path, default=Path("results"))
    run.add_argument("--limit", type=positive)
    judge = commands.add_parser("evaluate", help="Evaluate one completed experiment file")
    judge.add_argument("input", type=Path)
    judge.add_argument("--mode", choices=("llm", "exact"), default="llm")
    judge.add_argument("--output", type=Path, required=True)
    return parser


def validate_experiment(parser, args):
    if args.method in ("text-rag", "graph-rag", "base") and (
            args.zero_shot or args.max_steps is not None or args.max_prompt_tokens is not None):
        parser.error("Prompting and step/token budgets apply only to mmcot and graph-cot")
    if args.method not in ("text-rag", "graph-rag") and args.top_k != 1:
        parser.error("--top-k applies only to text-rag and graph-rag")
    if args.method in ("mmcot", "graph-cot") and args.max_steps is None:
        args.max_steps = 10 if args.method == "mmcot" else 15


def metadata(args, domain):
    config = LLMConfig.from_env()
    return {"version": __version__, "method": args.method, "domain": domain,
            "zero_shot": args.zero_shot, "max_steps": args.max_steps,
            "max_prompt_tokens": (args.max_prompt_tokens or (10000 if args.method == "mmcot" else 3896))
                                  if args.method in ("mmcot", "graph-cot") else None,
            "top_k": args.top_k, "llm": config.public_metadata(),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    # Help and offline benchmark inspection need only Python's standard library.
    if args.command == "inspect-data":
        counts = {domain: len(load_questions(args.data_dir / f"{domain}.json")) for domain in DOMAINS}
        print(json.dumps({"domains": counts, "total": sum(counts.values())}, indent=2))
        return
    if args.command in ("run", "query"):
        validate_experiment(parser, args)
    if args.env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=False)
    with ExitStack() as resources:
        if args.command == "query":
            result = make_engine(args, args.domain, resources).query(args.question)
            result = {"metadata": metadata(args, args.domain), "question": args.question, **result}
            if args.output:
                write_json(args.output, result)
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        elif args.command == "run":
            domains = DOMAINS if "all" in args.domains else tuple(dict.fromkeys(args.domains))
            # Validate every input and output before making a paid API call.
            jobs = []
            for domain in domains:
                source = args.data_dir / f"{domain}.json"
                questions = load_questions(source)
                if args.limit:
                    questions = questions[:args.limit]
                path = args.output_dir / args.method / domain / "run.json"
                if path.exists():
                    parser.error(f"Output exists: {path}; choose a new --output-dir")
                jobs.append((domain, source, questions, path))
            for domain, source, questions, path in jobs:
                info = metadata(args, domain)
                info.update(data_sha256=fingerprint(source), limit=args.limit)
                with ExitStack() as domain_resources:
                    engine = make_engine(args, domain, domain_resources)
                    run_benchmark(engine, questions, path, info)
                print(f"{domain}: {len(questions)} questions -> {path}")
        else:
            from .evaluation import evaluate
            document = json.loads(args.input.read_text(encoding="utf-8"))
            judge = None
            if args.mode == "llm":
                from .llm import ChatModel
                judge = ChatModel(LLMConfig.from_env(judge=True))
                resources.callback(judge.close)
            result = evaluate(document, judge)
            result["source_sha256"] = fingerprint(args.input)
            if judge:
                result["judge"] = judge.config.public_metadata()
            write_json(args.output, result)
            print(json.dumps({key: value for key, value in result.items() if key != "results"}, indent=2))
