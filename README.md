# 🦊 KeenFox Competitive Intelligence System

An AI-powered pipeline that monitors competitors in the B2B SaaS productivity market and generates concrete campaign recommendations — built with Claude (Anthropic).

---

## What It Does

1. **Scrapes** competitor websites, pricing pages, G2 reviews, and Reddit discussions
2. **Extracts** strategic signals: feature launches, customer sentiment, pricing, weaknesses
3. **Synthesizes** across all competitors to find whitespace and vulnerabilities
4. **Generates** actual campaign copy (headlines, email subjects, LinkedIn ads) + 5 prioritized GTM recommendations

---

## Competitors Tracked

| Competitor | Category |
|-----------|---------|
| Notion | All-in-one workspace |
| Asana | Project Management |
| ClickUp | Project Management |
| Monday.com | Work OS |
| Microsoft 365 Copilot | AI Productivity Suite |

---

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/keenfox-intel
cd keenfox-intel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=your_key_here   # Required — get free at console.anthropic.com
TAVILY_API_KEY=your_key_here       # Optional but recommended — get free at tavily.com
REDDIT_CLIENT_ID=your_id           # Optional — get free at reddit.com/prefs/apps
REDDIT_CLIENT_SECRET=your_secret
```

### 3. Run

```bash
# Full pipeline (scraping + analysis + report)
python main.py

# Skip scraping, use cached data (faster re-runs)
python main.py --skip-scraping

# Single competitor
python main.py --competitor clickup

# Ask a natural language question (run full pipeline first)
python main.py --query "What are customers complaining about in Asana?"
```

---

## Output

After running, check `outputs/`:

```
outputs/
├── competitive_intelligence_report.md   ← Main report (start here)
├── combined_intelligence.json           ← All extracted signals
├── strategic_synthesis.json             ← Market analysis
├── campaign_recommendations.json        ← Campaign recommendations
└── full_campaign_output.json            ← Combined JSON
```

---

## Project Structure

```
keenfox-intel/
├── main.py                         # Entry point
├── design_doc.md                   # Technical design document
├── requirements.txt
├── .env.example
├── src/
│   ├── config.py                   # Competitor configs + KeenFox profile
│   ├── ingestion/
│   │   ├── web_scraper.py          # Homepage + pricing scraping
│   │   ├── review_fetcher.py       # G2/Capterra reviews
│   │   └── reddit_fetcher.py       # Reddit community signals
│   ├── analysis/
│   │   ├── intelligence_engine.py  # Component 1: Signal extraction
│   │   └── campaign_integrator.py  # Component 2: Campaign recommendations
│   ├── prompts/
│   │   └── prompt_templates.py     # All LLM prompts centralized
│   └── utils/
│       ├── diff_engine.py          # What changed since last run
│       └── report_generator.py     # JSON → Markdown report
├── data/
│   ├── raw/                        # Cached scraped data
│   └── reports/                    # Timestamped run snapshots
└── outputs/                        # Final reports
```

---

## API Keys Guide

| Key | Required? | Where to get | Cost |
|-----|-----------|--------------|------|
| `ANTHROPIC_API_KEY` | ✅ Yes | [console.anthropic.com](https://console.anthropic.com) | $5 free credit on signup |
| `TAVILY_API_KEY` | Recommended | [tavily.com](https://tavily.com) | 1,000 free searches/month |
| Reddit keys | Optional | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) | Free |

The system works without Tavily and Reddit keys — it falls back gracefully with synthetic seed data labelled as illustrative.

---

## Sample Report Preview

```
## 📢 Campaign Recommendations

**Recommended Homepage Headline:**
> "Everything Asana charges extra for — included free in KeenFox"

**Cold Email Subject:** `Your team is paying 3x for features you should already have`

**Top GTM Recommendation:**
#1 🔴 Attack Asana's pricing confusion with a transparent pricing campaign
- Why: 847+ Asana reviews mention "too expensive" or "pricing not transparent"
- KPI: 20% increase in trial sign-ups from Asana comparison pages
- Timeline: Immediate
```

---

## Design Decisions

See [design_doc.md](design_doc.md) for full architecture, prompt strategy, and known limitations.
