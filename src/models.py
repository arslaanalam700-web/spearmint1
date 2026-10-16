"""
Data models for the AI Competitor Watch Agent.
"""

from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    PRODUCT_TECH = "Product & Tech"
    PRICING_PACKAGING = "Pricing & Packaging"
    HIRING_LEADERSHIP = "Hiring & Leadership"
    PARTNERSHIP_MA = "Partnerships & M&A"
    FUNDING_FINANCIALS = "Funding & Financials"
    LEGAL_REGULATORY = "Legal & Regulatory"
    OTHER = "General / Strategy"

    @property
    def emoji(self) -> str:
        emojis = {
            CategoryEnum.PRODUCT_TECH: "🚀",
            CategoryEnum.PRICING_PACKAGING: "💰",
            CategoryEnum.HIRING_LEADERSHIP: "👥",
            CategoryEnum.PARTNERSHIP_MA: "🤝",
            CategoryEnum.FUNDING_FINANCIALS: "📈",
            CategoryEnum.LEGAL_REGULATORY: "⚖️",
            CategoryEnum.OTHER: "📰",
        }
        return emojis.get(self, "📌")


class ImpactLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @property
    def badge_color(self) -> str:
        colors = {
            ImpactLevel.HIGH: "#dc2626",      # red
            ImpactLevel.MEDIUM: "#d97706",    # amber
            ImpactLevel.LOW: "#2563eb",       # blue
        }
        return colors.get(self, "#6b7280")


class RawArticle(BaseModel):
    title: str
    link: str
    source: str
    published_at: Optional[datetime] = None
    snippet: str = ""
    company: str
    raw_text: Optional[str] = None


class ProcessedUpdate(BaseModel):
    id: str
    company: str
    title: str
    summary: str
    why_it_matters: str = ""
    category: CategoryEnum = CategoryEnum.OTHER
    impact: ImpactLevel = ImpactLevel.MEDIUM
    sentiment: str = "Neutral"  # Positive, Neutral, Negative
    primary_url: str
    all_sources: List[str] = Field(default_factory=list)
    source_names: List[str] = Field(default_factory=list)
    published_date: Optional[str] = None
    confidence_score: float = 1.0


class CompetitorReport(BaseModel):
    company: str
    total_updates: int = 0
    updates_by_category: Dict[str, int] = Field(default_factory=dict)
    updates: List[ProcessedUpdate] = Field(default_factory=list)
    key_highlights: List[str] = Field(default_factory=list)
    sentiment_breakdown: Dict[str, int] = Field(default_factory=dict)


class IntelligenceBrief(BaseModel):
    title: str = "AI Competitor Intelligence Brief"
    generated_at: datetime = Field(default_factory=datetime.now)
    competitors_tracked: List[str] = Field(default_factory=list)
    time_window_days: int = 14
    total_signals_analyzed: int = 0
    total_meaningful_updates: int = 0
    executive_summary: str = ""
    macro_trends: List[str] = Field(default_factory=list)
    competitor_reports: Dict[str, CompetitorReport] = Field(default_factory=dict)
    threat_matrix: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    actionable_recommendations: List[str] = Field(default_factory=list)
    all_updates: List[ProcessedUpdate] = Field(default_factory=list)
