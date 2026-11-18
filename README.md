<div align="center">

# InternMatch

**AI-powered internship matching for students.**
Upload a resume, get live internships ranked by fit, see the skills you're missing, and ask an AI agent what to do next.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-agent-1C3C3C)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Evaluation](#evaluation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Overview

### The problem

Students outside top colleges rarely hear about off-campus internships in time. Openings are spread across
hundreds of company career pages, most listings on job portals need years of experience, and a student has no
easy way to tell which roles actually fit their skills.

### The solution

InternMatch collects live postings every day from official company job-board APIs, keeps only roles that are
open to students in India or remote, and ranks them against each student's profile. For every role it shows
the skills the student already has, the skills they are missing, and how to prepare.

After applying, it keeps helping: an application tracker with follow-up reminders, a study plan for each job built
from its description, a daily quiz on the topics those jobs test, and a mock interview for the exact role. Everything
runs on free tiers, and nothing asks the student to pay to apply.

---

## Key Features

| Feature | Description |
|---|---|
| **Live job index** | Daily ingestion from the public Greenhouse, Lever, Ashby, SmartRecruiters and Workday careers APIs: 116 companies such as NVIDIA, Cisco, Intel, Salesforce, Deutsche Bank, Swiggy, Razorpay, Paytm, Meesho, Sarvam AI and Bosch. Only India and open-remote roles are kept. No API keys needed. Edited postings are re-embedded and closed postings are deactivated. |
| **Student filters** | Tech roles only by default (Software, AI/ML, Data, DevOps/Cloud, Security, QA), so marketing or finance internships don't crowd out the matches. Filters for 6+ month internships and posting date, badges for internship length, start month (e.g. *Starts Jan 2027*) and new postings, and a warning on listings older than three months. |
| **Resume parsing** | PDF → text → contact details redacted → LLM returns a schema-validated profile (skills, target roles, education, experience). Resumes are never stored. |
| **Personalised ranking** | Vector retrieval on pgvector, then re-ranking on semantic fit, skill coverage, experience level and recency. *Save* and *Not for me* adapt the ranking to each student (Rocchio feedback). |
| **Skill-gap analysis** | Every match shows matched and missing skills from a curated vocabulary of ~90 technical skills. |
| **Explain my fit** | One structured LLM call returns a fit score, matched and missing skills, and up to three preparation steps, grounded in the posting. |
| **AI career agent** | A LangGraph tool-calling agent that searches jobs, recommends roles, reads postings and checks skill gaps, with per-session memory. |
| **Hybrid search** | Free-text search that fuses vector and full-text results with reciprocal rank fusion. |
| **Application tracker** | Saved → Applied → Online test → Interview → Offer / Rejected, with dates, notes, weekly counts and reminders (apply to saved roles, follow up after 10 days, prepare for tests). Stored in the browser; no account needed. |
| **Prep plan per job** | From the job description and the student's profile: topics to study by priority, free resources for each (from a hand-checked list, never AI-invented links), likely interview questions with answer hints, and a 7-day plan. |
| **Daily practice quiz** | 10 multiple-choice questions a day on the topics of the jobs being tracked, with explanations, a streak, per-topic accuracy and spaced repetition (topics answered wrong come back sooner). |
| **Mock interview** | A 6-question practice interview for a specific job, with feedback and a score after every answer and a summary at the end. |
| **Offline evaluation** | Ranking metrics (P@k, nDCG, MRR) against student personas and an LLM grounding check. |

---

## How It Works

```mermaid
flowchart TD
    A[Greenhouse / Lever / Ashby / SmartRecruiters / Workday APIs] -->|daily GitHub Actions job| B[Ingestion pipeline]
    B --> B1[Filter: India or remote]
    B1 --> B2[Tag level, years, role family,<br/>internship length and start month]
    B2 --> B3[Upsert + content hash]
    B3 --> B4[Embed with bge-small-en-v1.5]
    B4 --> C[(PostgreSQL + pgvector<br/>HNSW index)]

    C --> D[FastAPI backend]
    D --> D1["/match: retrieve → re-rank → personalise"]
    D --> D2["/search: vector + full-text, RRF"]
    D --> D3["/resume/parse: PDF → redact → LLM structured output"]
    D --> D4["/jobs/{id}/explain: grounded fit explanation"]
    D --> D5["/agent/chat: LangGraph agent with memory"]
    D --> D6["/jobs/{id}/prep, /quiz, /jobs/{id}/interview: interview coaching"]

    D1 & D2 & D3 & D4 & D5 & D6 --> E[Next.js web app<br/>tracker, quiz stats in localStorage]
```

