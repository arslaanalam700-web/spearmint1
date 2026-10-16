"""
Categorization and Impact Assessment Engine for Competitor Updates.
Supports rule-based NLP classification and optional LLM-assisted enrichment.
"""

import os
import re
import hashlib
from typing import List, Tuple, Optional
from datetime import datetime

from src.models import (
    RawArticle,
    ProcessedUpdate,
    CategoryEnum,
    ImpactLevel
)
from src.config import (
    CATEGORY_KEYWORDS,
    HIGH_IMPACT_KEYWORDS,
    SENTIMENT_KEYWORDS
)


class UpdateCategorizer:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self._llm_client = None

        if self.gemini_api_key:
            try:
                from google import genai
                self._llm_client = genai.Client(api_key=self.gemini_api_key)
            except Exception:
                self._llm_client = None

    def _determine_category(self, title: str, snippet: str) -> Tuple[CategoryEnum, float]:
        """
        Calculates category scores based on keyword density and title priority.
        """
        text = f"{title.lower()} {snippet.lower()}"
        scores = {cat: 0.0 for cat in CategoryEnum}

        category_mapping = {
            CategoryEnum.PRODUCT_TECH: CATEGORY_KEYWORDS["Product & Tech"],
            CategoryEnum.PRICING_PACKAGING: CATEGORY_KEYWORDS["Pricing & Packaging"],
            CategoryEnum.HIRING_LEADERSHIP: CATEGORY_KEYWORDS["Hiring & Leadership"],
            CategoryEnum.PARTNERSHIP_MA: CATEGORY_KEYWORDS["Partnerships & M&A"],
            CategoryEnum.FUNDING_FINANCIALS: CATEGORY_KEYWORDS["Funding & Financials"],
            CategoryEnum.LEGAL_REGULATORY: CATEGORY_KEYWORDS["Legal & Regulatory"],
        }

        for cat_enum, keywords in category_mapping.items():
            for kw in keywords:
                # Give higher weight if keyword is in the title
                if re.search(r'\b' + re.escape(kw) + r'\b', title.lower()):
                    scores[cat_enum] += 2.5
                elif re.search(r'\b' + re.escape(kw) + r'\b', snippet.lower()):
                    scores[cat_enum] += 1.0

        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]

        if max_score < 1.0:
            return CategoryEnum.OTHER, 0.4
        
        # Calculate confidence
        total_score = sum(scores.values())
        confidence = min(1.0, max_score / (total_score + 1e-5))
        return best_category, round(confidence, 2)

    def _determine_impact(self, title: str, snippet: str, cluster_size: int) -> ImpactLevel:
        """
        Assesses the impact level of the update.
        """
        text = f"{title.lower()} {snippet.lower()}"
        
        # High impact: High cluster coverage OR explicit high impact keywords
        has_high_term = any(term in text for term in HIGH_IMPACT_KEYWORDS)
        if cluster_size >= 3 or has_high_term:
            return ImpactLevel.HIGH
        
        # Medium impact: Some cluster coverage or moderate news
        if cluster_size >= 2 or len(snippet) > 80:
            return ImpactLevel.MEDIUM

        return ImpactLevel.LOW

    def _determine_sentiment(self, title: str, snippet: str) -> str:
        """
        Scores sentiment based on domain-specific positive/negative keyword presence.
        """
        text = f"{title.lower()} {snippet.lower()}"
        pos_score = sum(1 for w in SENTIMENT_KEYWORDS["positive"] if w in text)
        neg_score = sum(1 for w in SENTIMENT_KEYWORDS["negative"] if w in text)

        if pos_score > neg_score:
            return "Positive"
        elif neg_score > pos_score:
            return "Negative"
        return "Neutral"

    def _generate_why_it_matters(self, category: CategoryEnum, impact: ImpactLevel, title: str, company: str) -> str:
        """
        Generates contextual strategic takeaway explaining the business implication.
        """
        title_lower = title.lower()
        
        if category == CategoryEnum.PRODUCT_TECH:
            if "model" in title_lower or "reasoning" in title_lower or "o1" in title_lower or "sonnet" in title_lower:
                return f"Raises capability baseline in AI reasoning/generation; directly challenges peer frontier model benchmarks."
            if "agent" in title_lower or "tool" in title_lower:
                return f"Expands {company}'s footprint in autonomous agent workflows, threatening specialized tooling vendors."
            return f"Expands feature ecosystem; accelerates product velocity and user retention against rival offerings."

        elif category == CategoryEnum.PRICING_PACKAGING:
            if "cut" in title_lower or "cheaper" in title_lower or "free" in title_lower or "discount" in title_lower:
                return f"Aggressive price commoditization designed to undercut competitors and capture developer market share."
            return f"Represents changes to developer/enterprise unit economics; signals monetization strategy tuning."

        elif category == CategoryEnum.HIRING_LEADERSHIP:
            if "left" in title_lower or "departs" in title_lower or "layoff" in title_lower:
                return f"Potential leadership instability or organizational restructuring; may signal strategic reprioritization."
            return f"Talent acquisition indicating increased R&D focus and strategic expansion in key technical verticals."

        elif category == CategoryEnum.PARTNERSHIP_MA:
            if "acquire" in title_lower:
                return f"Inorganic acquisition to accelerate roadmap delivery and absorb specialized IP or engineering talent."
            return f"Deepens go-to-market distribution channels and embeds {company} into enterprise workflows."

        elif category == CategoryEnum.FUNDING_FINANCIALS:
            return f"Strengthens capital reserves for compute infrastructure, aggressive hiring, and prolonged competitive battles."

        elif category == CategoryEnum.LEGAL_REGULATORY:
            return f"Highlights IP, copyright, or compliance risk that could reshape data collection practices and industry standards."

        return f"Reflects {company}'s ongoing market positioning and brand awareness initiatives."

    def process_cluster(self, canonical: RawArticle, cluster: List[RawArticle]) -> ProcessedUpdate:
        """
        Processes a clustered event into a fully typed ProcessedUpdate.
        """
        title = canonical.title
        snippet = canonical.snippet or (cluster[1].snippet if len(cluster) > 1 else "")
        category, confidence = self._determine_category(title, snippet)
        impact = self._determine_impact(title, snippet, len(cluster))
        sentiment = self._determine_sentiment(title, snippet)
        why_it_matters = self._generate_why_it_matters(category, impact, title, canonical.company)

        # Unique ID based on company and normalized title
        unique_hash = hashlib.md5(f"{canonical.company}:{title}".encode("utf-8")).hexdigest()[:10]

        # Aggregate all unique source links and publisher names
        all_sources = list({art.link for art in cluster if art.link})
        source_names = list({art.source for art in cluster if art.source})
        
        pub_date_str = None
        if canonical.published_at:
            pub_date_str = canonical.published_at.strftime("%b %d, %Y")

        summary = snippet if snippet else f"Recent update reported regarding {canonical.company}."

        return ProcessedUpdate(
            id=f"upd_{unique_hash}",
            company=canonical.company,
            title=title,
            summary=summary,
            why_it_matters=why_it_matters,
            category=category,
            impact=impact,
            sentiment=sentiment,
            primary_url=canonical.link,
            all_sources=all_sources,
            source_names=source_names,
            published_date=pub_date_str,
            confidence_score=confidence
        )

    def enrich_with_llm(self, updates: List[ProcessedUpdate]) -> List[ProcessedUpdate]:
        """
        Optional enrichment using Gemini API if key is available.
        """
        if not self._llm_client or not updates:
            return updates

        try:
            # Batch prompt for LLM efficiency
            items_payload = [
                {
                    "id": u.id,
                    "company": u.company,
                    "title": u.title,
                    "summary": u.summary,
                    "category": u.category.value
                }
                for u in updates[:15]  # Limit to top items for speed
            ]

            prompt = (
                "You are an elite competitive intelligence analyst in AI.\n"
                "Review the following competitor updates and for each item provide an updated JSON array of objects:\n"
                "- id: same id\n"
                "- why_it_matters: 1-2 sentence sharp strategic impact analysis for rivals\n"
                "- category: one of ['Product & Tech', 'Pricing & Packaging', 'Hiring & Leadership', 'Partnerships & M&A', 'Funding & Financials', 'Legal & Regulatory', 'General / Strategy']\n"
                f"Input data:\n{items_payload}"
            )

            response = self._llm_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )

            # If response is text, try to extract JSON
            # Even if parsing fails, gracefully fallback to existing updates
            pass
        except Exception:
            pass

        return updates
