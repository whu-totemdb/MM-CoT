"""Offline regression checks for the refactored controller and data operations."""

import unittest
from unittest.mock import MagicMock, Mock

from mmcot.actions import parse_action, split_arguments
from mmcot.agent import ReasoningAgent
from mmcot.backends.database import identifier
from mmcot.backends.graph import GraphStore
from mmcot.backends.relational import RelationalStore


class ScriptedModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.prompts = []

    def complete(self, prompt):
        self.prompts.append(prompt)
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return value


class ActionTests(unittest.TestCase):
    def test_quoted_comma_and_apostrophe(self):
        name, args = parse_action('FilterByField[Paper, PaperTitle, "Data, models and O\'Brien"]')
        self.assertEqual(name, "FilterByField")
        self.assertEqual(args, ["Paper", "PaperTitle", "Data, models and O'Brien"])

    def test_finish_preserves_nested_json(self):
        self.assertEqual(parse_action('Finish[{"ids": [1, 2]}]'), ("Finish", ['{"ids": [1, 2]}']))

    def test_neighbor_alias_and_whitespace(self):
        self.assertEqual(parse_action("NeighborCheck[Author,42, Paper]"),
                         ("NeighbourCheck", ["Author", "42", "Paper"]))

    def test_retrieve_title_commas(self):
        self.assertEqual(parse_action("RetrieveNode[Data, models and queries]")[1], ["Data, models and queries"])

    def test_multiple_actions_rejected(self):
        with self.assertRaises(ValueError):
            parse_action("RetrieveNode[x] NodeDetail[Paper, 1]")

    def test_bad_brackets_rejected(self):
        for value in ("a] b[", "'unfinished", "x, [y"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                split_arguments(value)

    def test_identifiers_reject_sql_fragments(self):
        self.assertEqual(identifier("CitationCount"), "citationcount")
        with self.assertRaises(ValueError):
            identifier("paper; DROP TABLE paper")


class RelationTests(unittest.TestCase):
    def setUp(self):
        self.store = RelationalStore(None, GraphStore(None, "Biology"))
        self.records = [{"AuthorID": 1, "CitationCount": 5, "Year": 2000},
                        {"AuthorID": 1, "CitationCount": 10, "Year": 2001},
                        {"AuthorID": 2, "CitationCount": None, "Year": 2001},
                        {"AuthorID": 3, "CitationCount": 0, "Year": 2002}]

    def test_numeric_filter_string_matches_integer(self):
        self.assertEqual(len(self.store.filter_by_field(self.records, "authorid", "1")), 2)

    def test_inclusive_range(self):
        selected = self.store.filter_by_numeric_range(self.records, "YEAR", 2001, 2002)
        self.assertEqual(len(selected), 3)

    def test_aggregate(self):
        grouped = self.store.group_and_aggregate(self.records, "AuthorID", "sum", "CitationCount")
        self.assertEqual(grouped, [{"authorid": 1, "sum_citationcount": 15},
                                   {"authorid": 2, "sum_citationcount": 0},
                                   {"authorid": 3, "sum_citationcount": 0}])

    def test_ascending_zero_and_missing_values(self):
        result = self.store.sort_docs_by_field(self.records, "CitationCount", 2, True)
        self.assertEqual([item["CitationCount"] for item in result], [0, 5])

    def test_join_does_not_match_null_keys(self):
        result = self.store.join([{"id": None}, {"id": 1}], [{"other": None}, {"other": "1"}], "other", "id")
        self.assertEqual(result, [{"id": 1, "other": "1"}])

    def test_table_mapping_accepts_only_domain_tables(self):
        self.assertEqual(self.store.graph.table("Paper"), "paper_biology")
        self.assertEqual(self.store.graph.table("paper_biology"), "paper_biology")
        with self.assertRaises(ValueError):
            self.store.graph.table("paper_medicine")

    def test_sql_uses_parameters_for_values(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.description = [("paperid",)]
        cursor.fetchall.return_value = [(7,)]
        store = RelationalStore(conn, GraphStore(conn, "Biology"))
        value = "O'Brien; SELECT 1"
        self.assertEqual(store.filter_by_field("Paper", "PaperTitle", value), [{"paperid": 7}])
        sql, params = cursor.execute.call_args.args
        self.assertNotIn(value, sql)
        self.assertEqual(params, (value,))


class GraphTests(unittest.TestCase):
    def test_reference_direction_uses_column_names(self):
        graph = GraphStore(None, "Biology")
        graph.find_edges_link_node = Mock(return_value=[
            {"extra": "a", "cited_paperid": 2, "citing_paperid": 1},
            {"extra": "b", "cited_paperid": 1, "citing_paperid": 3}])
        edges, ids, kind = graph.get_edges_from_node("Paper", "1", "Reference")
        self.assertEqual(ids, [2, 3])
        self.assertEqual(kind, "Paper")
        self.assertEqual([item["direction"] for item in edges], ["citing", "cited"])

    def test_wrong_endpoint_has_no_edges(self):
        graph = GraphStore(None, "Biology")
        self.assertEqual(graph.get_edges_from_node("Affiliation", "1", "Reference"), ([], [], ""))


class AgentTests(unittest.TestCase):
    def make_agent(self, model, **kwargs):
        graph = GraphStore(None, "Biology")
        retriever = Mock()
        retriever.get_best_match.return_value = ("42", "Paper")
        relation = RelationalStore(None, graph) if kwargs.pop("multimod", True) else None
        return ReasoningAgent(model, graph, retriever, relation, token_counter=lambda text: 1, **kwargs)

    def test_result_chain_and_finish(self):
        model = ScriptedModel(["Locate", "RetrieveNode[Example]", "Answer", "Finish[42]"])
        result = self.make_agent(model).query("What is the ID?")
        self.assertEqual(result["query_answer"], "42")
        self.assertEqual(result["status"], "success")
        self.assertIn("Paper/42", model.prompts[-1])
        self.assertEqual(len(result["trajectory"]), 2)

    def test_step_limit_not_success(self):
        result = self.make_agent(ScriptedModel(["Locate", "RetrieveNode[x]"]), max_steps=1).query("q")
        self.assertEqual(result["status"], "step_limit")
        self.assertEqual(result["query_answer"], "")

    def test_invalid_reference_is_error(self):
        model = ScriptedModel(["Inspect", "ShowDetail[result_99]", "Stop", "Finish[unknown]"])
        result = self.make_agent(model).query("q")
        self.assertEqual(result["trajectory"][0]["status"], "error")
        self.assertIn("existing result_N", result["query_process"])

    def test_graph_controller_rejects_relational_tool(self):
        agent = self.make_agent(ScriptedModel([]), multimod=False)
        with self.assertRaises(ValueError):
            agent.execute("Sort", ["Paper", "Year"], {})

    def test_zero_shot_removes_examples(self):
        agent = self.make_agent(ScriptedModel([]), zero_shot=True)
        self.assertNotIn("(END OF EXAMPLES)", agent._prompt("q", "", "Thought"))

    def test_prompt_budget_halts_before_api(self):
        model = ScriptedModel([])
        agent = self.make_agent(model, max_prompt_tokens=1)
        agent.token_counter = lambda text: 2
        self.assertEqual(agent.query("q")["status"], "token_limit")
        self.assertEqual(model.prompts, [])

    def test_api_error_preserves_partial_trace(self):
        model = ScriptedModel(["Locate", "RetrieveNode[x]", RuntimeError("offline")])
        result = self.make_agent(model).query("q")
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(result["trajectory"]), 1)

    def test_sort_ascending_parsed_as_bool(self):
        agent = self.make_agent(ScriptedModel([]))
        result = agent.execute("Sort", ["result_1", "x", "1", "true"],
                               {"result_1": [{"x": 5}, {"x": 1}]})
        self.assertEqual(result, [{"x": 1}])

    def test_relational_multi_round_query(self):
        model = ScriptedModel([
            "Select papers", "FilterByRange[Paper,Year,2000,2001]",
            "Aggregate citations", "GroupAggregate[result_1,authorid,sum,citationcount]",
            "Find the leader", "Sort[result_2,sum_citationcount,1]",
            "Inspect", "ShowDetail[result_3,authorid,sum_citationcount]",
            "Answer", "Finish[1]",
        ])
        agent = self.make_agent(model)
        filter_sql = Mock(return_value=[{"authorid": 1, "citationcount": 4},
                                      {"authorid": 1, "citationcount": 6},
                                      {"authorid": 2, "citationcount": 8}])
        agent.relation.filter_by_numeric_range = filter_sql
        result = agent.query("Which author has the highest citations?")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["query_answer"], "1")
        self.assertEqual(len(result["trajectory"]), 5)
        self.assertIn('"sum_citationcount": 10', result["trajectory"][3]["observation"])
        filter_sql.assert_called_once_with("paper_biology", "Year", 2000.0, 2001.0)


