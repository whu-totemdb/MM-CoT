# MRBench files in this release

These QA records were supplied with the project and are derived from SciSciNet scholarly metadata. They preserve the original questions, answers, and per-domain IDs. The only per-record addition is `template_id`, matched against the original per-template question/answer pair. IDs are unique within a domain; use `(domain, id)` as a global identifier.

| Field | Meaning |
| --- | --- |
| `id` | Original per-domain QA ID |
| `question` | Original question text |
| `answer` | Original reference answer string |
| `template_id` | Original source-template number |

`manifest.json` records the byte-level SHA-256 of each original merged QA file and the corresponding reformatted release file. The release checksums include the added template field. No reference answers have been regenerated from a new database snapshot.

| Domain | Questions |
| --- | ---: |
| Biology | 150 |
| Chemistry | 150 |
| ComputerScience | 150 |
| MaterialsScience | 150 |
| Medicine | 146 |
| Total | 746 |

## Source templates

| ID | Question intent |
| --- | --- |
| 1 | Authors of a named paper |
| 2 | Affiliations of a named author |
| 3 | Retired publisher lookup; no records included |
| 4 | Citation count of a named paper |
| 5 | Highest-cited author among an institution's authors |
| 6 | Number of papers by an author |
| 7 | Most-cited paper by an author |
| 8 | Coauthors of an author on a specified paper |
| 9 | Closest collaborator by number of collaborations |
| 10 | Number of jointly authored papers for an author pair |
| 11 | Most-cited paper published in a specified year |
| 12 | Top three institutions by publication count in a year |
| 13 | Number of authors in an institution |
| 14 | Number of an institution's papers in a year |
| 15 | Highest total-citation author among authors publishing in a year |
| 16 | Highest total-citation institution among institutions publishing in a year |

Each active template has ten records per domain except Medicine templates 10 and 12, which each have eight. These are file counts rather than inferred historical scoring denominators. The data files do not include a verified graph/relation/combined label for every template, so no new task-category assignments are invented.

The original template generation scripts used an existing local database. They are not included as a data ingestion or benchmark regeneration pipeline. The large underlying database, its exact snapshot, sampling seeds, and the complete paraphrasing/validation process are unavailable in this directory. Consult the companion paper for the benchmark construction narrative. Upstream SciSciNet data terms continue to apply; no new license is assigned by this release.
