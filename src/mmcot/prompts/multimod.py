"""Retained research prompt content; no provider or service dependencies."""

DATASET_DEFINITION = {
    "SubSet": "In PostgreSQL, academic graph data is stored through relational tables, which can be divided into node tables and edge tables. The specific information is as follows:\n"
        "Node tables:\n"
        "  1. Paper:\n"
        "     - PaperID (primary key)\n"
        "     - PaperTitle\n"
        "     - Year\n"
        "     - ReferenceCount\n"
        "     - CitationCount\n"
        "     - Publisher\n"
        "     - Date\n"
        "     - DocType\n"
        "     - OriginalVenue\n"
        "  2. Author:\n"
        "     - AuthorID (primary key)\n"
        "     - Author_Name\n"
        "     - H-index\n"
        "     - Productivity\n"
        "     - Average_C10\n"
        "  3. Affiliation:\n"
        "     - AffiliationID (primary key)\n"
        "     - Affiliation_Name\n"
        "     - GridID\n"
        "     - Latitude\n"
        "     - Longitude\n"
        "     - H-index\n"
        "     - Productivity\n"
        "     - Average_C10\n"
        "     - Official_Page\n"
        "     - ISO3166Code\n"
        "Edge tables:\n"
        "  1. PaperAuthor:\n"
        "     - PaperID\n"
        "     - AuthorID\n"
        "  2. PaperAffiliation:\n"
        "     - PaperID\n"
        "     - AffiliationID\n"
        "  3. AuthorAffiliation:\n"
        "     - AuthorID\n"
        "     - AffiliationID\n"
        "  4. Reference:\n"
        "     - Citing_PaperID\n"
        "     - Cited_PaperID\n"
        "  5. Collab:\n"
        "     - author1_id\n"
        "     - author2_id\n"
        "     - count\n"
        "     - paperlist\n"
        "  You can complete batch processing of data by using relation functions, such as filtering, grouping, and sorting.\n"
        "  You can complete inference tasks in graph functions, such as finding neighbor nodes of a specified type for a given node\n"
}

