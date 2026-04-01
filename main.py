#!/usr/bin/env python3
# main.py
# KeenFox Competitive Intelligence System — Main Entry Point
#
# Usage:
#   python main.py --brand "Coca-Cola"           # Discover competitors & analyze
#   python main.py --brand "Notion"              # Works for any brand
#   python main.py --brand "Coca-Cola" --skip-scraping  # Use cached data
#   python main.py --query "your question"       # Natural language query

import os
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate API key early
if not os.getenv("GEMINI_API_KEY"):
    print("\n❌ ERROR: GEMINI_API_KEY not found.")
    print("   1. Copy .env.example to .env")
    print("   2. Add your API key from Google AI Studio")
    sys.exit(1)

from src.config import LLM_MODEL
from src.discovery.competitor_finder import discover_competitors, build_brand_profile
from src.analysis.intelligence_engine import run_intelligence_engine
from src.analysis.campaign_integrator import run_campaign_integrator, answer_natural_language_query
from src.utils.diff_engine import run_diff_engine
from src.utils.report_generator import generate_full_report

# Paths
RAW_DIR = "data/raw"
REPORTS_DIR = "data/reports"
OUTPUTS_DIR = "outputs"


def setup_dirs():
    for d in [RAW_DIR, REPORTS_DIR, OUTPUTS_DIR]:
        os.makedirs(d, exist_ok=True)


def load_cached_raw_data(competitors: dict) -> dict:
    """Load previously scraped raw data from disk."""
    print("[Main] Loading cached raw data...")
    raw_data_by_competitor = {}

    for key in competitors:
        raw_data_by_competitor[key] = {}

        for source in ["website", "reviews", "reddit"]:
            path = os.path.join(RAW_DIR, f"{key}_{source}.json")
            if os.path.exists(path):
                with open(path) as f:
                    raw_data_by_competitor[key][source] = json.load(f)
                print(f"  ✓ Loaded {key} {source}")
            else:
                print(f"  ⚠ Missing {key} {source} — run without --skip-scraping")

    return raw_data_by_competitor


def _ingest_single_competitor(key: str, comp: dict, raw_dir: str) -> tuple:
    """Ingest all data for a single competitor (used in parallel)."""
    from src.ingestion.web_scraper import scrape_website
    from src.ingestion.review_fetcher import fetch_reviews
    from src.ingestion.reddit_fetcher import fetch_reddit_signals
    from src.ingestion.search_fetcher import fetch_search_signals

    data = {}
    name = comp['name']

    # Website
    website_data = scrape_website(name, comp['website'], comp['pricing_url'])
    with open(os.path.join(raw_dir, f"{key}_website.json"), "w", encoding="utf-8") as f:
        json.dump(website_data, f, indent=2)
    data['website'] = website_data

    # Reviews
    review_data = fetch_reviews(name, comp.get('g2_url', ''))
    with open(os.path.join(raw_dir, f"{key}_reviews.json"), "w", encoding="utf-8") as f:
        json.dump(review_data, f, indent=2)
    data['reviews'] = review_data

    # Reddit
    reddit_data = fetch_reddit_signals(name, comp.get('reddit_keywords', [name]))
    with open(os.path.join(raw_dir, f"{key}_reddit.json"), "w", encoding="utf-8") as f:
        json.dump(reddit_data, f, indent=2)
    data['reddit'] = reddit_data

    # Search signals
    search_data = fetch_search_signals(name, comp['website'])
    with open(os.path.join(raw_dir, f"{key}_search.json"), "w", encoding="utf-8") as f:
        json.dump(search_data, f, indent=2)
    data['search'] = search_data

    return key, data


