# src/utils/report_generator.py
# Converts structured JSON outputs into a beautiful, readable Markdown report.

import json
import os
from datetime import datetime


def _section(title: str, emoji: str = "") -> str:
    prefix = f"{emoji} " if emoji else ""
    return f"\n## {prefix}{title}\n"


def _subsection(title: str) -> str:
    return f"\n### {title}\n"


def generate_intelligence_section(all_intelligence: dict, brand_name: str = "KeenFox") -> str:
    """Generate the competitive intelligence section of the report."""
    lines = [_section("Competitive Intelligence Breakdown", "🔍")]

    for key, intel in all_intelligence.items():
        comp_name = intel.get("competitor", key)
        lines.append(f"\n---\n### 🏢 {comp_name}\n")

        # Market positioning
        positioning = intel.get("market_positioning", "")
        if positioning:
            lines.append(f"**Positioning:** {positioning}\n")

        # Feature launches
        features = intel.get("feature_launches", [])
        if features:
            lines.append("**Recent Feature Launches:**")
            for f in features[:4]:
                urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    f.get("urgency", "low"), "⚪"
                )
                lines.append(
                    f"- {urgency_emoji} **{f.get('feature', 'Unknown')}**: "
                    f"{f.get('description', '')} "
                    f"*(Strategic implication: {f.get('strategic_implication', 'N/A')})*"
                )
            lines.append("")

        # Customer sentiment
        sentiment = intel.get("customer_sentiment", {})
        if sentiment:
            praises = sentiment.get("top_praises", [])
            complaints = sentiment.get("top_complaints", [])

            if praises:
                lines.append("**What customers love ✅:**")
                for p in praises[:3]:
                    lines.append(f"- {p}")
                lines.append("")

            if complaints:
                lines.append(f"**What customers hate ❌ (= {brand_name} opportunities):**")
                for c in complaints[:3]:
                    lines.append(f"- {c}")
                lines.append("")

        # Pricing signals
        pricing = intel.get("pricing_signals", {})
        if pricing:
            lines.append(
                f"**Pricing:** {pricing.get('model', 'Unknown')} | "
                f"Entry: {pricing.get('entry_price', 'N/A')} | "
                f"Perception: {pricing.get('perceived_value', 'N/A')}"
            )
            if pricing.get("recent_changes"):
                lines.append(f"⚠️ **Pricing change:** {pricing['recent_changes']}")
            lines.append("")

        # Weaknesses & gaps
        weaknesses = intel.get("weaknesses_and_gaps", [])
        if weaknesses:
            lines.append(f"**Weaknesses & {brand_name} Opportunities:**")
            for w in weaknesses[:3]:
                lines.append(
                    f"- **Weakness:** {w.get('weakness', '')} → "
                    f"**{brand_name} can:** {w.get('brand_opportunity', w.get('keenfox_opportunity', ''))}"
                )
            lines.append("")

    return "\n".join(lines)


def generate_synthesis_section(synthesis: dict) -> str:
    """Generate the strategic synthesis section."""
    lines = [_section("Market Strategic Analysis", "🧠")]

    snapshot = synthesis.get("market_snapshot", {})
    if snapshot:
        lines.append(f"🔴 **Biggest Threat:** {snapshot.get('biggest_threat', 'N/A')}\n")
        lines.append(f"💡 **Biggest Opportunity:** {snapshot.get('biggest_opportunity', 'N/A')}\n")
        lines.append(f"⚡ **Market Whitespace:** {snapshot.get('whitespace', 'N/A')}\n")
        lines.append(f"📈 **Market Trend:** {snapshot.get('trend', 'N/A')}\n")

    vulnerabilities = synthesis.get("competitor_vulnerabilities", [])
    if vulnerabilities:
        lines.append(_subsection("Competitor Vulnerabilities to Exploit"))
        for v in vulnerabilities:
            time_emoji = {"urgent": "🔴", "moderate": "🟡", "long-term": "🟢"}.get(
                v.get("time_sensitivity", "moderate"), "⚪"
            )
            lines.append(
                f"- {time_emoji} **{v.get('competitor', '')}**: {v.get('vulnerability', '')} "
                f"→ *Action: {v.get('how_to_exploit', '')}*"
            )
        lines.append("")

    positioning_rec = synthesis.get("positioning_recommendation", synthesis.get("keenfox_positioning_recommendation", {}))
    if positioning_rec:
        lines.append(_subsection("Recommended Positioning"))
        lines.append(f"**Recommended Angle:** {positioning_rec.get('recommended_primary_angle', '')}\n")
        lines.append(f"**Rationale:** {positioning_rec.get('rationale', '')}\n")
        proof_points = positioning_rec.get("proof_points_needed", [])
        if proof_points:
            lines.append("**Proof Points KeenFox Needs:**")
            for p in proof_points:
                lines.append(f"- {p}")
        lines.append("")

    return "\n".join(lines)


