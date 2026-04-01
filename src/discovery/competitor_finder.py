# src/discovery/competitor_finder.py
# AI-powered competitor discovery using Gemini.
# Given any brand name, discovers direct and indirect competitors.

import os
import json
import time
from typing import Optional
from google import genai

from src.config import LLM_MODEL

COMPETITOR_DISCOVERY_PROMPT = """
You are an expert market research analyst. Given a brand name, your job is to identify its top competitors — both direct and indirect.

Brand: {brand_name}

Instructions:
1. Identify 4-6 competitors (mix of direct and indirect).
2. For each competitor, provide their official website URL, a pricing page URL (best guess if unknown), the product category, and relevant Reddit search keywords.
3. Think broadly — include well-known rivals AND emerging disruptors.

Return ONLY a valid JSON object with this structure:
{{
  "brand_name": "{brand_name}",
  "brand_category": "the industry/category this brand operates in",
  "competitors": {{
    "competitor_key": {{
      "name": "Competitor Name",
      "website": "https://competitor.com",
      "pricing_url": "https://competitor.com/pricing",
      "g2_url": "https://www.g2.com/products/competitor-name/reviews",
      "reddit_keywords": ["competitor name", "competitor product"],
      "category": "Product Category",
      "why_competitor": "1 sentence on why this is a competitor"
    }}
  }}
}}

Use lowercase keys with no spaces for competitor_key (e.g. "pepsi", "thums_up", "coca_cola_zero").
Return ONLY valid JSON. No preamble, no explanation.
"""

BRAND_PROFILE_PROMPT = """
You are a brand strategist. Given a brand name and its category, create a strategic profile for the brand.

Brand: {brand_name}
Category: {brand_category}

Return ONLY a valid JSON object:
{{
  "name": "{brand_name}",
  "category": "{brand_category}",
  "current_tagline": "their known tagline or a description of their positioning",
  "current_channels": ["list", "of", "marketing", "channels", "they", "use"],
  "current_strengths": ["strength1", "strength2", "strength3"],
  "target_audience": "description of their target audience",
  "pricing_model": "their pricing approach"
}}

Return ONLY valid JSON.
"""


def _call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini API with retry logic for rate limits."""
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
            if "429" in err_str or "Resource" in err_str:
                wait_time = 15 * (attempt + 1)
                print(f"    [WARN] Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"    [ERROR] Gemini API call failed: {e}")
                return None

    print("    [ERROR] Max retries reached for Gemini API.")
    return None


def _parse_json(response: str) -> dict:
    """Safely parse JSON from LLM response."""
    if not response:
        return {"error": "No LLM response"}
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"error": "Could not parse JSON", "raw": response}


def discover_competitors(brand_name: str) -> dict:
    """
    Use AI to discover competitors for any given brand.
    Returns a dict in the same format as COMPETITORS in config.py.
    """
    print(f"\n[Discovery] Finding competitors for '{brand_name}'...")
    prompt = COMPETITOR_DISCOVERY_PROMPT.format(brand_name=brand_name)
    response = _call_gemini(prompt)
    time.sleep(2)

    result = _parse_json(response)

    if "error" in result:
        print(f"    [ERROR] Could not discover competitors: {result.get('error')}")
        return {}

    competitors = result.get("competitors", {})
    brand_category = result.get("brand_category", "Unknown")

    print(f"    ✓ Discovered {len(competitors)} competitors:")
    for key, comp in competitors.items():
        print(f"      - {comp.get('name', key)}: {comp.get('why_competitor', '')}")

    return competitors, brand_category


def build_brand_profile(brand_name: str, brand_category: str) -> dict:
    """
    Use AI to generate a strategic profile for the input brand.
    Returns a dict in the same format as KEENFOX_PROFILE in config.py.
    """
    print(f"\n[Discovery] Building brand profile for '{brand_name}'...")
    prompt = BRAND_PROFILE_PROMPT.format(
        brand_name=brand_name,
        brand_category=brand_category,
    )
    response = _call_gemini(prompt)
    time.sleep(2)

    profile = _parse_json(response)

    if "error" in profile:
        print(f"    [WARN] Could not build AI profile, using defaults.")
        return {
            "name": brand_name,
            "category": brand_category,
            "current_tagline": f"{brand_name} — leading brand",
            "current_channels": ["Digital", "Social Media", "Content Marketing"],
            "current_strengths": ["Brand Recognition"],
            "target_audience": "General consumers",
            "pricing_model": "Various",
        }

    print(f"    ✓ Brand profile generated")
    return profile
