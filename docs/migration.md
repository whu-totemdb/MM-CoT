# Migration from the working directory

| Original files | Release location / disposition |
| --- | --- |
| `MultiModAgent.py`, `GraphAgent.py` | `src/mmcot/agent.py`, `actions.py`; shared controller and action dispatch |
| `multimod_prompts.py`, `graph_prompts.py` | `src/mmcot/prompts/`; research instruction strings retained, service-specific templates and LangChain objects removed |
| `multimod_fewshots.py`, `graph_fewshots.py` | `src/mmcot/prompts/*_examples.py`; the research `SubSet` examples retained |
| `tools/graph_function.py` | `src/mmcot/backends/graph.py`; typed edges, directed citations, symmetric author collaboration |
| `tools/relation_function.py` | `src/mmcot/backends/relational.py`; table/list operations and parameterized database join |
| `tools/Retriever.py` | `src/mmcot/backends/vector.py`; same MPNet/L2 retrieval interface, configurable weights |
| `Text_RAG.py`, `Graph_RAG.py` | `src/mmcot/baselines.py`; keyword/answer prompts and context formatting retained with shared services |
| `llm_direct_query.py` | `BaseLLM` in `baselines.py`; original concise question prompt |
| `*_batch_query.py` | `mmcot run`; shared runner, result format, and CLI |
| `Graph_RAG_batch_query.py` | Discarded placeholder; replaced by the functioning shared runner |
| `accuracy_checker.py`, `batch_accuracy_checker.py` | `mmcot evaluate`; retained comparison rules, strict judgment parsing, explicit failure counts |
| Five merged `QA/*/*_QA.json` files | Excluded from the repository; local `data/` is ignored by Git |
| Per-template QA JSON and `QA/模板.md` | Excluded dataset artifacts; supply QA files separately for experiments |
| `QA/QA-Generate/`, `QA/Merge.py` | Excluded one-off database sampling and merge workflows; no unsupported data-regeneration claim |
| `tools/PaperRetriver.py` | Excluded unused alternative retriever |
| `MCPO-Server.py`, `MCPO-Server.md`, service-specific prompts/tests, `FRP/` | Excluded service and tunneling components |
| Original manual/smoke tests, model connectivity checks | Excluded; focused offline regression checks added for the refactor |
| `Results/`, `server.log`, `__pycache__/` | Excluded generated/local artifacts |

The original working files were not overwritten. Hardcoded API keys, gateways, database credentials, private hosts, and local absolute paths are not copied into the release. Configuration comes from `.env` or environment variables. Do not publish the parent working directory or its original files as part of this repository.

Implementation changes address malformed source initialization, duplicate graph connection cleanup, brittle comma parsing, invalid result references, inconsistent provider routing, ignored zero-shot templates, ascending sort parsing, undirected collaboration lookup, and errors previously converted into empty apparent successes. These changes are intentional; they can change experiment outcomes. See the reproducibility notes before comparing to historical scores.