def generate_campaign_section(recommendations: dict) -> str:
    """Generate the campaign recommendations section."""
    lines = [_section("Campaign Recommendations", "📢")]

    # Messaging
    messaging = recommendations.get("messaging_and_positioning", {})
    if messaging:
        lines.append(_subsection("Messaging & Copy Suggestions"))
        lines.append(f"**Current Weakness:** {messaging.get('current_weakness', '')}\n")
        lines.append(f"**Recommended Homepage Headline:**")
        lines.append(f"> {messaging.get('recommended_headline', '')}\n")
        lines.append(f"**Rationale:** {messaging.get('headline_rationale', '')}\n")
        lines.append(f"**Cold Email Subject:** `{messaging.get('cold_email_subject', '')}`")
        opening = messaging.get("cold_email_opening", "")
        if opening:
            lines.append(f"**Cold Email Opening:**\n> {opening}\n")
        lines.append(f"**LinkedIn Ad Copy:** `{messaging.get('linkedin_ad_copy', '')}`\n")
        lines.append(
            f"**Positioning Statement:** _{messaging.get('positioning_statement', '')}_\n"
        )

    # Channel Strategy
    channel = recommendations.get("channel_strategy", {})
    if channel:
        lines.append(_subsection("Channel Strategy"))

        double_down = channel.get("double_down", [])
        if double_down:
            lines.append("**✅ Double Down On:**")
            for c in double_down:
                lines.append(
                    f"- **{c.get('channel', '')}**: {c.get('reason', '')} "
                    f"→ *Tactic: {c.get('specific_tactic', '')}*"
                )
            lines.append("")

        pull_back = channel.get("pull_back", [])
        if pull_back:
            lines.append("**🛑 Pull Back From:**")
            for c in pull_back:
                lines.append(f"- **{c.get('channel', '')}**: {c.get('reason', '')}")
            lines.append("")

        new_channels = channel.get("new_channels_to_test", [])
        if new_channels:
            lines.append("**🧪 New Channels to Test:**")
            for c in new_channels:
                lines.append(
                    f"- **{c.get('channel', '')}**: {c.get('reason', '')} "
                    f"→ *First experiment: {c.get('first_experiment', '')}*"
                )
            lines.append("")

    # GTM Recommendations
    gtm = recommendations.get("gtm_strategic_recommendations", [])
    if gtm:
        lines.append(_subsection("Top GTM Strategic Recommendations"))
        for rec in gtm:
            priority = rec.get("priority", "?")
            timeline_emoji = {
                "immediate": "🔴",
                "30-days": "🟡",
                "90-days": "🟢",
            }.get(rec.get("timeline", ""), "⚪")

            lines.append(
                f"**#{priority} {timeline_emoji} {rec.get('recommendation', '')}**"
            )
            lines.append(f"- *Why:* {rec.get('rationale', '')}")
            lines.append(f"- *Data backing:* {rec.get('competitive_data_backing', '')}")
            lines.append(f"- *KPI:* {rec.get('kpi', '')}")
            lines.append(f"- *Timeline:* {rec.get('timeline', '')}")
            lines.append("")

    return "\n".join(lines)


def generate_diff_section(diff: dict | None) -> str:
    """Generate the diff section if diff data is available."""
    if not diff:
        return ""

    lines = [_section("What Changed Since Last Run", "🔄")]

    dates = diff.get("compared_dates", {})
    if dates:
        lines.append(
            f"*Comparing: {dates.get('previous', '?')} → {dates.get('current', '?')}*\n"
        )

    summary = diff.get("executive_summary_of_changes", "")
    if summary:
        lines.append(f"**Summary:** {summary}\n")

    new_signals = diff.get("new_signals", [])
    if new_signals:
        lines.append("**🆕 New Signals:**")
        for s in new_signals:
            urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                s.get("urgency", "low"), "⚪"
            )
            lines.append(
                f"- {urgency_emoji} **{s.get('competitor', '')}**: {s.get('signal', '')} "
                f"*(Importance: {s.get('strategic_importance', '')})*"
            )
        lines.append("")

    disappeared = diff.get("disappeared_signals", [])
    if disappeared:
        lines.append("**🗑️ Disappeared Signals:**")
        for s in disappeared:
            lines.append(
                f"- **{s.get('competitor', '')}**: {s.get('signal', '')} "
                f"→ {s.get('interpretation', '')}"
            )
        lines.append("")

    return "\n".join(lines)


def generate_full_report(
    all_intelligence: dict,
    campaign_output: dict,
    diff_data: dict | None,
    output_path: str,
    brand_name: str = "KeenFox",
) -> str:
    """
    Generate the complete markdown report and save to output_path.
    Returns the report text.
    """
    now = datetime.now()

    header = f"""# {brand_name} Competitive Intelligence Report
**Generated:** {now.strftime("%B %d, %Y at %H:%M")}  
**Brand Analyzed:** {brand_name}  
**Competitors Analyzed:** {", ".join([v.get("competitor", k) for k, v in all_intelligence.items()])}  
**Status:** Fresh data — ready to act on

---

> ⚡ **This report is AI-generated from live competitor data.**  
> Every recommendation is grounded in specific competitive signals.  
> Don't just read it — act on it.

---
"""

    synthesis = campaign_output.get("strategic_synthesis", {})
    recommendations = campaign_output.get("campaign_recommendations", {})

    sections = [
        header,
        generate_intelligence_section(all_intelligence, brand_name=brand_name),
        generate_synthesis_section(synthesis),
        generate_campaign_section(recommendations),
        generate_diff_section(diff_data),
    ]

    footer = f"""
---
*Report generated by KeenFox Competitive Intelligence System*  
*Brand: {brand_name} | Model: Gemini | Run at: {now.isoformat()}*  
*To refresh: `python main.py --brand "{brand_name}"` | To query: `python main.py --brand "{brand_name}" --query "your question"`*
"""
    sections.append(footer)

    report = "\n".join(sections)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Full report saved to: {output_path}")
    return report
