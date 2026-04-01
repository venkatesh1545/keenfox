# src/analysis/campaign_integrator.py
# Component 2: Campaign Feedback Loop Integrator
# Takes intelligence → uses Claude to generate strategic campaign recommendations

import os
import json
import time
from datetime import datetime
from typing import Optional
from google import genai

from src.prompts.prompt_templates import (
    STRATEGIC_SYNTHESIS_PROMPT,
    CAMPAIGN_RECOMMENDATIONS_PROMPT,
    NATURAL_LANGUAGE_QUERY_PROMPT,
)
from src.config import LLM_MODEL, LLM_MAX_TOKENS


def _call_gemini(prompt: str, max_tokens: int = LLM_MAX_TOKENS) -> Optional[str]:
    """Call Gemini API, return text response."""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=max_tokens,
            ),
        )
        return response.text
    except Exception as e:
        print(f"    [ERROR] Gemini API call failed: {e}")
        return None


def _parse_json_response(response: str) -> dict:
    """Parse JSON from Claude response safely."""
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
    return {"raw": response, "parse_error": True}


def _summarize_intelligence(all_intelligence: dict) -> str:
    """
    Create a concise summary of all intelligence for the campaign prompt.
    Keeps token usage manageable.
    """
    summaries = []
    for key, intel in all_intelligence.items():
        comp_name = intel.get("competitor", key)
        parts = [f"\n## {comp_name}"]

        # Feature launches
        features = intel.get("feature_launches", [])
        if features:
            feature_list = [f["feature"] for f in features[:3]]
            parts.append(f"Recent launches: {', '.join(feature_list)}")

        # Weaknesses
        weaknesses = intel.get("weaknesses_and_gaps", [])
        if weaknesses:
            weak_list = [w["weakness"] for w in weaknesses[:3]]
            parts.append(f"Key weaknesses: {', '.join(weak_list)}")

        # Sentiment
        sentiment = intel.get("customer_sentiment", {})
        if sentiment.get("top_complaints"):
            parts.append(f"Top complaints: {'; '.join(sentiment['top_complaints'][:2])}")

        # Positioning
        positioning = intel.get("market_positioning", "")
        if positioning:
            parts.append(f"Positioning: {positioning}")

        summaries.append("\n".join(parts))

    return "\n".join(summaries)[:6000]


def generate_strategic_synthesis(all_intelligence: dict, output_dir: str, brand_profile: dict = None) -> dict:
    """
    Step 1 of Component 2: Synthesize all competitor intelligence into a strategic brief.
    """
    if brand_profile is None:
        brand_profile = {"name": "KeenFox", "current_tagline": "Smart productivity", "target_audience": "SMBs", "current_strengths": [], "current_channels": []}

    print("\n[Campaign Integrator] Generating strategic synthesis...")

    intel_json = json.dumps(all_intelligence, indent=2)[:8000]

    prompt = STRATEGIC_SYNTHESIS_PROMPT.format(
        brand_name=brand_profile["name"],
        num_competitors=len(all_intelligence),
        keenfox_tagline=brand_profile["current_tagline"],
        target_audience=brand_profile["target_audience"],
        current_strengths=json.dumps(brand_profile["current_strengths"]),
        current_channels=json.dumps(brand_profile["current_channels"]),
        intel_data=intel_json,
    )

    response = _call_gemini(prompt)
    time.sleep(1)

    synthesis = _parse_json_response(response)
    synthesis["_meta"] = {
        "generated_at": datetime.now().isoformat(),
        "model": LLM_MODEL,
    }

    path = os.path.join(output_dir, "strategic_synthesis.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(synthesis, f, indent=2)
    print("  ✓ Strategic synthesis complete")

    return synthesis


def generate_campaign_recommendations(
    all_intelligence: dict,
    strategy_brief: dict,
    output_dir: str,
    brand_profile: dict = None,
) -> dict:
    """
    Step 2 of Component 2: Generate concrete campaign recommendations.
    """
    if brand_profile is None:
        brand_profile = {"name": "KeenFox", "current_tagline": "Smart productivity", "target_audience": "SMBs", "current_strengths": [], "current_channels": []}

    print("[Campaign Integrator] Generating campaign recommendations...")

    intel_summary = _summarize_intelligence(all_intelligence)
    strategy_json = json.dumps(strategy_brief, indent=2)[:3000]
    profile_json = json.dumps(brand_profile, indent=2)

    prompt = CAMPAIGN_RECOMMENDATIONS_PROMPT.format(
        brand_name=brand_profile["name"],
        keenfox_profile=profile_json,
        strategy_brief=strategy_json,
        intel_summary=intel_summary,
    )

    response = _call_gemini(prompt, max_tokens=4096)
    time.sleep(1)

    recommendations = _parse_json_response(response)
    recommendations["_meta"] = {
        "generated_at": datetime.now().isoformat(),
        "model": LLM_MODEL,
        "competitors_analyzed": list(all_intelligence.keys()),
    }

    path = os.path.join(output_dir, "campaign_recommendations.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(recommendations, f, indent=2)
    print("  ✓ Campaign recommendations generated")

    return recommendations


def run_campaign_integrator(
    all_intelligence: dict,
    output_dir: str,
    brand_profile: dict = None,
) -> dict:
    """
    Run the full campaign feedback loop.
    Returns combined output of synthesis + recommendations.
    """
    print("\n" + "="*60)
    print("COMPONENT 2: CAMPAIGN FEEDBACK LOOP INTEGRATOR")
    print("="*60)

    # Step 1: Strategic synthesis
    synthesis = generate_strategic_synthesis(all_intelligence, output_dir, brand_profile=brand_profile)

    # Step 2: Campaign recommendations
    recommendations = generate_campaign_recommendations(
        all_intelligence, synthesis, output_dir, brand_profile=brand_profile
    )

    combined = {
        "strategic_synthesis": synthesis,
        "campaign_recommendations": recommendations,
    }

    path = os.path.join(output_dir, "full_campaign_output.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    print("\n✓ Campaign integrator complete.")
    return combined


def answer_natural_language_query(query: str, all_intelligence: dict) -> str:
    """
    Bonus feature: Answer a natural language question about the competitive data.
    Example: "What are customers complaining about in Asana reviews this month?"
    """
    print(f"\n[NL Query] Processing: '{query}'")

    intel_json = json.dumps(all_intelligence, indent=2)[:8000]

    prompt = NATURAL_LANGUAGE_QUERY_PROMPT.format(
        intel_data=intel_json,
        user_query=query,
    )

    response = _call_gemini(prompt, max_tokens=1024)
    return response or "Could not generate an answer. Please check your API key."
