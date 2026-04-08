# 🦊 KeenFox — AI-Powered Competitive Intelligence System

> **Enter any brand name → Get instant competitor analysis, strategic insights, and campaign recommendations**

KeenFox is an automated competitive intelligence platform that uses AI (Google Gemini) to discover competitors for any brand, scrape live market data, extract strategic signals, and generate actionable go-to-market recommendations.

---

## 🎯 What It Does

1. **AI-Powered Competitor Discovery** — Enter "Coca-Cola" and the system automatically identifies Pepsi, Red Bull, Dr Pepper, Starbucks, etc.
2. **Multi-Source Data Ingestion** — Scrapes competitor websites, G2/Capterra reviews, Reddit discussions, LinkedIn posts, changelogs, and news
3. **Deep Intelligence Extraction** — Uses LLM-powered reasoning to extract feature launches, customer sentiment, pricing signals, weaknesses, and market positioning
4. **Strategic Campaign Recommendations** — Generates specific GTM actions: headlines, ad copy, channel strategy, and prioritized recommendations grounded in competitive data
5. **Temporal Diff Analysis** — Tracks what changed between runs to alert you to new competitive moves

---

## 🏗️ Architecture & Algorithm

### Pipeline Architecture

```
User Input (Brand Name)
        │
        ▼
┌─────────────────────────┐
│  Phase 0: AI Discovery  │  ← Gemini identifies 4-6 competitors
│  competitor_finder.py   │    + generates brand strategic profile
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│ Phase 1: Data Ingestion │  ← ThreadPoolExecutor (parallel)
│ web_scraper.py          │    All competitors scraped simultaneously
│ review_fetcher.py       │    Sources: Website, G2, Reddit, LinkedIn, News
│ reddit_fetcher.py       │
│ search_fetcher.py       │
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│ Phase 2: Intel Engine   │  ← LLM signal extraction per competitor
│ intelligence_engine.py  │    Extracts: features, sentiment, pricing,
│                         │    weaknesses, positioning
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│ Phase 3: Campaign Loop  │  ← LLM strategic synthesis + recommendations
│ campaign_integrator.py  │    Outputs: market snapshot, vulnerabilities,
│                         │    messaging, channel strategy, GTM priorities
└────────┬────────────────┘
         ▼
┌─────────────────────────┐
│ Phase 4: Diff + Report  │  ← JSON diff vs previous run + Markdown report
│ diff_engine.py          │
│ report_generator.py     │
└─────────────────────────┘
```

### Core Algorithm: Multi-Stage LLM Reasoning

The system does **not** simply summarize data. It uses a **multi-stage reasoning pipeline**:

1. **Stage 1 — Signal Extraction (per competitor):** The LLM is given raw scraped data and asked to extract *strategically relevant signals* — not summaries. It classifies each signal by urgency, evidence, and strategic implication.

2. **Stage 2 — Cross-Competitor Synthesis:** All extracted signals are fed into a strategic synthesis prompt that asks the LLM to *reason across competitors*: "What is the biggest threat? Where is the whitespace? What are unmet needs across ALL competitors?"

3. **Stage 3 — Campaign Generation:** The synthesis + raw signals are combined with the brand's profile to generate *specific, data-backed* GTM recommendations — actual ad copy, actual email subject lines, actual channel priorities with rationale.

Each prompt is engineered to enforce **structured JSON output** with mandatory fields, preventing the LLM from giving vague advice.

### Parallelism

Data ingestion uses `concurrent.futures.ThreadPoolExecutor` to scrape all competitors simultaneously (one thread per competitor). This reduces ingestion time from ~6 minutes (sequential) to ~1.5 minutes (parallel).

---

## 📁 File Structure & Purpose

```
keenfox-intel/
├── main.py                          # Entry point — CLI argument parsing & pipeline orchestration
├── requirements.txt                 # Python dependencies
├── .env                             # API keys (GEMINI, TAVILY, REDDIT) — not committed
├── .env.example                     # Template for required environment variables
├── design_doc.md                    # Technical design document (assignment submission)
│
├── src/
│   ├── __init__.py
│   ├── config.py                    # Global settings: LLM model, max tokens, cache TTL
│   │
│   ├── discovery/                   # 🆕 Phase 0: AI-powered competitor discovery
│   │   ├── __init__.py
│   │   └── competitor_finder.py     # Uses Gemini to discover competitors + build brand profile
│   │
│   ├── ingestion/                   # Phase 1: Multi-source data collection
│   │   ├── web_scraper.py           # Scrapes competitor homepages & pricing pages (BeautifulSoup)
│   │   ├── review_fetcher.py        # Fetches G2/Capterra reviews via Tavily search or fallback
│   │   ├── reddit_fetcher.py        # Fetches Reddit discussions via PRAW or Tavily
│   │   └── search_fetcher.py        # Fetches LinkedIn, changelogs, news via Tavily/DuckDuckGo
│   │
│   ├── analysis/                    # Phase 2-3: LLM-powered analysis
│   │   ├── intelligence_engine.py   # Per-competitor signal extraction via Gemini
│   │   └── campaign_integrator.py   # Cross-competitor synthesis + campaign recommendations
│   │
│   ├── prompts/                     # All LLM prompts (centralized)
│   │   └── prompt_templates.py      # Signal extraction, synthesis, campaign, diff, NLQ prompts
│   │
│   └── utils/                       # Phase 4: Output generation
│       ├── diff_engine.py           # Compares current vs previous run, highlights changes
│       └── report_generator.py      # Converts JSON intelligence into formatted Markdown report
│
├── data/
│   ├── raw/                         # Scraped raw data (website, reviews, reddit, search JSONs)
│   └── reports/                     # Timestamped report snapshots for diff analysis
│
└── outputs/
    ├── competitive_intelligence_report.md   # Final human-readable report
    ├── combined_intelligence.json           # All extracted intelligence (for NLQ queries)
    ├── full_campaign_output.json            # Campaign synthesis + recommendations
    └── {competitor}_intelligence.json       # Per-competitor intelligence files
```

