# InternMatch eval results

Run: 2026-11-18 08:08 UTC

Index: 2411 active jobs. Relevant = title matches the persona's role AND the job is an internship (gain 2) or entry-level (gain 1).

- Skipped persona 'DevOps / Cloud': no relevant jobs in the index today.

Personas evaluated: 7

| Method | P@5 | P@10 | nDCG@10 | MRR |
|---|---|---|---|---|
| Keyword (Postgres full-text) | 0.000 | 0.000 | 0.000 | 0.000 |
| Semantic (pgvector) | 0.114 | 0.143 | 0.247 | 0.243 |
| Hybrid (RRF) | 0.057 | 0.043 | 0.099 | 0.092 |
| InternMatch ranker | 0.314 | 0.257 | 0.604 | 0.663 |
