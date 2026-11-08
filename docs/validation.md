# Validation performed

Validation date: 2026-11-08.

The release was checked on Windows with Python 3.12.14. All checks below completed successfully:

- Compiled all release source files.
- Ran 39 offline regression tests with Python's standard-library unittest runner.
- Validated external QA loading, duplicate-ID rejection, and per-domain CLI inspection using temporary synthetic records. Tests do not require a bundled dataset.
- Compared the retained research dataset descriptions, few-shot/zero-shot instructions, and both few-shot example collections against their original Python constants; all retained values matched exactly.
- Loaded baseline modules without connecting to a database or API, including mocked Text RAG and one-hop Graph RAG queries.
- Exercised multi-round relational operation chaining and final-answer detection with a scripted model and controlled execution results.
- Checked CLI help, offline dataset inspection, experiment defaults, and rejection of options that do not apply to a selected method.
- Built a wheel with `pip wheel --no-deps --no-build-isolation`, installed it into a separate temporary directory without dependencies, and checked its offline CLI.
- Scanned release files for the original API-key literals; scanned Python files for the original private database host, local Linux paths, third-party gateway references, and service-specific code. No matches were found.

The focused tests cover parser handling of commas, quotes, and nested final answers; graph edge direction; numeric filtering; inclusive ranges; grouping; ascending/descending sorting; ID joins; parameter binding; controller budget exhaustion; missing result references; API failures; zero-shot prompts; baseline context formatting; atomic checkpoint writes; and evaluation denominator/judge-error handling.

## Checks not performed

No populated scholarly PostgreSQL instance, original vector collection, or configured model service was used. Live PostgreSQL/pgvector queries, model downloads, model-provider compatibility, full dependency installation, and end-to-end answer accuracy therefore remain unverified. The SQL join's execution against a live PostgreSQL server is also unverified. Mocked execution checks do not establish paper-score reproduction or large-data performance.

Dependency bounds are declared in `pyproject.toml`; this is not a validated exact-version lockfile. The GitHub Actions workflow is prepared for Python 3.10, 3.11, and 3.12, but was not run on GitHub during this task.