### File-by-File Purpose

| File | Purpose |
|------|---------|
| `main.py` | Entry point. Parses `--brand` CLI input, orchestrates the full pipeline, supports `--query` for natural language questions |
| `config.py` | Central configuration: LLM model (`gemini-2.5-flash`), token limits, cache TTL |
| `competitor_finder.py` | **AI Discovery Module.** Uses Gemini to identify 4-6 competitors for any brand + generates a strategic brand profile |
| `web_scraper.py` | Scrapes competitor homepages and pricing pages using `requests` + `BeautifulSoup`. Extracts clean text, removes noise (scripts, nav, footer) |
| `review_fetcher.py` | Fetches G2/Capterra review signals via Tavily web search. Falls back to DuckDuckGo scraping. Includes synthetic data for well-known brands |
| `reddit_fetcher.py` | Fetches Reddit discussions via PRAW (official Reddit API) or Tavily `site:reddit.com` search |
| `search_fetcher.py` | Fetches LinkedIn posts, product changelogs, and news via Tavily or DuckDuckGo HTML |
| `intelligence_engine.py` | Core analysis: sends compiled raw data to Gemini with structured extraction prompts. Includes retry logic for API rate limits |
| `campaign_integrator.py` | Two-stage LLM pipeline: (1) strategic synthesis across all competitors, (2) concrete campaign recommendations with specific copy and tactics |
| `prompt_templates.py` | All 5 LLM prompts centralized: signal extraction, strategic synthesis, campaign recommendations, diff analysis, natural language query |
| `diff_engine.py` | Compares current run's data against previous run. Uses Gemini to identify strategically meaningful changes over time |
| `report_generator.py` | Converts structured JSON output into a beautifully formatted Markdown report with emojis, urgency indicators, and section structure |

---

## 🛡️ Production Upgrades (V2)

The system is fortified with enterprise-grade reliability, strict guardrails, and rapid optimization:

*   **Optimization (Parallel Execution)**
    *   **Before:** Competitors analyzed sequentially using linear loops, leading to severe latency.
    *   **After:** Powered by `concurrent.futures.ThreadPoolExecutor`, executing massive LLM extraction payloads concurrently.
*   **Guardrails & Grounding (Chain-of-Thought)**
    *   **Before:** Loose prompt parsing subject to formatting hallucinations.
    *   **After:** Hardcoded backend `response_mime_type="application/json"` ensures pure type integrity. The engine mandates an internal `analysis_thought_process` where the LLM is forced to verify the data mathematically *before* creating the JSON payload.
*   **Error Detection & Schema Resilience**
    *   **Before:** Basic regex error fixing; failed abruptly with `KeyError`s if AI omitted keys.
    *   **After:** Captures HTTP 429 and 503 limits triggering an **Exponential Backoff** safety loop. Reconstructs missing JSON schema elements on the fly with safe fallback values, completely destroying runtime crash possibilities.

---

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and enter directory
cd keenfox-intel

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate    # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env` and add your keys:
```
GEMINI_API_KEY=your_google_ai_studio_key     # Required
TAVILY_API_KEY=your_tavily_key               # Optional — enriches reviews, Reddit, news
REDDIT_CLIENT_ID=your_reddit_id              # Optional — for Reddit API
REDDIT_CLIENT_SECRET=your_reddit_secret      # Optional
```

### 3. Run

```bash
# Analyze any brand
python main.py --brand "Coca-Cola"
python main.py --brand "Notion"
python main.py --brand "Nike"

# Re-use cached data (skip scraping)
python main.py --brand "Coca-Cola" --skip-scraping

# Ask questions about the competitive landscape
python main.py --brand "Coca-Cola" --query "What is Pepsi's biggest weakness?"
```

### 4. View Output

Open `outputs/competitive_intelligence_report.md` for the full formatted report.

---

## 🔑 API Keys

| Key | Required | Free Tier | Purpose |
|-----|----------|-----------|---------|
| `GEMINI_API_KEY` | ✅ Yes | ✅ Yes (Google AI Studio) | LLM reasoning — competitor discovery, signal extraction, synthesis |
| `TAVILY_API_KEY` | ❌ Optional | ✅ Yes (tavily.com) | Enriched web search for reviews, Reddit, news |
| `REDDIT_CLIENT_ID` | ❌ Optional | ✅ Yes (reddit.com/prefs/apps) | Direct Reddit API access |

---

## 🛠️ Tech Stack

- **LLM**: Google Gemini 2.5 Flash via `google-genai` SDK
- **Web Scraping**: `requests` + `BeautifulSoup4` + `lxml`
- **Search API**: Tavily (optional) with DuckDuckGo fallback
- **Reddit API**: PRAW (optional)
- **Concurrency**: `concurrent.futures.ThreadPoolExecutor`
- **Config**: `python-dotenv` for environment management
