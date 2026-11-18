# InternMatch eval results

Run: 2026-11-18 06:28 UTC

Index: 1010 active jobs. Relevant = title matches the persona's role AND the job is an internship (gain 2) or entry-level (gain 1).

- Skipped persona 'Data analyst': no relevant jobs in the index today.
- Skipped persona 'DevOps / Cloud': no relevant jobs in the index today.

Personas evaluated: 6

| Method | P@5 | P@10 | nDCG@10 | MRR |
|---|---|---|---|---|
| Keyword (Postgres full-text) | 0.000 | 0.000 | 0.000 | 0.000 |
| Semantic (pgvector) | 0.267 | 0.150 | 0.505 | 0.531 |
| Hybrid (RRF) | 0.067 | 0.067 | 0.226 | 0.188 |
| InternMatch ranker | 0.300 | 0.200 | 0.745 | 0.806 |
