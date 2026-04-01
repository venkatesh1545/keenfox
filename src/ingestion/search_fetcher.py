# src/ingestion/search_fetcher.py
# Fetches LinkedIn posts, company news, and product changelogs via web search.
# Uses Tavily if available, otherwise falls back to DuckDuckGo HTML search.

import os
import json
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """
    Fetch search results from DuckDuckGo HTML — no API key needed.
    Returns list of {title, snippet, url} dicts.
    """
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")

        results = []
        for result in soup.select(".result")[:max_results]:
            title_el = result.select_one(".result__title")
            snippet_el = result.select_one(".result__snippet")
            link_el = result.select_one(".result__url")

            title = title_el.get_text(strip=True) if title_el else ""
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            url_text = link_el.get_text(strip=True) if link_el else ""

            if title or snippet:
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "url": url_text,
                })
        return results
    except Exception as e:
        print(f"    [WARN] DuckDuckGo search failed: {e}")
        return []


def _search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """Search using Tavily API for richer content."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_results, search_depth="basic")
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("content", "")[:400],
                "url": r.get("url", ""),
            })
        return results
    except Exception as e:
        print(f"    [WARN] Tavily search failed: {e}")
        return []


def _search(query: str, max_results: int = 5) -> list[dict]:
    """Try Tavily first, fall back to DuckDuckGo."""
    if os.getenv("TAVILY_API_KEY"):
        results = _search_tavily(query, max_results)
        if results:
            return results
    return _search_duckduckgo(query, max_results)


def fetch_linkedin_signals(competitor_name: str) -> list[dict]:
    """
    Search for LinkedIn posts and company updates for a competitor.
    LinkedIn blocks direct scraping; we find indexed posts via search.
    """
    queries = [
        f"{competitor_name} LinkedIn company update announcement 2025",
        f"{competitor_name} new feature launch product update site:linkedin.com",
    ]
    results = []
    for q in queries:
        results.extend(_search(q, max_results=3))
        time.sleep(0.5)
    return results[:5]


def fetch_changelog_signals(competitor_name: str, website: str) -> list[dict]:
    """
    Search for product changelogs and release notes.
    """
    queries = [
        f"{competitor_name} changelog new features 2025",
        f"{competitor_name} product updates release notes 2025",
        f"site:{website.replace('https://', '').replace('http://', '')} changelog OR releases",
    ]
    results = []
    for q in queries:
        results.extend(_search(q, max_results=3))
        time.sleep(0.5)
    return results[:5]


def fetch_news_signals(competitor_name: str) -> list[dict]:
    """
    Search for recent news mentions — funding, partnerships, strategy shifts.
    """
    queries = [
        f"{competitor_name} funding partnership acquisition news 2025",
        f"{competitor_name} CEO strategy announcement 2025",
    ]
    results = []
    for q in queries:
        results.extend(_search(q, max_results=3))
        time.sleep(0.5)
    return results[:5]


def fetch_search_signals(competitor_name: str, website: str) -> dict:
    """
    Main entry point: fetch LinkedIn, changelog, and news signals for a competitor.
    Returns structured dict with all search-based signals.
    """
    print(f"  Fetching search signals: {competitor_name}")

    result = {
        "source": "search",
        "competitor": competitor_name,
        "fetched_at": datetime.now().isoformat(),
        "linkedin_signals": [],
        "changelog_signals": [],
        "news_signals": [],
        "raw_text": "",
        "errors": [],
    }

    try:
        result["linkedin_signals"] = fetch_linkedin_signals(competitor_name)
        print(f"    LinkedIn: {len(result['linkedin_signals'])} results")
    except Exception as e:
        result["errors"].append(f"LinkedIn fetch failed: {e}")

    try:
        result["changelog_signals"] = fetch_changelog_signals(competitor_name, website)
        print(f"    Changelog: {len(result['changelog_signals'])} results")
    except Exception as e:
        result["errors"].append(f"Changelog fetch failed: {e}")

    try:
        result["news_signals"] = fetch_news_signals(competitor_name)
        print(f"    News: {len(result['news_signals'])} results")
    except Exception as e:
        result["errors"].append(f"News fetch failed: {e}")

    # Compile raw text for LLM
    all_results = (
        result["linkedin_signals"]
        + result["changelog_signals"]
        + result["news_signals"]
    )
    text_parts = []
    for r in all_results:
        if r.get("title") or r.get("snippet"):
            text_parts.append(
                f"[{r.get('title', 'No title')}]\n{r.get('snippet', '')}"
            )
    result["raw_text"] = "\n\n".join(text_parts)[:5000]

    if not result["raw_text"]:
        result["errors"].append("No search signals fetched")
        print(f"    [WARN] No search signals for {competitor_name}")

    return result


def fetch_all_search_signals(competitors: dict, output_dir: str) -> dict:
    """Fetch search signals for all competitors."""
    results = {}

    for key, comp in competitors.items():
        print(f"\n[Search] Processing {comp['name']}...")
        data = fetch_search_signals(comp["name"], comp["website"])
        results[key] = data

        output_path = os.path.join(output_dir, f"{key}_search.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"    Saved to {output_path}")

        time.sleep(1.5)

    return results
