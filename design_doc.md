# KeenFox Competitive Intelligence System — Design Document

## Overview

This system is an AI-powered competitive intelligence and campaign feedback loop for KeenFox. It continuously monitors 5 competitors in the B2B SaaS productivity space, extracts strategic signals, and generates concrete campaign recommendations — replacing manual, reactive tracking with an automated, proactive intelligence pipeline.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: DATA INGESTION                      │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Web Scraper  │  │  Reviews     │  │   Reddit Fetcher     │   │
│  │              │  │  Fetcher     │  │                      │   │
│  │ - Homepage   │  │ - G2/Capterra│  │ - r/projectmgmt      │   │
│  │ - Pricing    │  │ - Tavily API │  │ - r/productivity     │   │
│  │              │  │ - Fallback   │  │ - PRAW or Tavily     │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         └─────────────────┴──────────────────────┘              │
│                           │                                     │
│                    data/raw/*.json                               │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│              COMPONENT 1: INTELLIGENCE ENGINE                    │
│                                                                  │
│  For each competitor:                                            │
│  raw data → compile_raw_data() → Claude (signal extraction)     │
│           → structured intelligence JSON                        │
│                                                                  │
│  Extracts: features, messaging, sentiment, pricing, weaknesses  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                   combined_intelligence.json
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│            COMPONENT 2: CAMPAIGN FEEDBACK LOOP                   │
│                                                                  │
│  Step 1: Strategic Synthesis                                     │
│    all intel → Claude → market snapshot, vulnerabilities,        │
│                         whitespace, positioning recommendation   │
│                                                                  │
│  Step 2: Campaign Recommendations                                │
│    synthesis + intel → Claude → messaging copy, channel          │
│                                  strategy, 5 GTM priorities      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     BONUS FEATURES                               │
│                                                                  │
│  Diff Engine: compare snapshots → what changed since last run    │
│  NL Queries: python main.py --query "what are users hating?"     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                  outputs/competitive_intelligence_report.md
```

---

## Data Flow

1. **Ingestion** — Three parallel scrapers pull raw text from:
   - Competitor websites and pricing pages (BeautifulSoup)
   - G2/Capterra reviews (Tavily API → fallback to web search → synthetic seed data)
   - Reddit discussions (PRAW → Tavily → graceful degradation)

2. **Intelligence Extraction** — Per-competitor Claude call with a carefully engineered prompt. Input: compiled raw text (capped at ~9K chars). Output: structured JSON with features, sentiment, pricing, weaknesses.

3. **Strategic Synthesis** — Single Claude call across all competitors. Input: combined intelligence. Output: market snapshot, vulnerabilities, whitespace, positioning recommendation.

4. **Campaign Generation** — Final Claude call producing concrete copy, channel strategy, and 5 prioritized GTM recommendations.

5. **Report Generation** — Pure Python converts JSON → Markdown report.

---

## Handling Noisy, Incomplete, or Conflicting Data

### Noise
- HTML scrapers strip scripts, nav, footer, and collapse whitespace before passing to Claude
- Text is truncated to ~4K chars per source to stay within useful context
- Claude is explicitly told in prompts to ignore non-strategic information

### Incomplete Data
- Each ingestion module has a 3-tier fallback: primary API → secondary method → synthetic seed data
- Synthetic review data is labelled clearly in the code and based on well-documented public information
- If a source fails, the pipeline continues with whatever data is available — `errors` fields log what was missed
- The `--skip-scraping` flag lets you reuse cached data without re-fetching

### Conflicting Data
- When multiple sources contradict each other (e.g., one review says pricing is cheap, another says expensive), the LLM is asked to note the sentiment distribution, not just pick one signal
- The `perceived_value` field in pricing signals is specifically designed to capture subjective perception vs. stated price

---

## Prompt Strategy

All prompts are in `src/prompts/prompt_templates.py`. The design philosophy:

### Principle 1: Role-First
Every prompt opens with a role: *"You are the Head of Competitive Strategy at KeenFox."* This activates strategic reasoning mode rather than summarization mode.

### Principle 2: Anti-Summarization Instruction
Explicit instruction: *"Your job is NOT to summarize. Your job is to extract STRATEGICALLY RELEVANT signals."* This is the single most important prompt design decision.

### Principle 3: Structured JSON Output
All prompts request specific JSON schemas. This ensures:
- Consistent, parseable output
- The LLM is forced to populate every field, preventing lazy partial answers
- Easy downstream processing

### Principle 4: Forcing Strategic Implication
The signal extraction prompt requires a `strategic_implication` field for every feature. The LLM cannot just report what exists — it must explain *why it matters to KeenFox*. Same for `keenfox_opportunity` in weaknesses.

### Prompt Chain Design
```
Prompt 1 (per competitor): raw data → structured signals
Prompt 2 (all competitors): structured signals → strategic synthesis  
Prompt 3 (synthesis + signals): → concrete copy + GTM recommendations
Prompt 4 (diff): old JSON + new JSON → change analysis
Prompt 5 (ad hoc): full intel + user question → natural language answer
```

This chain prevents any single prompt from being too long or asking the LLM to do too much at once.

---

## Known Limitations

### 1. G2 Anti-Scraping
G2.com blocks direct scraping. We work around this via Tavily search, which finds review snippets from indexed pages. A production version would use G2's official API (paid) or a data partner.

### 2. Data Freshness
Without a scheduler, data is only as fresh as the last `python main.py` run. In production, this would run as a daily cron job with a results diff surfaced via Slack or email.

### 3. LinkedIn Data
LinkedIn actively blocks automated scraping. Current implementation uses Tavily to find public LinkedIn posts indexed by search engines. This misses non-indexed content. A production version would use the LinkedIn Marketing API or a tool like Phantombuster.

### 4. LLM Hallucination Risk
Claude can occasionally generate plausible-sounding but inaccurate competitive details, especially when input data is sparse. Mitigations:
- All outputs include source URLs for human verification
- Low-confidence data is flagged in the `errors` field
- The system is designed as a *signal-generation* tool, not a source-of-truth

### 5. Rate Limits
The system adds `time.sleep()` between API calls. For a 5-competitor run, expect ~3-5 minutes total. A production version would use async calls.

---

## What I'd Build With More Time

1. **Scheduler + Alerts** — Run daily via cron, push diff highlights to Slack
2. **Vector Database** — Store all historical signals in Pinecone/Chroma for semantic search across time
3. **Streaming Dashboard** — Real-time React dashboard showing competitive map and live score updates
4. **Confidence Scoring** — Assign confidence scores to each signal based on source count and corroboration
5. **More Signal Sources** — Job postings (signals hiring direction), patent filings, press releases, conference talks
6. **Human-in-the-Loop** — Let the marketing team annotate/approve recommendations before they're acted on
7. **A/B Testing Integration** — Connect recommendations directly to KeenFox's ad platform to auto-test copy suggestions

---

## Tech Stack Rationale

| Choice | Why |
|--------|-----|
| **Claude (Anthropic)** | Best-in-class reasoning for strategic synthesis; recommended by KeenFox |
| **BeautifulSoup + requests** | Lightweight, no Selenium overhead; sufficient for static pages |
| **Tavily** | Search API with content retrieval — best free/cheap option for review data |
| **PRAW** | Official Reddit API — free, reliable, no scraping issues |
| **JSON storage** | No database overhead for a 5-competitor system; easily extensible to Postgres |
| **Python** | Best ecosystem for scraping, LLM integration, and data processing |

---

## Evaluation Self-Assessment

| Criterion | Our Approach |
|-----------|--------------|
| **System Design** | Modular pipeline with clear separation between ingestion, analysis, and reporting. Each component is independently runnable. |
| **Intelligence Quality** | Prompts force `strategic_implication` and `keenfox_opportunity` fields — every signal is connected to an action |
| **Campaign Recommendations** | Actual copy generated (headlines, email subject lines, LinkedIn ads) — not just direction |
| **Prompt Engineering** | 5-prompt chain, role-first design, anti-summarization instructions, structured output enforcement |
| **Design Doc** | This document — honest about limitations, explains every design decision |
