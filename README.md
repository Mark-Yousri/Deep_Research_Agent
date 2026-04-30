# Deep Research Agent

A multi-agent AI pipeline that takes a complex research question, runs parallel web searches, and synthesizes a comprehensive cited report — comparable to Perplexity or Gemini Deep Research, but fully open, auditable, and **100% free to run**.

## Architecture

```
User Question
     │
     ▼
┌─────────────┐
│  Guardrail  │  llama-3.1-8b-instant — blocks harmful/off-topic queries
└──────┬──────┘
       │ allowed
       ▼
┌─────────────┐
│   Planner   │  llama-3.3-70b-versatile — breaks question into 3–5 search queries
└──────┬──────┘
       │ queries[]
       ▼
┌──────────────────────────────┐
│  Searcher × N  (staggered)   │  Tavily Search API + llama-3.1-8b-instant extraction
└──────────────────────────────┘
       │ research_data[]
       ▼
┌─────────────┐
│   Writer    │  llama-3.3-70b-versatile — streaming cited report
└─────────────┘
       │ SSE stream
       ▼
  Web UI (FastAPI + vanilla JS)
```

## Features

- **Input guardrails** — fast classifier blocks harmful, nonsensical, and off-topic queries before any search or generation runs
- **Smart planning** — 70B model breaks your question into targeted, non-redundant search angles
- **Parallel search** — searches run concurrently with 2s stagger to respect free-tier rate limits; UI updates as each one completes
- **Rate-limit resilience** — automatic retry with exact backoff parsed from Groq error responses
- **Streaming UI** — report streams token-by-token with live Markdown rendering
- **Citations** — inline `[1]`, `[2]` references matched to source URLs

## Prerequisites

- Python 3.11+
- [Groq API key](https://console.groq.com/) — free, no credit card required
- [Tavily API key](https://app.tavily.com/) — free, 1,000 searches/month

## Setup

```bash
git clone https://github.com/yourusername/deep-research-agent
cd deep-research-agent

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — add GROQ_API_KEY and TAVILY_API_KEY
```

## Run

```bash
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq API — Llama 3.3 70B + Llama 3.1 8B (free tier) |
| Search | Tavily Search API (free tier) |
| Backend | FastAPI + uvicorn |
| Async | Python asyncio |
| Streaming | Server-Sent Events (SSE) |
| Frontend | Vanilla HTML/CSS/JS + marked.js |

## Project Structure

```
deep-research-agent/
├── agents/
│   ├── guardrail.py      # Safety classifier (Llama 3.1 8B)
│   ├── planner.py        # Query decomposition (Llama 3.3 70B)
│   ├── searcher.py       # Tavily search + extraction + rate-limit retry
│   ├── writer.py         # Streaming report synthesis (Llama 3.3 70B)
│   └── orchestrator.py   # Pipeline coordinator, SSE event emitter
├── tools/
│   └── tavily_search.py  # Tavily Search API wrapper
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── main.py               # FastAPI app
├── requirements.txt
├── .env.example
```
