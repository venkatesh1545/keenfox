# src/ingestion/web_scraper.py
# Scrapes competitor websites and pricing pages for signals

import requests
import json
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 15  # seconds


def _safe_get(url: str) -> Optional[str]:
    """Fetch a URL safely, return text or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    [WARN] Could not fetch {url}: {e}")
        return None


def _extract_text(html: str, max_chars: int = 8000) -> str:
    """Extract clean text from HTML, truncated to max_chars."""
    soup = BeautifulSoup(html, "lxml")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "meta", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Collapse whitespace
    import re
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def scrape_website(competitor_name: str, website_url: str, pricing_url: str) -> dict:
    """
    Scrape homepage and pricing page for a competitor.
    Returns structured raw data dict.
    """
    print(f"  Scraping website: {competitor_name}")
    result = {
        "source": "website",
        "competitor": competitor_name,
        "scraped_at": datetime.now().isoformat(),
        "homepage_text": "",
        "pricing_text": "",
        "errors": [],
    }

    # Homepage
    html = _safe_get(website_url)
    if html:
        result["homepage_text"] = _extract_text(html, max_chars=4000)
        print(f"    ✓ Homepage scraped ({len(result['homepage_text'])} chars)")
    else:
        result["errors"].append(f"Failed to fetch homepage: {website_url}")

    time.sleep(1.5)  # Be polite

    # Pricing page
    html = _safe_get(pricing_url)
    if html:
        result["pricing_text"] = _extract_text(html, max_chars=4000)
        print(f"    ✓ Pricing page scraped ({len(result['pricing_text'])} chars)")
    else:
        result["errors"].append(f"Failed to fetch pricing: {pricing_url}")

    return result


def scrape_all_competitors(competitors: dict, output_dir: str) -> dict:
    """
    Scrape websites for all competitors.
    Saves raw data and returns dict of results.
    """
    results = {}

    for key, comp in competitors.items():
        print(f"\n[Scraper] Processing {comp['name']}...")
        data = scrape_website(comp["name"], comp["website"], comp["pricing_url"])
        results[key] = data

        # Save raw data
        output_path = os.path.join(output_dir, f"{key}_website.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"    ✓ Saved to {output_path}")

        time.sleep(2)  # Rate limiting

    return results
