"""Iterative Thought/Action/Observation controller for MM-CoT and Graph-CoT."""

import json
import logging

from .actions import parse_action
from .backends.relational import get_field, json_default

logger = logging.getLogger(__name__)

GRAPH_ACTIONS = {"RetrieveNode", "NodeDetail", "NeighbourCheck", "EdgeCheck_LinkNode",
                 "EdgeCheck_BetweenNodes", "ShowDetail", "Finish"}
RELATIONAL_ACTIONS = {"FilterByField", "FilterByRange", "GroupAggregate", "Join", "Sort"}


class ReasoningAgent:
    def __init__(self, model, graph, retriever, relation=None, *, zero_shot=False,
                 max_steps=10, max_prompt_tokens=None, token_counter=None):
        if max_steps < 1:
            raise ValueError("max_steps must be positive")
        self.model, self.graph, self.retriever, self.relation = model, graph, retriever, relation
        self.zero_shot, self.max_steps = zero_shot, max_steps
        self.max_prompt_tokens = max_prompt_tokens or (10000 if relation else 3896)
        self.token_counter = token_counter

    def _prompt(self, question, scratchpad, phase):
        from .prompts import graph as graph_prompts, multimod as multimod_prompts
        from .prompts.graph_examples import EXAMPLES as GRAPH_EXAMPLES
        from .prompts.multimod_examples import EXAMPLES as MULTIMOD_EXAMPLES

        module = multimod_prompts if self.relation else graph_prompts
        name = "MultiMod_INSTRUCTION" if self.relation else "Graph_INSTRUCTION"
        if self.zero_shot:
            name += "_ZeroShot"
        examples = MULTIMOD_EXAMPLES if self.relation else GRAPH_EXAMPLES
        return getattr(module, name).format(
            examples="" if self.zero_shot else examples["SubSet"],
            dataset_definition=module.DATASET_DEFINITION["SubSet"], question=question,
            scratchpad=scratchpad, current_phase=phase)

    def _tokens(self, prompt):
        if self.token_counter is None:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            self.token_counter = lambda text: len(encoding.encode(text, disallowed_special=()))
        return self.token_counter(prompt)

    def _source(self, name, results):
        if name.startswith("result_"):
            if name not in results:
                raise ValueError(f"Unknown result reference: {name}")
            value = results[name]
            if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
                raise ValueError(f"{name} is not a record collection")
            return value
        return self.graph.table(name)

    def execute(self, name, args, results):
        allowed = GRAPH_ACTIONS | (RELATIONAL_ACTIONS if self.relation else set())
        if name not in allowed:
            raise ValueError(f"Unsupported action: {name}")
        if name == "ShowDetail":
            if not args or args[0] not in results:
                raise ValueError("ShowDetail requires an existing result_N")
            value = results[args[0]]
            if len(args) > 1:
                records = [value] if isinstance(value, dict) else value
                if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
                    raise ValueError("Attribute selection requires records")
                value = [{field: get_field(row, field) for field in args[1:]} for row in records]
            return value
        graph_functions = {
            "RetrieveNode": self.retriever.get_best_match,
            "NodeDetail": self.graph.check_nodes,
            "NeighbourCheck": self.graph.check_neighbours,
            "EdgeCheck_LinkNode": self.graph.find_edges_link_node,
            "EdgeCheck_BetweenNodes": self.graph.find_edge_between_nodes,
        }
        if name in graph_functions:
            return graph_functions[name](*args)
        if name == "FilterByField":
            source, field, value = args
            return self.relation.filter_by_field(self._source(source, results), field, value)
        if name == "FilterByRange":
            source, field, minimum, maximum = args
            minimum = None if minimum.lower() == "none" else float(minimum)
            maximum = None if maximum.lower() == "none" else float(maximum)
            return self.relation.filter_by_numeric_range(self._source(source, results), field, minimum, maximum)
        if name == "GroupAggregate":
            if not 2 <= len(args) <= 4:
                raise ValueError("GroupAggregate expects two to four arguments")
            source, field = args[:2]
            method = args[2] if len(args) > 2 else "count"
            agg_field = args[3] if len(args) > 3 and args[3].lower() != "none" else None
            return self.relation.group_and_aggregate(self._source(source, results), field, method, agg_field)
        if name == "Join":
            source, target, target_field, source_field = args
            if not source.startswith("result_"):
                raise ValueError("Join source must be result_N")
            return self.relation.join(self._source(source, results), self.graph.table(target), target_field, source_field)
        if name == "Sort":
            if not 2 <= len(args) <= 4:
                raise ValueError("Sort expects two to four arguments")
            source, field = args[:2]
            top_k = int(args[2]) if len(args) > 2 and args[2].lower() != "none" else None
            if len(args) > 3 and args[3].lower() not in ("true", "false"):
                raise ValueError("ascending must be true or false")
            ascending = len(args) > 3 and args[3].lower() == "true"
            return self.relation.sort_docs_by_field(self._source(source, results), field, top_k, ascending)
        raise ValueError(f"Cannot execute action {name}")

    @staticmethod
    def summarize(name, result):
        if name == "RetrieveNode":
            if result:
                node_id, kind = result
                return f"The node for this {kind.lower()} is {kind}/{node_id}."
            return "No matching node found."
        if name == "ShowDetail" or not isinstance(result, list):
            return json.dumps(result, ensure_ascii=False, default=json_default)
        if name == "Sort":
            sample = result[:3]
        elif name == "NeighbourCheck" and len(result) <= 3:
            sample = result
        elif name == "EdgeCheck_BetweenNodes":
            sample = result
        elif name == "EdgeCheck_LinkNode":
            sample = []
        else:
            sample = result[:1]
        return f"Found {len(result)} records. Sample results: " + json.dumps(sample, ensure_ascii=False, default=json_default)

    def query(self, question):
        scratchpad, results, trajectory = "", {}, []
        for step in range(1, self.max_steps + 1):
            prompt = self._prompt(question, scratchpad, "Thought")
            if self._tokens(prompt) > self.max_prompt_tokens:
                return self._result("", "token_limit", scratchpad, trajectory)
            try:
                thought = self.model.complete(prompt)
            except Exception as exc:
                return {**self._result("", "error", scratchpad, trajectory), "error": str(exc)}
            scratchpad += f"\nThought {step}: {thought}"
            action_prompt = self._prompt(question, scratchpad, "Action")
            if self._tokens(action_prompt) > self.max_prompt_tokens:
                return self._result("", "token_limit", scratchpad, trajectory)
            try:
                action = self.model.complete(action_prompt)
            except Exception as exc:
                return {**self._result("", "error", scratchpad, trajectory), "error": str(exc)}
            scratchpad += f"\nAction {step}: {action}"
            event = {"step": step, "thought": thought, "action": action}
            try:
                name, args = parse_action(action)
                if name == "Finish":
                    event["status"] = "finished"
                    trajectory.append(event)
                    return self._result(args[0], "success", scratchpad, trajectory)
                result = self.execute(name, args, results)
                observation = self.summarize(name, result)
                # Match the research implementation: ShowDetail inspects but does not create a new result.
                if name != "ShowDetail":
                    results[f"result_{step}"] = result
                observation = f"result_{step}: {observation}" if name != "ShowDetail" else observation
                event["status"] = "success"
            except Exception as exc:
                observation = f"Error: {exc}"
                event["status"] = "error"
                logger.debug("Tool execution failed", exc_info=True)
            event["observation"] = observation
            trajectory.append(event)
            scratchpad += f"\nObservation {step}: {observation}"
        return self._result("", "step_limit", scratchpad, trajectory)

    @staticmethod
    def _result(answer, status, scratchpad, trajectory):
        return {"query_answer": answer, "status": status,
                "query_process": scratchpad, "trajectory": trajectory}
