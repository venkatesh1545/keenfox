# src/analysis/intelligence_engine.py
# Component 1: Competitive Intelligence Engine
# Takes raw scraped data → uses Claude to extract structured strategic signals

import os
import json
import time
from datetime import datetime
from typing import Optional
from google import genai

from src.prompts.prompt_templates import SIGNAL_EXTRACTION_PROMPT
from src.config import LLM_MODEL, LLM_MAX_TOKENS


def _call_gemini(prompt: str) -> Optional[str]:
    """
    Call Gemini API and return text response.
    Handles errors and rate limits gracefully.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Resource Exhausted" in err_str:
                wait_time = 15 * (attempt + 1)
                print(f"    [WARN] Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"    [ERROR] Gemini API call failed: {e}")
                return None
    
    print("    [ERROR] Max retries reached for Gemini API.")
    return None


def _parse_json_response(response: str, fallback_key: str = "data") -> dict:
    """
    Safely parse JSON from Claude response.
    Handles cases where Claude adds extra text around JSON.
    """
    if not response:
        return {"error": "No response from LLM"}

    # Try direct parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON block
    import re
    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Return raw text if JSON parsing fails
    return {fallback_key: response, "parse_error": True}


def compile_raw_data(competitor_key: str, competitor_name: str, raw_data: dict) -> str:
    """
    Compile all raw data sources for a competitor into a single text block
    for LLM processing.
    """
    parts = []

    website_data = raw_data.get("website", {})
    if website_data.get("homepage_text"):
        parts.append(f"=== HOMEPAGE CONTENT ===\n{website_data['homepage_text'][:2000]}")
    if website_data.get("pricing_text"):
        parts.append(f"=== PRICING PAGE ===\n{website_data['pricing_text'][:2000]}")

    review_data = raw_data.get("reviews", {})
    if review_data.get("raw_text"):
        parts.append(f"=== CUSTOMER REVIEWS & FEEDBACK ===\n{review_data['raw_text'][:3000]}")

    reddit_data = raw_data.get("reddit", {})
    if reddit_data.get("raw_text"):
        parts.append(f"=== REDDIT COMMUNITY DISCUSSIONS ===\n{reddit_data['raw_text'][:2000]}")

    search_data = raw_data.get('search', {})
    if search_data.get('raw_text'):
        parts.append(f"=== LINKEDIN / CHANGELOG / NEWS ===\n{search_data['raw_text'][:2000]}")

    if not parts:
        return f"Limited data available for {competitor_name}. Analysis may be incomplete."

    return "\n\n".join(parts)


def extract_competitor_intelligence(
    competitor_key: str,
    competitor_config: dict,
    raw_data: dict,
    output_dir: str,
    brand_name: str = "KeenFox",
) -> dict:
    """
    Run the intelligence extraction pipeline for one competitor.
    Returns structured intelligence dict.
    """
    print(f"\n[Intelligence Engine] Analyzing {competitor_config['name']}...")

    compiled_data = compile_raw_data(
        competitor_key,
        competitor_config["name"],
        raw_data,
    )

    # Build prompt
    prompt = SIGNAL_EXTRACTION_PROMPT.format(
        competitor_name=competitor_config["name"],
        competitor_category=competitor_config["category"],
        raw_data=compiled_data,
        timestamp=datetime.now().isoformat(),
        brand_name=brand_name,
    )

    print(f"  Calling Gemini for signal extraction...")
    response = _call_gemini(prompt)
    time.sleep(1)  # Rate limiting

    intelligence = _parse_json_response(response, fallback_key="raw_analysis")

    # Add metadata
    intelligence["_meta"] = {
        "competitor_key": competitor_key,
        "analyzed_at": datetime.now().isoformat(),
        "data_sources": [k for k, v in raw_data.items() if v],
        "model_used": LLM_MODEL,
    }

    # Save
    output_path = os.path.join(output_dir, f"{competitor_key}_intelligence.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(intelligence, f, indent=2)
    print(f"  ✓ Intelligence extracted and saved")

    return intelligence


def run_intelligence_engine(
    competitors: dict,
    raw_data_by_competitor: dict,
    output_dir: str,
    brand_name: str = "KeenFox",
) -> dict:
    """
    Run the full intelligence extraction pipeline for all competitors.
    Returns dict of competitor_key -> intelligence_data.
    """
    print("\n" + "="*60)
    print("COMPONENT 1: COMPETITIVE INTELLIGENCE ENGINE")
    print("="*60)

    all_intelligence = {}

    for key, comp in competitors.items():
        raw_data = raw_data_by_competitor.get(key, {})
        intelligence = extract_competitor_intelligence(
            key, comp, raw_data, output_dir, brand_name=brand_name
        )
        all_intelligence[key] = intelligence

    # Save combined intelligence
    combined_path = os.path.join(output_dir, "combined_intelligence.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_intelligence, f, indent=2)

    print(f"\n✓ Intelligence engine complete. Analyzed {len(all_intelligence)} competitors.")
    return all_intelligence
