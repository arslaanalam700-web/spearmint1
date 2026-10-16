"""
processing.py - Intelligent Processing Module
Implements date validation, relevance filtering, duplicate detection, category assignment,
priority classification, and potential business impact derivation.
"""

import re
import difflib
import hashlib
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field

from search import RawArticle


class CategoryEnum(str, Enum):
    PRODUCT_LAUNCHES = "Product Launches"
    PRICING = "Pricing"
    HIRING = "Hiring"
    PARTNERSHIPS = "Partnerships"
    FUNDING_ACQUISITIONS = "Funding and Acquisitions"
    MARKET_EXPANSION = "Market Expansion"
    TECH_AI_DEVELOPMENTS = "Technology or AI Developments"
    GENERAL_STRATEGY = "General / Strategy"

    @property
    def emoji(self) -> str:
        return ""


class PriorityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @property
    def color_code(self) -> str:
        colors = {
            PriorityLevel.CRITICAL: "#b91c1c",  # Dark Red
            PriorityLevel.HIGH: "#ea580c",      # Orange Red
            PriorityLevel.MEDIUM: "#d97706",    # Amber
            PriorityLevel.LOW: "#2563eb",       # Blue
        }
        return colors.get(self, "#6b7280")


class RetainedUpdate(BaseModel):
    """
    Every retained update strictly adheres to the evaluator schema.
    """
    id: str
    company: str
    headline: str
    category: CategoryEnum
    event_date: str                     # Clean formatted publication or event date
    source_url: str
    concise_summary: str
    priority_level: PriorityLevel
    potential_business_impact: str
    all_citations: List[str] = Field(default_factory=list)
    source_publishers: List[str] = Field(default_factory=list)
    is_sample_data: bool = False
    verification_status: str = "Verified"  # 'Verified' or 'Single Source'


# Indicator dictionary for noise and automated content farms
NOISE_BLOCKLIST: Set[str] = {
    "motley fool", "zacks", "investorplace", "stock to buy", "penny stock",
    "short interest in", "insider selling", "target price raised", "etf holds",
    "options trading volume", "marketbeat", "stock alert", "technical analysis shows",
    "why is stock moving", "earnings call transcript", "dow jones today"
}

# English stop words for title tokenization
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "up", "about", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "shall", "should", "may", "might", "must", "can",
    "could", "its", "it", "this", "that", "these", "those", "how", "what", "why",
    "who", "which", "when", "where", "new", "says", "announces", "announced"
}

# Multi-dimensional keyword taxonomy for the exact 7 categories
CATEGORY_TAXONOMY: Dict[CategoryEnum, List[str]] = {
    CategoryEnum.PRODUCT_LAUNCHES: [
        "launch", "launches", "launched", "release", "releases", "released",
        "unveil", "unveils", "unveiled", "introduces", "introduced", "announces new",
        "roll out", "rolls out", "general availability", "ga", "preview", "beta release",
        "v1.", "v2.", "v3.", "v4.", "v5.", "version", "canvas", "feature rollout"
    ],
    CategoryEnum.PRICING: [
        "pricing", "price", "prices", "discount", "discounts", "slashed", "slashes",
        "tier", "tiers", "subscription", "plan", "plans", "token cost", "per million tokens",
        "free tier", "enterprise tier", "pay as you go", "cheaper", "cost cut",
        "rate limit", "credits", "seat pricing", "billing", "monetization"
    ],
    CategoryEnum.HIRING: [
        "hire", "hired", "hires", "appoints", "appointed", "joined", "joins",
        "departs", "departed", "left", "leaves", "steps down", "resigned", "resigns",
        "ceo", "cto", "cpo", "coo", "chief executive", "vp", "vice president", "head of",
        "researcher", "talent", "poached", "layoff", "layoffs", "headcount", "co-founder"
    ],
    CategoryEnum.PARTNERSHIPS: [
        "partner", "partners", "partnership", "partnerships", "collaborates", "collaboration",
        "integrates with", "integration", "allies with", "alliance", "deal with", "agrees with",
        "teams up", "joint venture", "reseller agreement", "cloud agreement", "distribution deal"
    ],
    CategoryEnum.FUNDING_ACQUISITIONS: [
        "funding", "fundraise", "fundraising", "raise", "raises", "raised",
        "round", "series a", "series b", "series c", "series d", "series e",
        "seed round", "valuation", "valued at", "investor", "investors", "venture capital",
        "acquire", "acquires", "acquired", "acquisition", "acquisitions", "buyout", "merger",
        "ipo", "arr milestone", "revenue growth"
    ],
    CategoryEnum.MARKET_EXPANSION: [
        "expand", "expands", "expansion", "enters", "entering", "region", "europe", "asia",
        "japan", "india", "middle east", "global rollout", "sovereign ai", "datacenter",
        "data center", "localized", "government cloud", "new market", "opened office"
    ],
    CategoryEnum.TECH_AI_DEVELOPMENTS: [
        "model", "models", "reasoning model", "llm", "frontier model", "weights",
        "open weights", "benchmark", "benchmarks", "context window", "latency", "evals",
        "fine-tuning", "rag", "agent", "agents", "agentic", "inference speed",
        "multimodal", "architecture", "breakthrough", "synthetic data", "tool use"
    ]
}

