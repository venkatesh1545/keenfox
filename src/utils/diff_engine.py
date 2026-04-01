# src/utils/diff_engine.py
# Bonus: Detects what changed between the current and previous report run.
# Compares JSON snapshots and highlights new signals vs previous report.

import os
import json
from datetime import datetime
from google import genai

from src.prompts.prompt_templates import DIFF_ANALYSIS_PROMPT
from src.config import LLM_MODEL


def find_previous_report(reports_dir: str) -> tuple[str, dict] | tuple[None, None]:
    """
    Find the most recent previous report in the reports directory.
    Returns (date_string, data_dict) or (None, None) if no previous report.
    """
    try:
        files = [f for f in os.listdir(reports_dir) if f.startswith("report_") and f.endswith(".json")]
        if len(files) < 2:
            return None, None

        files.sort(reverse=True)
        previous_file = files[1]  # Second most recent

        with open(os.path.join(reports_dir, previous_file)) as f:
            data = json.load(f)

        date_str = previous_file.replace("report_", "").replace(".json", "")
        return date_str, data

    except Exception as e:
        print(f"[Diff] Could not load previous report: {e}")
        return None, None


def save_current_report(reports_dir: str, all_intelligence: dict, campaign_output: dict) -> str:
    """Save current run's data as a timestamped report."""
    os.makedirs(reports_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.json"

    report = {
        "generated_at": datetime.now().isoformat(),
        "intelligence": all_intelligence,
        "campaign_output": campaign_output,
    }

    path = os.path.join(reports_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[Diff] Current report saved: {filename}")
    return timestamp


def generate_diff_report(
    current_intelligence: dict,
    previous_intelligence: dict,
    previous_date: str,
    current_date: str,
) -> dict:
    """
    Use Claude to identify meaningful changes between two intelligence snapshots.
    """
    print("[Diff] Generating diff analysis...")

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        prompt = DIFF_ANALYSIS_PROMPT.format(
            previous_date=previous_date,
            previous_data=json.dumps(previous_intelligence, indent=2)[:4000],
            current_date=current_date,
            current_data=json.dumps(current_intelligence, indent=2)[:4000],
        )

        response_obj = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=2048,
            ),
        )

        response = response_obj.text

        try:
            diff = json.loads(response)
        except Exception:
            import re
            match = re.search(r"\{[\s\S]*\}", response)
            diff = json.loads(match.group()) if match else {"raw": response}

        diff["compared_dates"] = {
            "previous": previous_date,
            "current": current_date,
        }
        return diff

    except Exception as e:
        print(f"[Diff] Error generating diff: {e}")
        return {"error": str(e)}


def run_diff_engine(
    current_intelligence: dict,
    campaign_output: dict,
    reports_dir: str,
) -> dict | None:
    """
    Main entry point for diff engine.
    Saves current report and generates diff if a previous report exists.
    """
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Save current
    save_current_report(reports_dir, current_intelligence, campaign_output)

    # Try to find previous
    previous_date, previous_data = find_previous_report(reports_dir)
    if not previous_data:
        print("[Diff] No previous report found — skipping diff analysis.")
        print("       Run the system again tomorrow to see what changed!")
        return None

    previous_intelligence = previous_data.get("intelligence", {})

    diff = generate_diff_report(
        current_intelligence,
        previous_intelligence,
        previous_date,
        current_date,
    )

    print(f"[Diff] ✓ Diff analysis complete vs report from {previous_date}")
    return diff
