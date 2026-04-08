# KeenFox Competitive Intelligence System — Design Document

## 1. Problem Statement

Most competitive intelligence is done manually: analysts Google competitors, read review sites, scan Reddit, and manually compile findings into spreadsheets. This process is:

- **Slow** — Takes hours per competitor, per cycle
- **Incomplete** — Humans miss signals across multiple channels
- **Subjective** — Insights depend on the analyst's bias and experience
- **Stale** — By the time the report is ready, the data is already outdated
- **Non-scalable** — Adding a new competitor means redoing the entire process

**Goal**: Build an automated system that takes any brand name as input and produces a structured competitive intelligence report with actionable campaign recommendations — in minutes, not days.

---

## 2. System Design

### 2.1 High-Level Architecture

The system follows a **staged pipeline architecture** with five distinct phases:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│   Phase 0    │    │   Phase 1    │    │   Phase 2    │    │   Phase 3    │    │ Phase 4  │
│   Discovery  │───▶│  Ingestion   │───▶│  Extraction  │───▶│  Synthesis   │───▶│  Output  │
│   (Gemini)   │    │  (Parallel)  │    │  (Gemini)    │    │  (Gemini)    │    │  (JSON/  │
│              │    │              │    │              │    │              │    │  Report) │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────┘
```

**Design Principle — Separation of Concerns**: Each phase produces a well-defined intermediate output (JSON) that feeds into the next phase. This makes it possible to:
- Debug any phase independently
- Cache intermediate results (`--skip-scraping`)
- Replace any phase (e.g., swap Gemini for GPT-4) without touching the rest
- Run phases in different modes (parallel vs. sequential)

### 2.2 Module Responsibility Map

| Module | Responsibility | I/O |
|--------|---------------|-----|
| `competitor_finder.py` | AI-powered competitor discovery + brand profiling | Brand name → Competitor dict + Brand profile |
| `web_scraper.py` | Homepage and pricing page scraping | URLs → Clean text |
| `review_fetcher.py` | G2/Capterra review collection | Competitor name → Review snippets |
| `reddit_fetcher.py` | Reddit discussion mining | Keywords → Posts + comments |
| `search_fetcher.py` | LinkedIn, changelog, and news search | Competitor name → Signal list |
| `intelligence_engine.py` | Per-competitor LLM signal extraction | Raw data → Structured intelligence JSON |
| `campaign_integrator.py` | Cross-competitor synthesis + campaign generation | All intelligence → Strategy brief + recommendations |
| `diff_engine.py` | Temporal change detection | Current vs. previous report → Change diff |
| `report_generator.py` | JSON → Markdown report formatting | Structured data → Human-readable report |
| `prompt_templates.py` | Centralized prompt management | Template strings with placeholders |

### 2.3 Why This Architecture?

**Alternative 1: Monolithic single-script approach**
- Simpler to write initially, but impossible to test, debug, or extend
- Rejected because competitive intelligence has fundamentally different concerns (data collection vs. analysis vs. reporting)

**Alternative 2: Microservices with message queues**
- Better for production at scale, but over-engineered for this use case
- Would require infrastructure (Redis, Celery, etc.) that adds complexity without proportional benefit

**Chosen: Modular pipeline with well-defined interfaces**
- Each module is a Python file with clear input/output contracts
- Modules can be tested independently
- Adding a new data source means adding one file in `ingestion/` — no changes to analysis or reporting

---

## 3. Intelligence Quality

### 3.1 Multi-Source Data Fusion

The system doesn't rely on a single data source. For each competitor, it collects:

| Source | What It Captures | Why It Matters |
|--------|-----------------|----------------|
| Homepage | Messaging, positioning, value props | How they want to be perceived |
| Pricing page | Pricing model, tiers, perceived value | Economic positioning |
| G2/Capterra reviews | Real customer sentiment (pros/cons) | How they're actually perceived |
| Reddit discussions | Unfiltered opinions, migration stories | Ground truth from actual users |
| LinkedIn posts | Corporate strategy signals, hiring trends | Strategic direction |
| News/changelogs | Feature launches, funding, partnerships | Competitive moves in real time |

This multi-source approach means the LLM has **diverse evidence** to reason from, producing insights that are non-obvious and grounded.

### 3.2 Signal Extraction — Not Summarization

The key design decision in the intelligence engine is that it extracts **strategically relevant signals**, not summaries. The prompt explicitly instructs:

> "Your job is NOT to summarize. Your job is to extract STRATEGICALLY RELEVANT signals."

Each extracted signal includes:
- **Evidence**: What specific data supports this finding
- **Strategic implication**: Why this matters competitively
- **Urgency classification**: High / Medium / Low
- **Exploitability**: Concrete action the brand can take

This forces the LLM to **reason about competitive implications** rather than just restating what it read.

### 3.3 Trade-offs

| Trade-off | Decision | Rationale |
|-----------|----------|-----------|
| Data freshness vs. API costs | Cache scraped data for 12 hours | Websites don't change hourly; saves API calls |
| Scraping depth vs. speed | Truncate text to 4000-8000 chars | LLM context windows and cost; most signal is in the first few thousand chars |
| Tavily vs. free scraping | Try Tavily first, fall back to DuckDuckGo | Tavily gives richer content but isn't free at scale; DuckDuckGo is always available |
| Parallel vs. sequential ingestion | Parallel with ThreadPoolExecutor | ~4x speedup with no correctness trade-off (I/O-bound tasks) |

---

## 4. Campaign Recommendations

### 4.1 Two-Stage Reasoning

The campaign engine uses a **two-stage architecture** rather than a single prompt:

**Stage 1 — Strategic Synthesis**: Takes intelligence from ALL competitors and produces a cross-competitor analysis:
- Market snapshot (biggest threat, biggest opportunity, whitespace, trend)
- Competitor vulnerabilities with exploitation strategies
- Market messaging gaps
- Positioning recommendation with proof points

**Stage 2 — Tactical Recommendations**: Takes the synthesis + raw signals + brand profile and generates specific, executable recommendations:
- Actual headline copy, email subject lines, LinkedIn ad copy
- Channel strategy (double-down / pull-back / new channels to test)
- 5 prioritized GTM recommendations with KPIs, timelines, and data backing

### 4.2 Why Two Stages?

A single prompt that goes from raw data → campaign recommendations produces generic advice. By separating synthesis from recommendations:
1. The synthesis acts as a "thinking step" — the LLM first builds a strategic model
2. The recommendations can reference the synthesis for grounding
3. Each prompt stays within a focused reasoning scope
4. Outputs can be independently validated

### 4.3 Grounding Enforcement

Every recommendation requires a `competitive_data_backing` field that must cite specific competitive intelligence. This prevents hallucinated or generic advice like "invest in content marketing" and forces outputs like:

> "Launch comparison landing pages targeting ClickUp's complaint about 'buggy performance' — 47% of their G2 reviews mention reliability issues."

---

## 5. Prompt Engineering

### 5.1 Design Principles

1. **Role Framing**: Each prompt assigns a specific expert role ("Head of Competitive Strategy", "senior marketing strategist") to set the reasoning frame
2. **Anti-Summary Instructions**: Explicit instructions like "Your job is NOT to summarize" prevent the LLM from defaulting to safe regurgitation
3. **Structured JSON Output**: All prompts demand exact JSON schemas with mandatory fields, ensuring parseable and actionable output
4. **Reasoning Directives**: Prompts include explicit reasoning questions ("Ask: What does this mean for positioning? Where are competitors vulnerable RIGHT NOW?")
5. **Brand-Agnostic Templates**: All prompts use `{brand_name}` placeholders so the same pipeline works for any brand

### 5.2 Prompt Catalog

| Prompt | Purpose | Key Engineering Decision |
|--------|---------|------------------------|
| `SIGNAL_EXTRACTION_PROMPT` | Extract competitive signals from raw data | Forces urgency classification + strategic implication per signal |
| `STRATEGIC_SYNTHESIS_PROMPT` | Cross-competitor analysis | Frames 5 explicit strategic questions the LLM must answer |
| `CAMPAIGN_RECOMMENDATIONS_PROMPT` | Tactical GTM output | Requires actual copy (headlines, emails) not just advice |
| `DIFF_ANALYSIS_PROMPT` | Temporal change detection | Instructs to focus on "strategically meaningful changes — not cosmetic differences" |
| `NATURAL_LANGUAGE_QUERY_PROMPT` | Ad-hoc questions | Grounds answer in provided data; admits when data is insufficient |
| `COMPETITOR_DISCOVERY_PROMPT` | Find competitors for any brand | Requires website URLs, pricing URLs, Reddit keywords — structured output for pipeline compatibility |
| `BRAND_PROFILE_PROMPT` | Generate brand strategic profile | Outputs in same format as manual config so existing code works unchanged |

### 5.3 Why Gemini 2.5 Flash?

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Gemini 2.5 Pro | Highest reasoning quality | Very strict free-tier quota (50 req/day) → pipeline crashes | Rejected for default use |
| Gemini 2.5 Flash | Fast, generous free tier (1500 req/day), good reasoning | Slightly less capable than Pro for nuanced strategy | **Selected** — best trade-off for pipeline reliability |
| GPT-4o | Strong reasoning, wide adoption | Requires OpenAI API key, no free tier | Not selected — adds dependency |
| Claude 3.5 Sonnet | Excellent for analysis | Original choice but API key issues prompted migration | Migrated away from |

---

## 6. Technical Trade-offs & Decisions

### 6.1 Dynamic Discovery vs. Hardcoded Competitors

**Original design**: Hardcoded competitor list in `config.py`
**Current design**: AI discovers competitors dynamically from brand name input

**Trade-off**: Dynamic discovery uses an extra LLM call (cost + latency) but makes the system genuinely useful for any brand. The AI may occasionally identify unexpected competitors, but this is a *feature* — it reveals competitive threats the user might not have considered.

### 6.2 Parallel Ingestion

**Risk**: Multiple threads hitting the same external services could trigger rate limits
**Mitigation**: Each thread handles a different competitor (different websites), so rate limiting per domain isn't an issue. Added 1-2 second delays within each thread between requests.

### 6.3 LLM Rate Limit Handling

**Problem**: Free-tier Gemini quotas cause `429 RESOURCE_EXHAUSTED` errors mid-pipeline
**Solution**: Exponential backoff retry loop (3 attempts, 15s/30s/45s delays). This keeps the pipeline alive without requiring paid API access.

### 6.4 Tavily Optional Dependency

**Problem**: Not all users will have a Tavily API key
**Solution**: Every Tavily call has a DuckDuckGo HTML fallback. The code checks for the key *before* importing the library, avoiding even the import error. No Tavily = graceful degradation, not failure.

### 6.5 System Upgrades (v2): Scaling to Production

To move the project from a prototype state into an interview-level enterprise standard, three core mechanisms were upgraded:

1. **Optimization (Parallelization)** — `intelligence_engine.py` heavily relied on a single-threaded architecture (linear loop) which skyrocketed analysis latency natively. We swapped this directly for `concurrent.futures.ThreadPoolExecutor` which spins parallel inference sessions with the LLM API instantly.
2. **Error Robustness** — Eliminated rigid loops and inserted **Exponential Backoff (`wait_time = (2 ** attempt) * 5`)** algorithms natively targeting HTTP 429/503 network drops. Further, introduced a strict python validation layer (`required_keys` verification) forcing blank-schemas, mathematically preventing any downstream runtime `KeyError` crashes.
3. **Guardrails & Grounding** — Locked the generative models output exclusively using `response_mime_type="application/json"` backend flags enforcing type safety. To prevent data hallucinations entirely, we mandated an internal `analysis_thought_process` block requiring explicit "Chain-of-Thought" reasoning. The engine forces the agent to cite and review scraped material before formulating cross-competitive insights.

---

## 7. Extensibility

The modular architecture supports several natural extensions:

| Extension | Effort | What Changes |
|-----------|--------|-------------|
| Add new data source (e.g., Glassdoor) | Add one file in `ingestion/` | No other changes needed |
| Add web dashboard | Add `app.py` + `templates/` | Pipeline code unchanged |
| Switch to GPT-4 | Change `LLM_MODEL` in config + update `genai` calls | Prompts unchanged |
| Add more competitors per run | Change discovery prompt to request 8-10 | No code changes |
| Add email alerts on diff | Add alert logic after `diff_engine` | Pipeline unchanged |
| Schedule daily runs | Add cron job / Windows Task Scheduler | Just run `main.py` |

---

## 8. Known Limitations

1. **Web scraping fragility**: Some websites (Red Bull, Dr Pepper) block scraping with 403 errors. The system handles this gracefully but gets less data for those competitors.
2. **LLM JSON reliability**: Occasionally the LLM returns non-JSON or wraps JSON in markdown code blocks. The `_parse_json_response` function handles this with regex extraction fallback.
3. **Rate limits**: Free-tier Gemini allows ~1500 requests/day for Flash. A single run uses ~10-12 LLM calls (2 for discovery + 6 for extraction + 2 for synthesis + 1-2 for diff). This supports ~100+ runs/day.
4. **No real-time monitoring**: The system produces point-in-time reports. Continuous monitoring would require a scheduler and persistence layer.
5. **Intelligence extraction depth depends on data quality**: If a competitor's website has minimal text or reviews are sparse, the LLM has less to reason from. The system reports this transparently rather than hallucinating.
