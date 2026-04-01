# src/ingestion/reddit_fetcher.py
# Fetches Reddit discussions about competitors from r/projectmanagement and related subs.
# Uses PRAW (Reddit API) if credentials available, falls back to Pushshift/web search.

import os
import json
import time
from datetime import datetime
from typing import Optional


SUBREDDITS = [
    "projectmanagement",
    "productivity",
    "Entrepreneur",
    "smallbusiness",
    "remotework",
    "SaaS",
]


def _fetch_via_praw(keywords: list[str], subreddits: list[str], limit: int = 20) -> list[dict]:
    """Use Reddit's official API via PRAW."""
    try:
        import praw
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "KeenFoxIntel/1.0"),
        )

        posts = []
        for subreddit_name in subreddits[:3]:  # Limit to avoid rate limits
            subreddit = reddit.subreddit(subreddit_name)
            for keyword in keywords[:2]:
                try:
                    for submission in subreddit.search(keyword, limit=5, time_filter="year"):
                        posts.append({
                            "subreddit": subreddit_name,
                            "title": submission.title,
                            "text": submission.selftext[:500],
                            "score": submission.score,
                            "num_comments": submission.num_comments,
                            "url": f"https://reddit.com{submission.permalink}",
                            "top_comments": _get_top_comments(submission, limit=3),
                        })
                except Exception:
                    continue
            time.sleep(0.5)

        return posts

    except Exception as e:
        print(f"    [WARN] PRAW fetch failed: {e}")
        return []


def _get_top_comments(submission, limit: int = 3) -> list[str]:
    """Get top comments from a Reddit post."""
    try:
        submission.comments.replace_more(limit=0)
        comments = []
        for comment in submission.comments[:limit]:
            if hasattr(comment, "body") and len(comment.body) > 50:
                comments.append(comment.body[:300])
        return comments
    except Exception:
        return []


def _fetch_via_tavily(competitor_name: str, keywords: list[str]) -> list[dict]:
    """Use Tavily to search Reddit for competitor mentions."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = f"site:reddit.com {competitor_name} review experience {keywords[0]}"
        response = client.search(query=query, max_results=5, search_depth="basic")

        posts = []
        for r in response.get("results", []):
            if "reddit.com" in r.get("url", ""):
                posts.append({
                    "subreddit": "reddit",
                    "title": r.get("title", ""),
                    "text": r.get("content", "")[:500],
                    "url": r.get("url", ""),
                    "top_comments": [],
                })
        return posts

    except Exception as e:
        print(f"    [WARN] Tavily Reddit search failed: {e}")
        return []


def fetch_reddit_signals(competitor_name: str, keywords: list[str]) -> dict:
    """
    Fetch Reddit discussions mentioning a competitor.
    Tries PRAW first, then Tavily, then returns empty with note.
    """
    print(f"  Fetching Reddit signals: {competitor_name}")

    result = {
        "source": "reddit",
        "competitor": competitor_name,
        "fetched_at": datetime.now().isoformat(),
        "posts": [],
        "raw_text": "",
        "errors": [],
    }

    # Try PRAW first
    if os.getenv("REDDIT_CLIENT_ID"):
        posts = _fetch_via_praw(keywords, SUBREDDITS)
        if posts:
            result["posts"] = posts
            print(f"    ✓ Found {len(posts)} Reddit posts via PRAW")

    # Try Tavily if PRAW empty
    if not result["posts"] and os.getenv("TAVILY_API_KEY"):
        posts = _fetch_via_tavily(competitor_name, keywords)
        result["posts"] = posts
        print(f"    ✓ Found {len(posts)} Reddit results via Tavily")

    # Compile raw text for LLM processing
    text_parts = []
    for post in result["posts"]:
        text_parts.append(f"Title: {post['title']}\nContent: {post['text']}")
        for comment in post.get("top_comments", []):
            text_parts.append(f"Comment: {comment}")

    result["raw_text"] = "\n\n".join(text_parts)[:6000]

    if not result["posts"]:
        result["errors"].append("No Reddit data fetched — configure REDDIT or TAVILY API keys")
        print(f"    [INFO] No Reddit data for {competitor_name}")

    return result


def fetch_all_reddit(competitors: dict, output_dir: str) -> dict:
    """Fetch Reddit signals for all competitors."""
    results = {}

    for key, comp in competitors.items():
        print(f"\n[Reddit] Processing {comp['name']}...")
        data = fetch_reddit_signals(comp["name"], comp["reddit_keywords"])
        results[key] = data

        output_path = os.path.join(output_dir, f"{key}_reddit.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"    ✓ Saved to {output_path}")

        time.sleep(1)

    return results
