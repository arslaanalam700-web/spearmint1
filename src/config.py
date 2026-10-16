"""
Configuration and Taxonomies for the AI Competitor Watch Agent.
"""

from typing import Dict, List, Set

# Default Competitor presets for quick analysis
PRESET_COMPETITOR_GROUPS = {
    "Frontier AI Labs": [
        "OpenAI",
        "Anthropic",
        "Google DeepMind",
        "Mistral AI",
        "Meta AI",
        "xAI"
    ],
    "AI Code & Developer Assistants": [
        "Cursor",
        "GitHub Copilot",
        "Replit",
        "Cognition AI",
        "Tabnine",
        "Windsurf"
    ],
    "AI Search & Productivity": [
        "Perplexity AI",
        "Cohere",
        "Glean",
        "Notion AI",
        "You.com",
        "Harvey AI"
    ],
    "AI Cloud & Enterprise Infrastructure": [
        "Databricks",
        "Snowflake",
        "Scale AI",
        "Hugging Face",
        "Together AI",
        "Weights & Biases"
    ]
}

# Blocklist keywords indicating low-value stock spam or noise
NOISE_INDICATORS: Set[str] = {
    "motley fool", "zacks investment", "investorplace", "stock to buy", 
    "penny stock", "earnings call transcript", "why is stock moving",
    "short interest in", "insider selling", "etf holds", "target price raised",
    "options trading volume", "institutional investors buy", "zacks rank",
    "marketbeat", "stock alert", "technical analysis shows", "dow jones today"
}

# Categories and their defining keyword signals
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Product & Tech": [
        "launch", "launched", "release", "released", "unveil", "unveils", "unveiled",
        "announces", "announced", "feature", "features", "model", "models", "preview",
        "beta", "update", "updates", "llm", "context window", "benchmark", "benchmarks",
        "agent", "agents", "api", "multimodal", "sdk", "version", "v1.", "v2.", "v3.", "v4.", "v5.",
        "fine-tuning", "rag", "evals", "open source", "weights", "weights release",
        "deployment", "speedup", "latency", "breakthrough", "architecture", "tool use",
        "reasoning model", "workflow", "canvas"
    ],
    "Pricing & Packaging": [
        "pricing", "price", "prices", "discount", "tier", "tiers", "subscription",
        "plan", "plans", "token cost", "per million tokens", "free tier", "enterprise tier",
        "rate limit", "pay as you go", "cheaper", "cost cut", "price reduction",
        "billing", "credits", "seat pricing", "monetization", "fee", "free trial"
    ],
    "Hiring & Leadership": [
        "hire", "hired", "hires", "appoints", "appointed", "joined", "joins", "departs",
        "left", "leaves", "steps down", "stepped down", "resigned", "resigns", "chief executive",
        "ceo", "cto", "cpo", "coo", "vp", "vice president", "head of", "director",
        "researcher", "talent", "poached", "layoff", "layoffs", "restructuring",
        "co-founder", "founding member", "headcount", "executive"
    ],
    "Partnerships & M&A": [
        "partner", "partners", "partnership", "partnerships", "collaborates", "collaboration",
        "integrates", "integration", "integrations", "allies", "alliance", "deal", "deals",
        "acquired", "acquires", "acquisition", "merge", "merger", "agrees with",
        "reseller", "cloud agreement", "distribution", "powers", "teaming up",
        "joint venture", "syndication", "ecosystem partner"
    ],
    "Funding & Financials": [
        "funding", "fund", "funds", "fundraise", "fundraising", "raise", "raises", "raised",
        "round", "series a", "series b", "series c", "series d", "series e", "series f",
        "seed", "seed round", "valuation", "valued at", "venture capital", "investor",
        "investors", "arr", "annual recurring revenue", "revenue milestone", "profitable",
        "ipo", "public offering", "capital raise", "billion valuation"
    ],
    "Legal & Regulatory": [
        "sue", "sues", "sued", "lawsuit", "copyright", "infringement", "patent", "patents",
        "ftc", "sec", "regulatory", "regulation", "regulators", "scrutiny", "probe",
        "investigation", "antitrust", "subpoena", "compliance", "eu ai act",
        "licensing dispute", "court", "judge", "trademark", "settlement"
    ]
}

# High-impact indicators to detect game-changing moves
HIGH_IMPACT_KEYWORDS: Set[str] = {
    "flagship", "groundbreaking", "breakthrough", "acquires", "acquisition",
    "billion", "lawsuit", "superintelligence", "o1", "o3", "gpt-5", "claude 3.5",
    "claude 4", "gemini 2", "major update", "paradigm shift", "sweeps benchmarks",
    "state of the art", "sota", "ceo", "series b", "series c", "series d", "exclusive partnership"
}

# Positive vs Negative sentiment signals
SENTIMENT_KEYWORDS = {
    "positive": [
        "breakthrough", "surge", "growth", "outperform", "record", "triumph",
        "expanded", "wins", "leading", "efficient", "faster", "slashes price",
        "sota", "praised", "adoption", "thriving", "milestone"
    ],
    "negative": [
        "outage", "downtime", "lawsuit", "decline", "layoff", "departs", "criticism",
        "backlash", "vulnerability", "breach", "fail", "delay", "struggles",
        "probe", "loss", "controversy", "safety concern"
    ]
}
