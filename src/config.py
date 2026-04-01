# src/config.py
# Central configuration for all competitors and data sources

COMPETITORS = {
    "notion": {
        "name": "Notion",
        "website": "https://www.notion.so",
        "pricing_url": "https://www.notion.so/pricing",
        "g2_url": "https://www.g2.com/products/notion/reviews",
        "reddit_keywords": ["notion app", "notion.so", "notion productivity"],
        "category": "All-in-one workspace",
    },
    "asana": {
        "name": "Asana",
        "website": "https://asana.com",
        "pricing_url": "https://asana.com/pricing",
        "g2_url": "https://www.g2.com/products/asana/reviews",
        "reddit_keywords": ["asana project management", "asana app", "asana tasks"],
        "category": "Project Management",
    },
    "clickup": {
        "name": "ClickUp",
        "website": "https://clickup.com",
        "pricing_url": "https://clickup.com/pricing",
        "g2_url": "https://www.g2.com/products/clickup/reviews",
        "reddit_keywords": ["clickup", "clickup app", "clickup review"],
        "category": "Project Management",
    },
    "monday": {
        "name": "Monday.com",
        "website": "https://monday.com",
        "pricing_url": "https://monday.com/pricing",
        "g2_url": "https://www.g2.com/products/monday-com/reviews",
        "reddit_keywords": ["monday.com", "monday crm", "monday project"],
        "category": "Work OS",
    },
    "microsoft365": {
        "name": "Microsoft 365 Copilot",
        "website": "https://www.microsoft.com/en-us/microsoft-365",
        "pricing_url": "https://www.microsoft.com/en-us/microsoft-365/business/compare-all-plans",
        "g2_url": "https://www.g2.com/products/microsoft-365/reviews",
        "reddit_keywords": ["microsoft 365 copilot", "m365 copilot", "office 365 copilot"],
        "category": "AI Productivity Suite",
    },
}

# KeenFox's current positioning (used for gap analysis)
KEENFOX_PROFILE = {
    "name": "KeenFox",
    "category": "B2B SaaS Productivity",
    "current_tagline": "Smart productivity for modern teams",
    "current_channels": ["LinkedIn", "Google Ads", "Content Marketing", "Email"],
    "current_strengths": ["Ease of use", "Integrations", "Customer support"],
    "target_audience": "SMB and mid-market teams (10-500 employees)",
    "pricing_model": "Per-seat SaaS subscription",
}

# Data freshness: how many hours before re-fetching
CACHE_TTL_HOURS = 12

# LLM settings
LLM_MODEL = "gemini-2.5-flash"
LLM_MAX_TOKENS = 4096