### Ranking pipeline

1. **Retrieve** – 150 nearest postings by cosine similarity (HNSW) plus 50 full-text matches.
2. **Filter** – experience level (internship / entry level), role family (tech roles by default), remote only, city,
   maximum years of experience, minimum internship length, posting date.
3. **Re-rank** – weighted score:

   | Signal | Weight | Source |
   |---|---|---|
   | Semantic similarity | 0.60 | profile embedding vs posting embedding |
   | Experience level | 0.25 | internship > entry level > other |
   | Skill coverage | 0.10 | profile skills found in the posting |
   | Recency | 0.05 | exponential decay, 30-day scale |

4. **Personalise** – the query vector moves toward tracked roles (+0.35) and away from hidden roles (−0.20).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic |
| AI / LLM | Groq (`openai/gpt-oss-120b`), LangChain, LangGraph |
| Embeddings | fastembed `BAAI/bge-small-en-v1.5` (384-dim, runs locally) |
| Database | PostgreSQL + pgvector (HNSW), full-text search |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 |
| Tooling | uv, pytest, ESLint, Docker |
| CI/CD | GitHub Actions (tests, build, daily job refresh) |
| Hosting | Render (API), Vercel (web), Neon (database) – all free tiers |

---

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.12 automatically)
- Node.js 20+
- A free [Groq API key](https://console.groq.com/keys)

No Docker or database installation is needed for local development: `DATABASE_URL=local` starts an embedded
PostgreSQL with pgvector, stored in `%LOCALAPPDATA%\InternMatch` on Windows (`~/.local/share/InternMatch` elsewhere),
outside the project so sync tools such as OneDrive never touch database files.

### 1. Clone

```bash
git clone https://github.com/bhargavi-46/InternMatch.git
cd InternMatch
```

### 2. Backend

```bash
cd backend
uv sync
cp .env.example .env              # add your GROQ_API_KEY
uv run python -m app.ingest.run   # fetch and embed jobs (first run ~20 min)
uv run uvicorn app.main:app --port 8000
```

API docs are available at http://localhost:8000/docs.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

> **Tip:** Without a Groq key, matching and search still work. Type your skills in instead of uploading a resume.

---

## Configuration

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `local` | `local` for embedded Postgres, or a PostgreSQL connection string (e.g. Neon) |
| `GROQ_API_KEY` | For AI features | – | Resume parsing, fit explanations, chat |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Any Groq chat model with structured output |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated frontend URLs |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend base URL |

All external services used have a free tier: [Groq](https://console.groq.com),
[Neon](https://neon.tech), [Render](https://render.com),
[Vercel](https://vercel.com).

---

## API Reference

| Method | Endpoint | Description | Rate limited |
|---|---|---|---|
| `GET` | `/health` | Health check | |
| `GET` | `/stats` | Index size, student roles, companies, last refresh | |
| `GET` | `/jobs` | List active jobs with filters | |
| `GET` | `/jobs/{id}` | Job details | |
| `POST` | `/search` | Hybrid free-text search | |
| `POST` | `/match` | Ranked matches for a profile, with saved / hidden feedback | |
| `POST` | `/resume/parse` | PDF resume (≤ 5 MB) → structured profile | ✔ |
| `POST` | `/jobs/{id}/explain` | LLM fit explanation for one job | ✔ |
| `POST` | `/agent/chat` | Conversational agent, memory per `thread_id` | ✔ |
| `POST` | `/jobs/{id}/prep` | Prep plan: topics with free resources, likely questions, 7-day plan | ✔ |
| `POST` | `/quiz` | Multiple-choice practice questions for given topics and weak topics | ✔ |
| `POST` | `/jobs/{id}/interview` | Next mock-interview message (stateless; the client sends the transcript) | ✔ |

LLM endpoints are limited to 30 calls per 10 minutes per IP to stay within the Groq free quota.
Full request and response schemas are in the interactive docs at `/docs`.

---

## Evaluation

Ranking quality is measured on the live index against student personas (ML/AI, backend, frontend, data analyst,
security, product, support engineering). A posting is relevant when its title matches the persona's role and it is an
internship (gain 2) or entry-level role (gain 1).

| Method | P@5 | P@10 | nDCG@10 | MRR |
|---|---|---|---|---|
| Keyword (Postgres full-text) | 0.000 | 0.000 | 0.000 | 0.000 |
| Semantic (pgvector) | 0.114 | 0.143 | 0.247 | 0.243 |
| Hybrid (RRF) | 0.057 | 0.043 | 0.099 | 0.092 |
| **InternMatch ranker** | **0.314** | **0.257** | **0.604** | **0.663** |

*Measured on an earlier index of 2,411 active jobs, 7 personas, top-10 results.* Ranker weights were chosen with a small sweep on an earlier,
smaller index, so treat the gap as indicative rather than proof. Absolute precision is limited by supply: about
110 postings in the index are student roles on a given day.

```bash
cd backend
uv run python -m app.evals.run          # ranking metrics → eval_results.md
uv run python -m app.evals.run --llm    # adds the LLM grounding check
```

---

## Testing

```bash
# Backend: unit and API tests
cd backend && uv run pytest

# Frontend: lint and production build
cd frontend && npm run lint && npm run build
```

Both run on every push and pull request through GitHub Actions (`.github/workflows/ci.yml`).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `GROQ_API_KEY is not set` in the app | Add the key to `backend/.env` and restart the API. |
| `Local database did not become ready` | Read `postgres.log` in the folder named in the error. Stop the API with `Ctrl+C`; the database shuts down with it. |
| `429 Too Many Requests` | The AI endpoints allow 30 calls per 10 minutes per IP. Wait and retry. |

---

## Deployment

| Step | Service | Action |
|---|---|---|
| 1 | **Neon** | Create a project and copy the connection string. |
| 2 | **GitHub Actions** | Add the repository secret `DATABASE_URL`. Run the *Refresh jobs* workflow once; it then runs daily at 08:00 IST. |
| 3 | **Render** | *New → Blueprint* → select this repo (`render.yaml`). Set `DATABASE_URL`, `GROQ_API_KEY`, `CORS_ORIGINS`. |
| 4 | **Vercel** | Import the repo with root directory `frontend` and set `NEXT_PUBLIC_API_URL` to the Render URL. |

To run the full stack in containers instead: `docker compose up`.

> Render's free plan sleeps after 15 minutes of inactivity; the first request afterwards takes about a minute.

---

## Project Structure

```
InternMatch/
├── backend/
│   ├── app/
│   │   ├── ingest/          # job-board fetchers, filters, tags, upsert, embedding
│   │   ├── evals/           # personas, metrics, evaluation runner
│   │   ├── main.py          # FastAPI app and routes
│   │   ├── ranking.py       # retrieval, rank fusion, re-ranking, personalisation
│   │   ├── agent.py         # fit explanations + LangGraph agent
│   │   ├── coach.py         # prep plans, daily quiz, mock interview
│   │   ├── resume.py        # PDF parsing + LLM profile extraction
│   │   ├── skills.py        # skills vocabulary and extraction
│   │   ├── embeddings.py    # local embedding model
│   │   ├── db.py, models.py # database engine and schema
│   │   └── ratelimit.py     # per-IP rate limiting
│   ├── tests/               # pytest suite
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages and layout
│       ├── components/      # profile, filters, match cards, search, chat, tracker, quiz, interview
│       └── lib/             # API client, types, storage, tracker and quiz logic
├── .github/workflows/       # CI and daily job refresh
├── docker-compose.yml
└── render.yaml
```

---

## Design Decisions

- **Official APIs only.** Jobs come from public job-board APIs that companies publish; no scraping of sites whose terms forbid it.
- **Local embeddings.** `bge-small-en-v1.5` runs on CPU, so embedding costs nothing and needs no API key.
- **One database for everything.** pgvector keeps vectors, full-text search and relational filters in a single PostgreSQL query.
- **Structured LLM outputs.** Resume parsing and fit explanations use JSON-schema structured output, validated with Pydantic.
- **Privacy by default.** Emails and phone numbers are removed before a resume reaches the LLM, and resumes are never saved. Tracked applications, notes, prep plans and quiz progress live in the browser.
- **No invented links.** The LLM only classifies each study topic; links come from a short, hand-checked list of free resources.

---

## Known Limitations

- Coverage is limited to companies whose job boards are public; many Indian internships are posted only on portals without an API.
- Experience level is inferred from titles and "N years of experience" phrases and can be wrong for unusual wording.
- Internship length and start month are read from the posting text, so they are missing when a posting doesn't state them.
- Quiz questions are AI-generated and checked for format, not reviewed by a person; an answer can occasionally be wrong.
- Tracker and quiz progress are stored per browser, so they don't sync between devices.
- Agent memory is held in the API process and resets when the server restarts.

---

## Roadmap

- [ ] Email alerts for new high-fit internships
- [ ] More Indian company job boards (many use ATSs without a public API)
- [ ] Optional sign-in to sync the tracker and quiz progress across devices
- [ ] Persistent agent memory in PostgreSQL
- [ ] Larger, hand-labelled evaluation set
