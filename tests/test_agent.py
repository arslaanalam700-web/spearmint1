"""
Unit and Integration Tests for AI Competitor Watch Agent.
"""

import unittest
from datetime import datetime
from src.models import (
    RawArticle,
    ProcessedUpdate,
    CategoryEnum,
    ImpactLevel,
    IntelligenceBrief
)
from src.deduplicator import UpdateDeduplicator
from src.categorizer import UpdateCategorizer
from src.synthesizer import BriefSynthesizer
from src.agent import CompetitorWatchAgent


class TestCompetitorWatchAgent(unittest.TestCase):

    def setUp(self):
        self.deduplicator = UpdateDeduplicator(similarity_threshold=0.45)
        self.categorizer = UpdateCategorizer()
        self.synthesizer = BriefSynthesizer()

    def test_noise_filtering(self):
        """Tests that stock spam, penny stock alerts, and irrelevant articles are filtered."""
        noise_article = RawArticle(
            title="Why Is OpenAI Stock Moving Today? Motley Fool Report",
            link="https://fool.com/example",
            source="Motley Fool",
            snippet="Short interest and options trading volume in penny stocks.",
            company="OpenAI"
        )
        self.assertTrue(self.deduplicator.is_noise(noise_article))

        unrelated_article = RawArticle(
            title="Best 10 Tech Gadgets of 2026 for Camping",
            link="https://gadgets.com/top10",
            source="Tech Reviews",
            snippet="Check out these batteries and flashlights for summer hiking.",
            company="Anthropic"
        )
        self.assertTrue(self.deduplicator.is_noise(unrelated_article))

        valid_article = RawArticle(
            title="Anthropic Launches Claude 3.5 Sonnet with State of the Art Coding",
            link="https://techcrunch.com/anthropic-claude",
            source="TechCrunch",
            snippet="Anthropic announces the release of Claude 3.5 Sonnet.",
            company="Anthropic"
        )
        self.assertFalse(self.deduplicator.is_noise(valid_article))

    def test_deduplication_and_clustering(self):
        """Tests clustering of syndicated/duplicate coverage into a single canonical event."""
        art1 = RawArticle(
            title="Anthropic Launches Claude 3.5 Sonnet Model",
            link="https://techcrunch.com/item1",
            source="TechCrunch",
            snippet="Anthropic releases new model.",
            company="Anthropic"
        )
        art2 = RawArticle(
            title="Anthropic Releases Claude 3.5 Sonnet With New Features",
            link="https://theverge.com/item2",
            source="The Verge",
            snippet="Anthropic announces Claude 3.5 Sonnet.",
            company="Anthropic"
        )
        art3 = RawArticle(
            title="Anthropic Unveils Next-Gen Claude 3.5 Sonnet",
            link="https://venturebeat.com/item3",
            source="VentureBeat",
            snippet="Anthropic's latest Claude 3.5 Sonnet benchmark results.",
            company="Anthropic"
        )
        art_diff = RawArticle(
            title="Anthropic Announces Major Enterprise Cloud Partnership with AWS",
            link="https://aws.amazon.com/blog/anthropic",
            source="AWS Blog",
            snippet="AWS expands strategic alliance with Anthropic.",
            company="Anthropic"
        )

        clusters = self.deduplicator.deduplicate_and_cluster([art1, art2, art3, art_diff])
        # Should have 2 clusters: Claude 3.5 Sonnet cluster and AWS Partnership cluster
        self.assertEqual(len(clusters), 2)
        
        # Check that the first cluster combined 3 articles
        sonnet_cluster = [c for c in clusters if "Claude 3.5 Sonnet" in c[0].title][0]
        self.assertEqual(len(sonnet_cluster[1]), 3)

    def test_categorization(self):
        """Tests accurate categorization across various business update types."""
        cases = [
            (
                "OpenAI announces o1 reasoning model with high benchmark performance",
                "Preview release of o1 reasoning capabilities and API endpoints.",
                CategoryEnum.PRODUCT_TECH
            ),
            (
                "Anthropic slashes token pricing by 50% for prompt caching on Claude 3.5",
                "New pricing tier and reduced per-million-tokens cost announced.",
                CategoryEnum.PRICING_PACKAGING
            ),
            (
                "Former Meta AI VP joins OpenAI as Head of Post-Training",
                "Key executive hire departs Meta to join rival lab.",
                CategoryEnum.HIRING_LEADERSHIP
            ),
            (
                "Cursor partners with Databricks to bring AI coding assistant to enterprise",
                "Multi-year collaboration and integration announced.",
                CategoryEnum.PARTNERSHIP_MA
            ),
            (
                "Perplexity AI raises $500M in Series C funding at $9B valuation",
                "Venture capital round led by prominent institutional investors.",
                CategoryEnum.FUNDING_FINANCIALS
            ),
            (
                "Authors sue Midjourney and OpenAI over copyright infringement in court",
                "Class-action lawsuit filed citing unauthorized training data.",
                CategoryEnum.LEGAL_REGULATORY
            ),
        ]

        for title, snippet, expected_cat in cases:
            cat, conf = self.categorizer._determine_category(title, snippet)
            self.assertEqual(cat, expected_cat, f"Failed for title: {title}. Got {cat}, expected {expected_cat}")

    def test_brief_synthesis(self):
        """Tests end-to-end synthesis of intelligence brief, threat matrix, markdown and HTML."""
        competitors = ["OpenAI", "Anthropic"]
        update1 = ProcessedUpdate(
            id="u1",
            company="OpenAI",
            title="OpenAI Releases o3-mini Reasoning Model",
            summary="New reasoning model optimized for math and coding.",
            why_it_matters="Direct challenge to competitive reasoning models.",
            category=CategoryEnum.PRODUCT_TECH,
            impact=ImpactLevel.HIGH,
            sentiment="Positive",
            primary_url="https://openai.com/blog/o3",
            source_names=["TechCrunch"]
        )
        update2 = ProcessedUpdate(
            id="u2",
            company="Anthropic",
            title="Anthropic Announces Price Reduction on Claude 3 Haiku",
            summary="Prompt caching discounts and cheaper batch API.",
            why_it_matters="Puts cost pressure on rival entry-level inference.",
            category=CategoryEnum.PRICING_PACKAGING,
            impact=ImpactLevel.MEDIUM,
            sentiment="Positive",
            primary_url="https://anthropic.com/pricing",
            source_names=["Anthropic News"]
        )

        brief = self.synthesizer.synthesize(
            competitors=competitors,
            all_updates=[update1, update2],
            time_window_days=14,
            raw_signals_count=20
        )

        self.assertEqual(len(brief.competitors_tracked), 2)
        self.assertEqual(brief.total_meaningful_updates, 2)
        self.assertIn("OpenAI", brief.threat_matrix)
        self.assertIn("Anthropic", brief.threat_matrix)
        self.assertEqual(brief.threat_matrix["OpenAI"][CategoryEnum.PRODUCT_TECH.value], 1)
        self.assertEqual(brief.threat_matrix["Anthropic"][CategoryEnum.PRICING_PACKAGING.value], 1)

        # Verify markdown export
        md = self.synthesizer.to_markdown(brief)
        self.assertIn("AI Competitor Intelligence Brief", md)
        self.assertIn("Competitive Activity Matrix", md)
        self.assertIn("OpenAI Releases o3-mini Reasoning Model", md)

        # Verify HTML export
        html = self.synthesizer.to_html(brief)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("OpenAI Releases o3-mini Reasoning Model", html)


if __name__ == "__main__":
    unittest.main()
