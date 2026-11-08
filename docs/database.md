# Database interface

Database methods use PostgreSQL with the pgvector extension. They query an existing scholarly dataset; the repository does not ship the full SciSciNet snapshot, an ingestion pipeline, precomputed vectors, or a database dump.

## Domain naming

Each domain has its own table suffix:

| CLI domain | Suffix |
| --- | --- |
| Biology | `biology` |
| Chemistry | `chemistry` |
| ComputerScience | `computerscience` |
| MaterialsScience | `materialsscience` |
| Medicine | `medicine` |

For example, `Paper` maps to `paper_computerscience` in Computer Science. Table access is restricted to the selected domain's eight scholarly tables. PostgreSQL identifiers use lowercase names. Models may supply the logical table or its full domain-specific name.

## Expected tables

The following describes the existing code's interface, not a verified reconstruction of the original database DDL. Expose tables or views with these names and adapt types to your source data. IDs must remain mutually compatible across edges and node tables; BIGINT is suitable for the supplied scholarly IDs.

| Table prefix | Required fields |
| --- | --- |
| `paper_` | `paperid`, `papertitle`, `year`, `referencecount`, `citationcount`, `publisher`, `date`, `doctype`, `originalvenue` |
| `author_` | `authorid`, `author_name`; optional metrics described in prompts |
| `affiliation_` | `affiliationid`, `affiliation_name`; optional location and productivity metadata |
| `paperauthor_` | `paperid`, `authorid` |
| `paperaffiliation_` | `paperid`, `affiliationid` |
| `authoraffiliation_` | `authorid`, `affiliationid` |
| `reference_` | `citing_paperid`, `cited_paperid` |
| `collab_` | `author1_id`, `author2_id`, `count`, `paperlist` |
| `vectors_` | `id`, `nodetype`, `embedding` |

`nodetype` is exactly `Paper`, `Author`, or `Affiliation`. The original schema descriptions also mention H-index, productivity, average_c10, and affiliation details such as gridid, latitude, longitude, official_page, and iso3166code. Node-detail queries return all actual columns; names in the prompt are descriptive. Fields used in filtering, grouping, and sorting must be ordinary SQL identifiers, such as `citationcount`, `year`, and `authorid`. Descriptive names containing a hyphen need a view alias such as `h_index` before use in relational actions.

Reference edges are directed from citing to cited paper. General Paper-to-Paper neighbor access considers both directions, and Graph RAG annotates each direction in its context. Collaboration edges are treated symmetrically when finding a pair of authors. Edge count refers to stored rows; `count` can represent the number of coauthored papers.

## Vector setup

Query embeddings use `sentence-transformers/all-mpnet-base-v2` by default. Stored vectors must use the identical encoder and preprocessing, with 768 dimensions for that model. To use local weights, set `EMBEDDING_MODEL` to a local directory. The implementation uses the pgvector L2 operator `<->`, matching the supplied retriever.

For example, an administrator can create the extension and a vector table in an already prepared database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE vectors_computerscience (
    id BIGINT NOT NULL,
    nodetype TEXT NOT NULL CHECK (nodetype IN ('Paper', 'Author', 'Affiliation')),
    embedding vector(768) NOT NULL,
    PRIMARY KEY (id, nodetype)
);
```

This creates an empty interface table, not the benchmark database. Insert vectors generated from the same scholarly entities as your node tables. Index choice and index-building are deployment-specific. The supplied retriever does not create or require a DiskANN index; the paper's deployment description cannot be reconstructed from these files alone.

## Execution and configuration

Set `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, and optionally `PGSSLMODE` in `.env` or the environment. Connections have a finite connect timeout, use autocommit, and default to read-only sessions. The application never creates or modifies permanent scholarly tables.

Filtering, grouping, and sorting accept a table name or a prior result list. Table input executes SQL; list input executes in Python. A Join sends source records as a JSON parameter to PostgreSQL, matches source and target keys there, and merges source/target records on return; target columns win when names overlap. ID joins use textual equality, so source keys must preserve the database's ID representation. No temporary-table creation is required.

Vector values and query values are bound parameters. Logical table names are allowlisted by domain, and relational field identifiers are validated before constructing SQL. Database errors are surfaced as tool observations instead of silently becoming empty successful results. The original graph neighbors and relational operators materialize their complete results in application memory; large intermediate sets still require sufficient memory.
