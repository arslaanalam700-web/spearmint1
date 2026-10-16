"""
test_pipeline.py - Comprehensive Unit and Reliability Tests
Tests:
- Input validation (5-10 competitors, duplicate handling)
- Date filtering (7, 14, 30 days cutoff, future date protection)
- Relevance and noise filtering (suppressing stock spam and off-target mentions)
- Duplicate detection & consolidation across multiple publications
- Category assignment across all 7 required business categories
- Priority classification and business impact derivation
- Missing sources & empty search results (monitoring gaps)
- Explicitly labeled sample data mode
- CSV and PDF export generation
"""

import unittest
from datetime import datetime, timezone, timedelta
from search import RawArticle, SearchEngine
from processing import (
    UpdateProcessor,
    RetainedUpdate,
    CategoryEnum,
    PriorityLevel
)
from reporting import ReportGenerator, IntelligenceReport
from agent import CompetitorWatchAgent


class TestCompetitorWatchAgentPipeline(unittest.TestCase):

    def setUp(self):
        self.agent = CompetitorWatchAgent()
        self.processor = UpdateProcessor()
        self.reporter = ReportGenerator()

    # 1. Input Validation Tests
    def test_input_validation_enforces_5_to_10_competitors(self):
        # Case: < 5 competitors
        valid, msg, _ = CompetitorWatchAgent.validate_inputs(["OpenAI", "Anthropic", "Cursor"], 14)
        self.assertFalse(valid)
        self.assertIn("at least 5 competitors", msg)

        # Case: > 10 competitors
        too_many = [f"Company_{i}" for i in range(12)]
        valid, msg, _ = CompetitorWatchAgent.validate_inputs(too_many, 14)
        self.assertFalse(valid)
        self.assertIn("at most 10 competitors", msg)

        # Case: Duplicate entries should be consolidated
        with_dupes = ["OpenAI", "Anthropic", "openai", "Cursor", "Perplexity", "Mistral AI", "ANTHROPIC"]
        valid, msg, cleaned = CompetitorWatchAgent.validate_inputs(with_dupes, 14)
        self.assertTrue(valid)
        self.assertEqual(len(cleaned), 5)
        self.assertIn("OpenAI", cleaned)
        self.assertIn("Anthropic", cleaned)

    def test_monitoring_period_validation(self):
        # Valid periods
        for d in [7, 14, 30]:
            valid, _, _ = CompetitorWatchAgent.validate_inputs(["OpenAI", "Anthropic", "Cursor", "Perplexity", "Mistral"], d)
            self.assertTrue(valid)

        # Invalid periods
        for invalid_d in [1, 5, 10, 45, 60]:
            valid, msg, _ = CompetitorWatchAgent.validate_inputs(["OpenAI", "Anthropic", "Cursor", "Perplexity", "Mistral"], invalid_d)
            self.assertFalse(valid)
            self.assertIn("Must be one of 7, 14, or 30 days", msg)

    # 2. Date Filtering Tests
    def test_date_filtering(self):
        now = datetime.now(timezone.utc)
        
        # Valid: 5 days ago in a 14-day window
        self.assertTrue(self.processor.is_valid_date(now - timedelta(days=5), 14))
        
        # Invalid: 20 days ago in a 14-day window
        self.assertFalse(self.processor.is_valid_date(now - timedelta(days=20), 14))
        
        # Invalid: Future date
        self.assertFalse(self.processor.is_valid_date(now + timedelta(days=3), 14))
        
        # Invalid: None date
        self.assertFalse(self.processor.is_valid_date(None, 14))

    # 3. Relevance & Noise Filtering Tests
    def test_relevance_and_noise_filtering(self):
        # Noise stock article
        spam_article = RawArticle(
            title="Why OpenAI Stock Rose Today: Motley Fool Analysis",
            link="https://fool.com/stocks",
            source="Motley Fool",
            snippet="Short interest and options trading volume in penny stocks.",
            company="OpenAI"
        )
        self.assertFalse(self.processor.is_relevant_and_clean(spam_article))

        # Irrelevant mention without company token
        unrelated = RawArticle(
            title="Best Smart Vacuum Cleaners for Summer 2026",
            link="https://reviews.com/vacuums",
            source="Tech Reviews",
            snippet="Robot vacuums tested for pet hair removal.",
            company="Anthropic"
        )
        self.assertFalse(self.processor.is_relevant_and_clean(unrelated))

        # Real high-signal announcement
        real_article = RawArticle(
            title="Anthropic Releases Claude 3.7 Sonnet With Hybrid Reasoning",
            link="https://techcrunch.com/anthropic",
            source="TechCrunch",
            snippet="Anthropic announces Claude 3.7 Sonnet with toggleable thinking time.",
            company="Anthropic",
            published_at=datetime.now(timezone.utc)
        )
        self.assertTrue(self.processor.is_relevant_and_clean(real_article))

    # 4. Duplicate Detection & Consolidation Tests
    def test_duplicate_detection_and_consolidation(self):
        now = datetime.now(timezone.utc)
        art1 = RawArticle(
            title="Anthropic Launches Claude 3.7 Sonnet Hybrid Reasoning Model",
            link="https://techcrunch.com/art1",
            source="TechCrunch",
            snippet="Anthropic releases new model.",
            company="Anthropic",
            published_at=now
        )
        art2 = RawArticle(
            title="Anthropic Releases Claude 3.7 Sonnet With New Reasoning Features",
            link="https://theverge.com/art2",
            source="The Verge",
            snippet="Anthropic unveils Claude 3.7 Sonnet.",
            company="Anthropic",
            published_at=now
        )
        art_other = RawArticle(
            title="Anthropic Slashes Token Pricing by 50% for Prompt Caching",
            link="https://anthropic.com/pricing",
            source="Anthropic Blog",
            snippet="Prompt caching discount announced.",
            company="Anthropic",
            published_at=now
        )

        clusters = self.processor.deduplicate_articles([art1, art2, art_other])
        self.assertEqual(len(clusters), 2)
        
        # Sonnet cluster should contain both TechCrunch and The Verge articles
        sonnet_cluster = [c for c in clusters if "Claude 3.7 Sonnet" in c[0].title][0]
        self.assertEqual(len(sonnet_cluster[1]), 2)

    # 5. Category Assignment Across All 7 Categories Tests
    def test_category_assignment_across_7_categories(self):
        test_cases = [
            ("OpenAI launches Operator agent general availability preview", "New autonomous browser agent rollout", CategoryEnum.PRODUCT_LAUNCHES),
            ("Anthropic cuts token pricing and adds enterprise discount tier", "Slashed per-million tokens cost and added pricing plan", CategoryEnum.PRICING),
            ("Former Google DeepMind research VP joins OpenAI as Head of Post-Training", "Key leadership hire departs to rival lab", CategoryEnum.HIRING),
            ("Cursor partners with Databricks to bring enterprise AI code assistant", "Strategic distribution and integration alliance announced", CategoryEnum.PARTNERSHIPS),
            ("Perplexity AI raises $500M Series C funding round at $9B valuation", "Venture capital fundraise backed by institutional investors", CategoryEnum.FUNDING_ACQUISITIONS),
            ("Mistral AI expands into Japan and opens new Tokyo sovereign AI datacenter", "Global expansion into Asian market and localized cloud", CategoryEnum.MARKET_EXPANSION),
            ("OpenAI releases new reasoning model benchmarks and technical architecture", "Breakthrough evals on math, synthetic data, and latency", CategoryEnum.TECH_AI_DEVELOPMENTS),
        ]

        for title, snippet, expected in test_cases:
            assigned = self.processor.assign_category(title, snippet)
            self.assertEqual(assigned, expected, f"Failed for '{title}'. Got {assigned}, expected {expected}")

    # 6. Priority and Business Impact Tests
    def test_priority_and_business_impact(self):
        priority = self.processor.evaluate_priority(
            title="OpenAI announces flagship breakthrough o3 model",
            snippet="Groundbreaking reasoning model sweeps benchmarks.",
            cluster_size=4,
            category=CategoryEnum.PRODUCT_LAUNCHES
        )
        self.assertEqual(priority, PriorityLevel.CRITICAL)

        impact = self.processor.derive_business_impact(
            category=CategoryEnum.PRICING,
            priority=PriorityLevel.HIGH,
            headline="Anthropic slashes token pricing",
            company="Anthropic"
        )
        self.assertIn("Inference cost commoditization", impact)

    # 7. Missing Sources & Monitoring Gaps Tests
    def test_monitoring_gaps_reporting(self):
        competitors = ["OpenAI", "QuietCo"]
        updates = {
            "OpenAI": [
                RetainedUpdate(
                    id="u1",
                    company="OpenAI",
                    headline="OpenAI Launches o3",
                    category=CategoryEnum.PRODUCT_LAUNCHES,
                    event_date="Oct 10, 2026",
                    source_url="https://openai.com",
                    concise_summary="Launched o3 model.",
                    priority_level=PriorityLevel.HIGH,
                    potential_business_impact="Competes with frontier models.",
                    source_publishers=["TechCrunch"]
                )
            ],
            "QuietCo": []  # No updates found
        }

        report = self.reporter.synthesize_report(
            competitors=competitors,
            updates_by_comp=updates,
            period_days=14,
            raw_signals_count=10
        )
        self.assertIn("QuietCo", report.monitoring_gaps)
        self.assertIn("No verified public announcements detected", report.monitoring_gaps["QuietCo"])

    # 8. Sample Benchmark Data Explicit Labeling Tests
    def test_sample_benchmark_data_is_explicitly_labeled(self):
        search_engine = SearchEngine()
        sample_records = search_engine.get_explicit_sample_data("OpenAI", days=14)
        self.assertTrue(len(sample_records) > 0)
        for r in sample_records:
            self.assertTrue(r.is_sample_data)
            self.assertIn("[DEMO SAMPLE]", r.title)

    # 9. CSV and PDF Export Tests
    def test_csv_and_pdf_export(self):
        competitors = ["OpenAI", "Anthropic", "Cursor", "Perplexity AI", "Mistral AI"]
        updates = {c: [] for c in competitors}
        updates["OpenAI"].append(
            RetainedUpdate(
                id="u_test",
                company="OpenAI",
                headline="OpenAI Releases o3-mini Reasoning Model",
                category=CategoryEnum.PRODUCT_LAUNCHES,
                event_date="Oct 12, 2026",
                source_url="https://openai.com/o3",
                concise_summary="New lightweight reasoning model released.",
                priority_level=PriorityLevel.HIGH,
                potential_business_impact="Increases reasoning speed.",
                source_publishers=["OpenAI Blog", "TechCrunch"]
            )
        )

        report = self.reporter.synthesize_report(competitors, updates, period_days=14, raw_signals_count=25)

        # CSV Export Verification
        csv_str = self.reporter.export_csv(report)
        self.assertIn("Company,Headline [Factual],Category,Priority Level", csv_str)
        self.assertIn("OpenAI Releases o3-mini Reasoning Model", csv_str)

        # PDF Export Verification
        pdf_bytes = self.reporter.export_pdf(report)
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