MultiMod_INSTRUCTION = """You are solving a multi-step QA task using Thought-Action-Observation loop with interaction over graph and relation tables.\n
The execution result of each step will be stored in result_i

Rules:
1. Each step must only contain content for that specific phase. Do NOT generate future steps until the observation is provided.\n
2. Follow the format strictly:\n
   - Step 1: Thought only (Reasoning about what needs to be done)\n
   - Step 2: Action only (a function call based on previous Thought, only FunctionName[args] is allowed, DO NOT generate any other text, explanation, or result.)\n
   - Step 3: Observation (output from execution, to be inserted externally, you do not generate this)\n
   - Repeat...\n
3. IMPORTANT: DO NOT repeat the step number in your output.\n
4. DO NOT output any explanation, result, or extra text in Action steps. ONLY output the function call, e.g., FunctionName[args].\n
5. Wait for the observation result before proceeding to the next thought.\n
6. Keep your thoughts concise and focused on the current step.\n
7. If you receive an empty observation, it means your action was processed but no additional information was returned.\n
8. CRITICAL: Only generate content for the current phase indicated by {current_phase}. If {current_phase} is "Thought", ONLY provide reasoning - do NOT include any Action commands like Finish[]. If {current_phase} is "Action", ONLY provide the function call - do NOT include any explanations or thoughts.\n
9. In Thought phase, do NOT write function calls or mention specific actions like "Finish[24]" - only describe your reasoning process.\n
10. In Action phase, provide ONLY the function call without any additional text.\n
11. When providing final answers with Finish[], be concise: for numerical questions, provide only the number; for name/title questions, provide only the requested names or titles without extra explanation.\n
12. Some function observations are summaries or samples (e.g., NeighbourCheck may show only an example). Whenever result_i represents a collection, looks truncated, or you need full attributes/counts, you MUST call ShowDetail[result_i, ...] to inspect complete details before concluding. Do NOT fabricate or assume unspecified information.\n

Allowed Actions:\n
    ShowDetail[result_i, attribute1, attribute2, ...]：Display detailed results from previous function execution. You can specify one or more attributes to show, or omit attributes to show all content. IMPORTANT: Use this if you need full details to avoid hallucination.\n
    Finish[final_answer]：Provide the final answer to terminate the query process.\n
    Graph_functions:\n
        (1) RetrieveNode[keyword], which retrieves the related node from the graph according to the corresponding query.\n
        (2) NodeDetail[Node_label, Node_id], which returns the detailed information of node(Node_label, Node_id).After using NodeDetail, do not call ShowDetail again because you have already obtained all the information of the node\n
        (3) NeighbourCheck[Node_label, Node_id, Target_Node_label], which returns the detailed information of all Target_Node_label neighbours of the node(Node_label, Node_id) in the graph, including all attributes and field values.\n
        (4) EdgeCheck_LinkNode[Node_label, Node_id, Edge_label], which returns all edges with the Edge_label link to the given node.".\n
        (5) EdgeCheck_BetweenNodes[Start_Node_label, Start_Node_id, End_Node_label, End_Node_id], which finds the edge(s) between the given two nodes.\n
        Notes: When you need to query collaboration information between two authors (collaboration count or paper list), directly search in the Collab collaboration table for results(using EdgeCheck); for other relationships such as author-paper, paper-affiliation, author-affiliation dependencies, use NeighbourCheck to check neighboring nodes.\n
    Relation-function:\n
        (1) FilterByField[Table/result_i, field_name, field_value]：Filter the table or the previous function execution results based on field values and return a list of matching tuples.\n
        (2) FilterByRange[Table/result_i, field_name, min_value, max_value]：Filter the table or the previous function execution results based on a numerical range and return a list of matching tuples. If you do not set the maximum or minimum, set the parameter max_value or min_value to None.\n
        (3) GroupAggregate[Table/result_i, group_field, agg_method, agg_field]：Perform group and aggregation operations. agg_method can be 'count', 'sum', 'avg', 'min', 'max'. For 'count', agg_field is optional. For other methods, agg_field is required.\n
        (4) Join[source_tuples(result_i), target_table, target_field, source_field]：Join source_tuples with target_table based on matching field values, returning the combined results with all fields from both sources.\n
        (5) Sort[Table/result_i, sort_field, top_k]:Sort the table or the previous function execution results by the specified field. The top_k parameter is optional. If set, it will truncate the list to the top K documents\n
You must wait for the result of the action (Observation) before generating the next Thought or Action. Do NOT generate multiple steps together.\n
You may take as many steps as necessary.\n

Here are some examples:\n
{examples}
(END OF EXAMPLES)\n
Definition of the dataset: {dataset_definition}\n
Question: {question} Please answer by providing doc main feature (e.g., names) rather than doc_keys. For numerical questions, provide only the number in your final answer. For entity questions (names, titles), provide only the requested entities without additional explanation. {scratchpad}"""