# High-priority signals to escalate PriorityLevel
CRITICAL_PRIORITY_SIGNALS: Set[str] = {
    "flagship", "billion", "breakthrough", "acquisition", "acquires", "antitrust",
    "ceo steps down", "sweeps benchmarks", "o1", "o3", "claude 3.7", "gpt-5",
    "major security", "series c", "series d", "transformative"
}


class UpdateProcessor:
    """
    Cleans, validates, dedupes, categorizes, and prioritizes competitor news.
    """

    def __init__(self, similarity_threshold: float = 0.45):
        self.similarity_threshold = similarity_threshold

    def is_valid_date(self, dt: Optional[datetime], max_days: int) -> bool:
        """
        Validates date: must be non-null, not in future, and within max_days window.
        """
        if dt is None:
            return False
        now = datetime.now(timezone.utc)
        # Allow slight clock skew of 1 hour into future
        if dt > now + timedelta(hours=1):
            return False
        cutoff = now - timedelta(days=max_days)
        return dt >= cutoff

    def is_relevant_and_clean(self, article: RawArticle) -> bool:
        """
        Filters out noise, clickbait, and irrelevant articles.
        """
        text = f"{article.title.lower()} {article.snippet.lower()}"

        # 1. Blocklist check
        if any(bad in text for bad in NOISE_BLOCKLIST):
            return False

        # 2. Company relevance check:
        # Require company name (or primary tokens) in title or snippet
        comp_clean = re.sub(r'[^a-zA-Z0-9\s]', '', article.company.lower())
        tokens = [t for t in comp_clean.split() if len(t) > 2]
        has_mention = any(t in text for t in tokens)
        if not has_mention:
            return False

        # 3. Minimum length
        if len(article.title.strip()) < 12:
            return False

        return True

    def _tokenize(self, text: str) -> Set[str]:
        clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        return {w for w in clean.split() if w not in STOPWORDS and len(w) > 2}

    def compute_similarity(self, title_a: str, title_b: str) -> float:
        """
        Calculates hybrid similarity (Jaccard + SequenceMatcher) to detect duplicate coverage.
        """
        tokens_a = self._tokenize(title_a)
        tokens_b = self._tokenize(title_b)
        if not tokens_a or not tokens_b:
            return 0.0

        jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
        seq = difflib.SequenceMatcher(None, " ".join(sorted(tokens_a)), " ".join(sorted(tokens_b))).ratio()
        return 0.6 * jaccard + 0.4 * seq

    def deduplicate_articles(self, articles: List[RawArticle]) -> List[Tuple[RawArticle, List[RawArticle]]]:
        """
        Clusters articles covering the same announcement.
        Returns list of (canonical_article, clustered_articles).
        """
        valid = [a for a in articles if self.is_relevant_and_clean(a)]
        clusters: List[List[RawArticle]] = []

        for art in valid:
            matched = None
            for cluster in clusters:
                if self.compute_similarity(art.title, cluster[0].title) >= self.similarity_threshold:
                    matched = cluster
                    break
            if matched:
                matched.append(art)
            else:
                clusters.append([art])

        results: List[Tuple[RawArticle, List[RawArticle]]] = []
        for cluster in clusters:
            # Pick canonical article: prefer longer informative title and original domain
            canonical = max(cluster, key=lambda a: (len(a.title) + len(a.snippet)))
            results.append((canonical, cluster))

        return results

    def assign_category(self, title: str, snippet: str) -> CategoryEnum:
        """
        Categorizes updates into one of the 7 official business categories.
        """
        text = f"{title.lower()} {snippet.lower()}"
        scores = {cat: 0.0 for cat in CategoryEnum}

        for cat, keywords in CATEGORY_TAXONOMY.items():
            for kw in keywords:
                # Higher weight for headline matches
                if re.search(r'\b' + re.escape(kw) + r'\b', title.lower()):
                    scores[cat] += 2.5
                elif re.search(r'\b' + re.escape(kw) + r'\b', snippet.lower()):
                    scores[cat] += 1.0

        best = max(scores, key=scores.get)
        if scores[best] < 1.0:
            return CategoryEnum.GENERAL_STRATEGY
        return best

    def evaluate_priority(self, title: str, snippet: str, cluster_size: int, category: CategoryEnum) -> PriorityLevel:
        """
        Classifies priority based on industry magnitude, coverage consensus, and keyword signals.
        """
        text = f"{title.lower()} {snippet.lower()}"
        has_critical = any(sig in text for sig in CRITICAL_PRIORITY_SIGNALS)

        if has_critical or (cluster_size >= 4 and category in {CategoryEnum.PRODUCT_LAUNCHES, CategoryEnum.FUNDING_ACQUISITIONS}):
            return PriorityLevel.CRITICAL
        if cluster_size >= 2 or category in {CategoryEnum.PRODUCT_LAUNCHES, CategoryEnum.PRICING, CategoryEnum.HIRING}:
            return PriorityLevel.HIGH
        if cluster_size == 1 and len(snippet) > 80:
            return PriorityLevel.MEDIUM
        return PriorityLevel.LOW

    def derive_business_impact(self, category: CategoryEnum, priority: PriorityLevel, headline: str, company: str) -> str:
        """
        Generates potential business impact analysis strictly tied to competitive dynamics.
        """
        hl = headline.lower()

        if category == CategoryEnum.PRODUCT_LAUNCHES:
            if "reasoning" in hl or "model" in hl:
                return f"Shifts capability frontier; forces peer products to benchmark accuracy, latency, and reasoning depth."
            return f"Expands {company}'s core product surface area, heightening feature parity competition for developer workflows."

        elif category == CategoryEnum.PRICING:
            if "cut" in hl or "slashe" in hl or "free" in hl or "discount" in hl:
                return f"Inference cost commoditization; aggressively exerts margin pressure and attracts price-sensitive developers."
            return f"Represents changes to enterprise unit economics; signals monetization transition or usage tier restructuring."

        elif category == CategoryEnum.HIRING:
            if "left" in hl or "departs" in hl or "layoff" in hl:
                return f"Organizational realignment or leadership churn; may create talent poaching opportunities or project delays."
            return f"Strategic talent acquisition signaling intensified R&D focus in specialized AI and infrastructure verticals."

        elif category == CategoryEnum.PARTNERSHIPS:
            return f"Deepens enterprise distribution moats and integrates {company} deeper into enterprise cloud and GTM ecosystems."

        elif category == CategoryEnum.FUNDING_ACQUISITIONS:
            if "acquire" in hl:
                return f"Inorganic roadmap acceleration; absorbs competitive engineering talent and proprietary technology."
            return f"Substantially bolsters capital runway for expensive compute infrastructure and sustained GTM expansion."

        elif category == CategoryEnum.MARKET_EXPANSION:
            return f"Broadens global geographic presence and unlocks regional sovereign enterprise compliance accounts."

        elif category == CategoryEnum.TECH_AI_DEVELOPMENTS:
            return f"Advances fundamental AI infrastructure or developer tooling, raising the barrier to entry for smaller entrants."

        return f"Signals ongoing strategic execution and incremental market positioning by {company}."

    def process_and_retain(
        self,
        company: str,
        raw_articles: List[RawArticle],
        max_days: int = 14
    ) -> List[RetainedUpdate]:
        """
        Executes complete intelligent processing pipeline for a competitor's raw articles.
        """
        # Step 1: Date validation filter
        date_valid = [
            a for a in raw_articles
            if a.is_sample_data or self.is_valid_date(a.published_at, max_days)
        ]

        # Step 2: Deduplicate and consolidate articles covering the same announcement
        clusters = self.deduplicate_articles(date_valid)

        retained: List[RetainedUpdate] = []
        for canonical, cluster_members in clusters:
            title = canonical.title
            snippet = canonical.snippet or (cluster_members[1].snippet if len(cluster_members) > 1 else "")
            
            category = self.assign_category(title, snippet)
            priority = self.evaluate_priority(title, snippet, len(cluster_members), category)
            impact = self.derive_business_impact(category, priority, title, company)

            # Date formatting
            date_str = canonical.published_at.strftime("%b %d, %Y") if canonical.published_at else "Recent (Window)"

            # Citations and source publishers
            citations = list({a.link for a in cluster_members if a.link})
            publishers = list({a.source for a in cluster_members if a.source})

            # Verification status
            verification = "Verified (Multi-Source)" if len(publishers) > 1 else "Single Source"
            if canonical.is_sample_data:
                verification = "Demo Benchmark Data"

            # Unique deterministic ID
            uid = hashlib.md5(f"{company}:{title}:{date_str}".encode("utf-8")).hexdigest()[:10]

            summary = snippet if snippet else f"Verified announcement concerning {company}."

            retained.append(
                RetainedUpdate(
                    id=f"upd_{uid}",
                    company=company,
                    headline=title,
                    category=category,
                    event_date=date_str,
                    source_url=canonical.link,
                    concise_summary=summary,
                    priority_level=priority,
                    potential_business_impact=impact,
                    all_citations=citations,
                    source_publishers=publishers,
                    is_sample_data=canonical.is_sample_data,
                    verification_status=verification
                )
            )

        # Sort retained updates: Critical first, then High, Medium, Low
        priority_rank = {
            PriorityLevel.CRITICAL: 0,
            PriorityLevel.HIGH: 1,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 3
        }
        retained.sort(key=lambda u: priority_rank[u.priority_level])
        return retained
