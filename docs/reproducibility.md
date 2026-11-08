# Reproducibility and implementation behavior

This release is a refactored research companion. It retains the supplied research instruction strings, few-shot examples, answer-comparison rules, and baseline prompt text, while replacing duplicated client and experiment plumbing. It is not a bit-for-bit archive of historical runs.

## What is present

- All five available merged QA files, with original question/answer/ID values and added template provenance.
- MM-CoT and a graph-only controller sharing the same lifecycle and parser.
- Base LLM, node-metadata Text RAG, and one-hop Graph RAG configurations.
- Explicit model IDs, temperature, step/token budgets, dataset hashes, timing, statuses, and operation traces in experiment outputs.
- Offline regression checks and CI configuration.

## What is not recoverable here

The full original scholarly database snapshot, ingestion and embedding scripts, vector files, exact dependency versions, historical model endpoint versions, and a reconciled set of scored question IDs are absent. Original result folders are excluded from this release. No scores are presented as newly reproduced paper results.

The actual dataset has 746 records; Medicine has 146. Template 3 was retired. The paper reports dataset and accuracy tables, but those tables do not determine which available records were scored. In particular, neither a reported domain mean nor the available QA counts establishes a pooled, sample-level accuracy. Keep per-domain denominators explicit when comparing new experiments.

## Controller behavior

Each round generates one Thought and then one Action. Actions use `FunctionName[arguments]`; one action per round is enforced so `result_N` remains unambiguous. The original research examples already use this form. `Finish[answer]` is the only successful controller termination. The model receives execution observations between rounds.

| Setting | MM-CoT | Graph-CoT |
| --- | ---: | ---: |
| Default maximum rounds | 10 | 15 |
| Default prompt-token budget | 10,000 | 3,896 |
| Default retrieval result count | 1 | 1 |
| Default temperature | 0 | 0 |

Round defaults match the supplied batch scripts. Token counting in this release uses `cl100k_base` over the full formatted prompt before both model calls. The source used its legacy tokenizer and checked the full prompt for MM-CoT but only the scratchpad for Graph-CoT. These are approximate controller safeguards, not model-specific context-window guarantees. A run that exceeds a budget returns `step_limit` or `token_limit` with no fabricated final answer.

The original zero-shot template selection did not reliably reach the actual model call. This release selects the proper zero-shot instruction and omits examples. Provider-specific aliases and third-party gateway URLs were removed. Model IDs are sent exactly as configured, with no hidden conversion from a requested model family to a different endpoint model. API errors have finite SDK retries and are recorded as errors. One shared configured temperature replaces inconsistent per-provider defaults, including the original MM-CoT Qwen setting of 0.01.

## Action implementation

| Category | Supported actions |
| --- | --- |
| Vector | `RetrieveNode[keyword]` |
| Graph | `NodeDetail[label, id]`, `NeighbourCheck[label, id, target_label]`, `EdgeCheck_LinkNode[label, id, edge_label]`, `EdgeCheck_BetweenNodes[label, id, label, id]` |
| Relational | `FilterByField[source, field, value]`, `FilterByRange[source, field, min, max]`, `GroupAggregate[source, group_field, method, agg_field]`, `Join[result_N, target_table, target_field, source_field]`, `Sort[source, field, top_k, ascending]` |
| Control | `ShowDetail[result_N, optional_fields...]`, `Finish[answer]` |

`NeighborCheck` is accepted as an alias. Quotes protect commas in field values; whitespace after commas is optional. `None` denotes an open range bound or an omitted sort limit. `GroupAggregate` supports `count`, `sum`, `avg`, `min`, and `max`; the aggregation field is optional for count. Sort defaults to descending and accepts an optional final `true` or `false` flag. Unknown actions and missing result references become error observations. Graph-CoT rejects relational actions.

Complete intermediate results live in a Python dictionary. Routine collection observations expose counts and samples: generally one row, up to three for Sort and small neighbor sets, all pair-edge results, and counts only for linked-edge collections. NodeDetail exposes the node. ShowDetail expands the retained value and optionally selects fields; it can return a long observation. Feedback is deterministic formatting, with no learned summarizer. It does not guarantee constant context size.

Table-based relational actions execute in PostgreSQL; actions on intermediate lists can execute in Python. Join delegates key matching to PostgreSQL. This distinction matters when interpreting the paper's description of backend computation. The release does not claim that every intermediate stays in the database or that context growth, runtime efficiency, or memory savings have been experimentally established.

## Baselines

Text RAG retains the supplied LLM keyword-extraction prompt and concise-answer prompt, retrieves one node by default, and formats its stored metadata. It does not rebuild a paper-chunk text index.

Graph RAG adds one-hop neighbors through all five scholarly edge types. Its retained formatting displays at most five nodes per neighbor group, truncates long neighbor field values to 100 characters, and includes edge summaries. Queries still materialize the underlying ego-graph in memory. Zero-valued attributes are now retained. Base LLM retains the supplied concise Chinese question prompt and receives no retrieved context.

## Evaluation

The semantic evaluator retains the supplied comparison rules, including exact numerical agreement and equivalence of author lists despite ordering/formatting. It accepts only an unambiguous `Correct` or `Incorrect` judgment. The source's substring-based judgment parsing is replaced by exact label parsing. Exact mode normalizes case and whitespace only and is not the paper's semantic accuracy.

All processed QA records count toward the domain denominator, including failed queries and budget exhaustion. Judge API failures remain unresolved: `accuracy` is null until all judgments succeed, while explicit lower/upper bounds are reported. Incomplete interrupted runs cannot be scored through the CLI. The runner currently supports checkpoint inspection rather than automatic resume. Record provider model versions, database snapshot, encoder, dependency environment, and any separate selection rules with every reported result.