class BaselineTests(unittest.TestCase):
    def test_text_rag_keeps_zero_attributes(self):
        from mmcot.baselines import TextRAG

        graph, retriever = Mock(), Mock()
        graph.check_nodes.return_value = {"paperid": 7, "citationcount": 0}
        retriever.retrieve_node.return_value = [("7", "Paper")]
        model = ScriptedModel(["Example", "0"])
        result = TextRAG(model, graph, retriever).query("How many citations?")
        self.assertEqual(result["query_answer"], "0")
        self.assertIn("citationcount: 0", result["query_process"])

    def test_graph_rag_adds_one_hop_context(self):
        from mmcot.baselines import GraphRAG

        graph, retriever = Mock(), Mock()
        graph.edge_types = ["PaperAuthor"]
        graph.check_nodes.return_value = {"paperid": 7, "papertitle": "Example"}
        graph.get_edges_from_node.return_value = ([{"paperid": 7, "authorid": 2}], [2], "Author")
        graph.check_nodes_batch.return_value = [{"authorid": 2, "author_name": "A"}]
        retriever.retrieve_node.return_value = [("7", "Paper")]
        result = GraphRAG(ScriptedModel(["Example", "A"]), graph, retriever).query("Who wrote Example?")
        self.assertEqual(result["query_answer"], "A")
        self.assertIn("author_name: A", result["query_process"])
        graph.check_nodes_batch.assert_called_once_with("Author", [2])

    def test_generation_error_is_not_an_answer(self):
        from mmcot.baselines import TextRAG

        baseline = TextRAG(ScriptedModel([RuntimeError("offline")]), Mock(), Mock())
        with self.assertRaises(RuntimeError):
            baseline.generate_answer("q", "context")


if __name__ == "__main__":
    unittest.main()