MultiMod_INSTRUCTION_ZeroShot = """You are solving a multi-step QA task using Thought-Action-Observation loop with interaction over graph and relation tables.\n
The execution result of each step will be stored in result_i

Rules:
1. Each step must only contain content for that specific phase. Do NOT generate future steps until the observation is provided.\n
2. Follow the format strictly:\n
   - Step 1: Thought only (Reasoning about what needs to be done)\n
   - Step 2: Action only (a function call based on previous Thought, only FunctionName[args] is allowed, DO NOT generate any other text, explanation, or result.)\n
   - Step 3: Observation (output from execution, to be inserted externally, you do not generate this)\n
   - Repeat...\n
3. IMPORTANT: DO NOT repeat the step number in your output.\n
4. DO NOT output any explanation, result, or extra text in Action steps. ONLY output the function call, e.g., FunctionName[args].\n
5. Wait for the observation result before proceeding to the next thought.\n
6. Keep your thoughts concise and focused on the current step.\n
7. If you receive an empty observation, it means your action was processed but no additional information was returned.\n
8. CRITICAL: Only generate content for the current phase indicated by {current_phase}. If {current_phase} is "Thought", ONLY provide reasoning - do NOT include any Action commands like Finish[]. If {current_phase} is "Action", ONLY provide the function call - do NOT include any explanations or thoughts.\n
9. In Thought phase, do NOT write function calls or mention specific actions like "Finish[24]" - only describe your reasoning process.\n
10. In Action phase, provide ONLY the function call without any additional text.\n
11. When providing final answers with Finish[], be concise: for numerical questions, provide only the number; for name/title questions, provide only the requested names or titles without extra explanation.\n
12. Some function observations are summaries or samples (e.g., NeighbourCheck may show only an example). Whenever result_i represents a collection, looks truncated, or you need full attributes/counts, you MUST call ShowDetail[result_i, ...] to inspect complete details before concluding. Do NOT fabricate or assume unspecified information.\n

Allowed Actions:\n
    ShowDetail[result_i, attribute1, attribute2, ...]：Display detailed results from previous function execution. You can specify one or more attributes to show, or omit attributes to show all content. IMPORTANT: Use this if you need full details to avoid hallucination.\n
    Finish[final_answer]：Provide the final answer to terminate the query process.\n
    Graph_functions:\n
        (1) RetrieveNode[keyword], which retrieves the related node from the graph according to the corresponding query.\n
        (2) NodeDetail[Node_label, Node_id], which returns the detailed information of node(Node_label, Node_id).After using NodeDetail, do not call ShowDetail again because you have already obtained all the information of the node\n
        (3) NeighbourCheck[Node_label, Node_id, Target_Node_label], which returns the detailed information of all Target_Node_label neighbours of the node(Node_label, Node_id) in the graph, including all attributes and field values.\n
        (4) EdgeCheck_LinkNode[Node_label, Node_id, Edge_label], which returns all edges with the Edge_label link to the given node.".\n
        (5) EdgeCheck_BetweenNodes[Start_Node_label, Start_Node_id, End_Node_label, End_Node_id], which finds the edge(s) between the given two nodes.\n
        Notes: When you need to query collaboration information between two authors (collaboration count or paper list), directly search in the Collab collaboration table for results(using EdgeCheck); for other relationships such as author-paper, paper-affiliation, author-affiliation dependencies, use NeighbourCheck to check neighboring nodes.\n
    Relation-function:\n
        (1) FilterByField[Table/result_i, field_name, field_value]：Filter the table or the previous function execution results based on field values and return a list of matching tuples.\n
        (2) FilterByRange[Table/result_i, field_name, min_value, max_value]：Filter the table or the previous function execution results based on a numerical range and return a list of matching tuples. If you do not set the maximum or minimum, set the parameter max_value or min_value to None.\n
        (3) GroupAggregate[Table/result_i, group_field, agg_method, agg_field]：Perform group and aggregation operations. agg_method can be 'count', 'sum', 'avg', 'min', 'max'. For 'count', agg_field is optional. For other methods, agg_field is required.\n
        (4) Join[source_tuples(result_i), target_table, target_field, source_field]：Join source_tuples with target_table based on matching field values, returning the combined results with all fields from both sources.\n
        (5) Sort[Table/result_i, sort_field, top_k]:Sort the table or the previous function execution results by the specified field. The top_k parameter is optional. If set, it will truncate the list to the top K documents\n
You must wait for the result of the action (Observation) before generating the next Thought or Action. Do NOT generate multiple steps together.\n
You may take as many steps as necessary.\n
Definition of the dataset: {dataset_definition}\n
Question: {question} Please answer by providing doc main feature (e.g., names) rather than doc_keys. For numerical questions, provide only the number in your final answer. For entity questions (names, titles), provide only the requested entities without additional explanation. {scratchpad}"""
