# **Greyamp AI Sales Agent**

**Agentic AI pipeline to automate B2B lead discovery, enrichment, qualification and outreach for Greyamp Consulting.**

> This repository contains a modular, multi-agent system implemented in Python and ported conceptually to LangFlow. The pipeline generates Ideal Customer Profiles (ICPs), scouts news sources for AI-related buying signals, enriches and qualifies leads using LLMs and the Tavily API, and prepares outreach-ready prospects.

---

## **Table of contents**

- [Project Overview](#project-overview)
- [Architecture & Agents](#architecture--agents)
- [Repository structure](#repository-structure)
- [Requirements & Environment](#requirements--environment)
- [Quickstart — run the pipeline locally](#quickstart--run-the-pipeline-locally)
- [Data files & outputs](#data-files--outputs)
- [LangFlow migration notes](#langflow-migration-notes)
- [Design decisions & best practices](#design-decisions--best-practices)
- [How to extend](#how-to-extend)
- [Known limitations & future work](#known-limitations--future-work)
- [Credits](#credits)

---

## **Project Overview**

The **Greyamp AI Sales Agent** is designed to automate discovery of high-quality B2B prospects aligned with Greyamp Consulting's AI-first services. The system focuses on:

- generating targeted ICPs for the sales search space,
- continuously scouting multiple news sources for AI-related signals,
- extracting company entities from articles and enriching them with authoritative metadata (CEO, HQ, website), and
- filtering & saving outreach-ready leads.

This README is based on the Python implementation of the four pipeline phases. See the internship report for the full background, metrics and validation results.

---

## **Architecture & Agents**

The pipeline is implemented as a set of independent agents (scripts). Each agent consumes JSON and writes a structured JSON output for the next stage:

1. **Strategist (phase1\_strategist.py)** — analyses `greyamp_context.txt` and produces a structured company summary that seeds ICP generation.
2. **ICP Generator (phase2\_icp\_generator.py)** — creates `icp_profiles.json` containing 5 validated ICPs (industry, cities, buying signals).
3. **Scout (phase3\_scout.py)** — queries multi-source news APIs (GNews + NewsAPI), constructs broad AI-focused queries per ICP, deduplicates results and writes `raw_leads.json`.
4. **Analyst (phase4\_analyst.py)** — extracts candidate company names from articles using an LLM, enriches them via the Tavily API, applies quality filters and writes `qualified_leads.json`.

Each phase is intentionally modular to allow re-running a single stage without rerunning the whole system.

---

## **Repository structure**

```text
├── phase1_strategist.py       # creates company summary
├── phase2_icp_generator.py    # builds icp_profiles.json
├── phase3_scout.py            # harvests news articles -> raw_leads.json
├── phase4_analyst.py          # enriches & qualifies -> qualified_leads.json
├── icp_profiles.json          # ICP output (generated)
├── raw_leads.json             # Scout output (sample articles)
├── qualified_leads.json       # Analyst output (Final qualified leads) 
├── greyamp_context.txt        # Company context used by Strategist
├── Greyamp Final Internship Report.pdf  # Full report with design, results
├── .env                       # Environment variable
└── README.md                  # About the project
```

---

## **Requirements & Environment**

Recommended Python version: **3.10+**.

Suggested dependencies (put into `requirements.txt`):

- openai-compatible SDK used in your environment (the repo uses `openai` / OpenAI client)
- requests
- python-dotenv
- tavily (the Tavily client wrapper used in analysis phase)

Environment variables:

```
OPENAI_API_KEY=sk-...
GNEWS_API_KEY=...
NEWSAPI_KEY=...
TAVILY_API_KEY=...
```

Notes:

- The pipeline uses OpenAI LLMs (gpt-4o-mini, gpt-4o) for structured outputs and entity extraction — keep your keys secure.
- Tavily is used for company enrichment in Phase 4; ensure `TAVILY_API_KEY` is available.

---

## **Quickstart — run the pipeline locally**

1. Clone the repo and create a virtual environment

```bash
git clone <repo-url>
cd Greyamp-AI-Sales-Agent
python -m venv venv
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. Create a `.env` and set the API keys.

3. Run the phases in order (you can re-run any phase independently):

```bash
python phase1_strategist.py      # produces the initial summary (used by Phase 2)
python phase2_icp_generator.py   # generates icp_profiles.json
python phase3_scout.py           # builds raw_leads.json from multi-source news
python phase4_analyst.py         # enriches & filters -> qualified_leads.json
```

**Notes and tips:**

- Phase 2 expects the Phase 1 summary inserted into the `phase2_icp_generator.py` or available as a saved JSON file. See the scripts' top comments for where to paste the Phase 1 output or how to persist it.
- Phase 3 calls GNews and NewsAPI; missing keys will skip the corresponding source but the script is defensive and will continue.
- Phase 4 requires a valid `TAVILY_API_KEY` and will exit if absent — it performs Tavily searches to enrich leads.

---

## **Data files & outputs**

- `icp_profiles.json` — canonical list of generated ICPs (sample contents provided in repo).
- `raw_leads.json` — de-duplicated articles discovered by the Scout. Each entry contains title, description, content snippet, url, publishedAt, source and matched icp.
- `qualified_leads.json` — final enriched leads produced by Analyst. Each entry follows the schema used in the Analyst prompt (company\_name, location\_city, key\_person\_name, key\_person\_role, qualifying\_event\_signal, summary).
- `Greyamp Final Internship Report.pdf` — full project documentation, architecture, validations and learnings.

---

## **Langflow migration notes**

The project includes a migration of logical steps into LangFlow visual flows. Key points:

- LangFlow flows mirror the Python phases using `File`, `Prompt Template`, `Language Model`, `API Request` and `Save File` nodes.
- Extra care was required to handle type conversion (Message vs Data) using `Type Convert` nodes and small Python Interpreter nodes where complex logic (de-duplication, retries) was necessary.
- The LangFlow migration improves maintainability and enables non‑developers to run and tweak prompts, but pay attention to node I/O types when modifying flows.

---

## **Design decisions & best practices**

- **Multi-agent architecture**: Separating responsibilities (Strategist → ICP → Scout → Analyst → Outreach) reduces coupling and makes tuning easy.
- **Structured outputs**: Prompts instruct LLMs to return JSON objects and the code uses `response_format` or parsing + `json.loads` for deterministic downstream consumption.
- **Tiered LLM usage**: Use cheaper / smaller models (gpt-4o-mini) for extraction & quick passes, and larger models (gpt-4o) for final validation and enrichment to balance cost and quality.
- **Defensive API handling**: Scripts include retries/backoff, rate-limit awareness, and deduplication (URL set) to keep data quality high.

---

## **How to extend**

Suggested next steps and extension points:

- **Outreach flow**: implement the Outreach agent that uses RAG (embed Greyamp marketing assets) to produce personalized emails and deliver them to a CRM.
- **Persistence**: add a small SQLite DB or vector DB to store leads, embeddings and outreach history for analytics and A/B testing.
- **Scheduler**: run the Scout on a cron / Cloud Function to keep leads fresh.
- **UI / Dashboard**: add a Streamlit/FastAPI UI to preview and approve outreach drafts.
- **Testing**: add unit tests and integration tests for prompt stability and API wrappers.

---

## **Known limitations & future work**

- Some LLM outputs may still require manual validation — continue to log and sample-check generated JSON.
- LangFlow node types and conversions add complexity; document node I/O when sharing flows with others.
- Expand news sources or add social signals (LinkedIn, Crunchbase) to increase discovery coverage.

---

## **Credits**

Prepared by: **Saksham Agrawal** for Greyamp Consulting (Internship project)

For full project writeup, architecture and experimental results, read `Greyamp Final Internship Report.pdf` included in repository.