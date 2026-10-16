"""
AI Competitor Watch Agent Package
"""

from src.models import (
    CategoryEnum,
    ImpactLevel,
    RawArticle,
    ProcessedUpdate,
    CompetitorReport,
    IntelligenceBrief,
)
from src.collector import CompetitorDataCollector
from src.deduplicator import UpdateDeduplicator
from src.categorizer import UpdateCategorizer
from src.synthesizer import BriefSynthesizer
from src.agent import CompetitorWatchAgent
from src.config import PRESET_COMPETITOR_GROUPS

__all__ = [
    "CompetitorWatchAgent",
    "CompetitorDataCollector",
    "UpdateDeduplicator",
    "UpdateCategorizer",
    "BriefSynthesizer",
    "CategoryEnum",
    "ImpactLevel",
    "RawArticle",
    "ProcessedUpdate",
    "CompetitorReport",
    "IntelligenceBrief",
    "PRESET_COMPETITOR_GROUPS",
]