def collect_raw_data(competitors: dict) -> dict:
    """Run all data ingestion pipelines in PARALLEL (one thread per competitor)."""
    print("\n" + "="*60)
    print("PHASE 1: DATA INGESTION (PARALLEL)")
    print("="*60)

    raw_data_by_competitor = {}

    with ThreadPoolExecutor(max_workers=len(competitors)) as executor:
        futures = {
            executor.submit(_ingest_single_competitor, key, comp, RAW_DIR): key
            for key, comp in competitors.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                k, data = future.result()
                raw_data_by_competitor[k] = data
                print(f"  ✓ {competitors[k]['name']} — all data collected")
            except Exception as e:
                print(f"  ✗ {key} — ingestion failed: {e}")
                raw_data_by_competitor[key] = {}

    print(f"\n✓ Data ingestion complete for {len(raw_data_by_competitor)} competitors.")
    return raw_data_by_competitor


def print_summary(campaign_output: dict, brand_name: str):
    """Print a quick summary to terminal after run."""
    print("\n" + "="*60)
    print(f"✅ {brand_name.upper()} INTELLIGENCE RUN COMPLETE")
    print("="*60)

    synthesis = campaign_output.get("strategic_synthesis", {})
    snapshot = synthesis.get("market_snapshot", {})

    if snapshot:
        print(f"\n🔴 Biggest Threat: {snapshot.get('biggest_threat', 'N/A')[:100]}...")
        print(f"💡 Biggest Opportunity: {snapshot.get('biggest_opportunity', 'N/A')[:100]}...")

    recs = campaign_output.get("campaign_recommendations", {})
    messaging = recs.get("messaging_and_positioning", {})
    if messaging.get("recommended_headline"):
        print(f"\n📢 Recommended Headline: \"{messaging['recommended_headline']}\"")

    gtm = recs.get("gtm_strategic_recommendations", [])
    if gtm:
        print(f"\n📋 Top GTM Recommendation:")
        top = gtm[0]
        print(f"   #{top.get('priority')}: {top.get('recommendation', '')}")

    print(f"\n📄 Full report: {OUTPUTS_DIR}/competitive_intelligence_report.md")
    print(f"📊 JSON data: {OUTPUTS_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="KeenFox Competitive Intelligence System")
    parser.add_argument("--brand", type=str, required=True, help="Brand name to analyze (e.g., 'Coca-Cola', 'Notion')")
    parser.add_argument("--query", type=str, help="Ask a natural language question about competitors")
    parser.add_argument("--skip-scraping", action="store_true", help="Skip data collection, use cached data")
    args = parser.parse_args()

    setup_dirs()
    brand_name = args.brand

    print(f"\n🦊 KeenFox Competitive Intelligence System")
    print(f"📅 Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏷️  Brand: {brand_name}")

    # Phase 0: AI-Powered Competitor Discovery
    print("\n" + "="*60)
    print("PHASE 0: AI-POWERED COMPETITOR DISCOVERY")
    print("="*60)

    competitors, brand_category = discover_competitors(brand_name)
    if not competitors:
        print("❌ Could not discover competitors. Please check your API key.")
        sys.exit(1)

    brand_profile = build_brand_profile(brand_name, brand_category)

    print(f"\n🏢 Discovered Competitors: {', '.join(c.get('name', k) for k, c in competitors.items())}")

    # Natural language query mode
    if args.query:
        combined_path = os.path.join(OUTPUTS_DIR, "combined_intelligence.json")
        if not os.path.exists(combined_path):
            print("❌ No intelligence data found. Run without --query first to generate data.")
            sys.exit(1)

        with open(combined_path) as f:
            all_intelligence = json.load(f)

        answer = answer_natural_language_query(args.query, all_intelligence)
        print(f"\n💬 Query: {args.query}")
        print(f"\n📖 Answer:\n{answer}")
        return

    # Phase 1: Data collection
    if args.skip_scraping:
        raw_data_by_competitor = load_cached_raw_data(competitors)
    else:
        raw_data_by_competitor = collect_raw_data(competitors)

    # Phase 2: Intelligence extraction (Component 1)
    all_intelligence = run_intelligence_engine(
        competitors,
        raw_data_by_competitor,
        OUTPUTS_DIR,
        brand_name=brand_name,
    )

    # Save combined intelligence for query mode
    combined_path = os.path.join(OUTPUTS_DIR, "combined_intelligence.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_intelligence, f, indent=2)

    # Phase 3: Campaign recommendations (Component 2)
    campaign_output = run_campaign_integrator(
        all_intelligence, OUTPUTS_DIR, brand_profile=brand_profile
    )

    # Phase 4: Diff engine (Bonus)
    diff_data = run_diff_engine(all_intelligence, campaign_output, REPORTS_DIR)

    # Phase 5: Generate report
    report_path = os.path.join(OUTPUTS_DIR, "competitive_intelligence_report.md")
    generate_full_report(all_intelligence, campaign_output, diff_data, report_path, brand_name=brand_name)

    # Print terminal summary
    print_summary(campaign_output, brand_name)


if __name__ == "__main__":
    main()
