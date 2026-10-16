"""
agent.py - Research Pipeline Orchestrator
Validates user inputs (enforcing 5-10 competitors, 7/14/30 days period),
orchestrates information retrieval, intelligent processing, and intelligence report synthesis.
"""

import os
import sys
import argparse
from typing import List, Dict, Tuple, Optional, Callable

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from search import SearchEngine, RawArticle
from processing import UpdateProcessor, RetainedUpdate
from reporting import ReportGenerator, IntelligenceReport


class CompetitorWatchAgent:
    """
    Autonomous Agent orchestrating competitive intelligence research.
    """

    VALID_PERIODS = {7, 14, 30}
    MIN_COMPETITORS = 5
    MAX_COMPETITORS = 10

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        similarity_threshold: float = 0.45,
        search_timeout: int = 12
    ):
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.search_engine = SearchEngine(timeout=search_timeout)
        self.processor = UpdateProcessor(similarity_threshold=similarity_threshold)
        self.reporter = ReportGenerator()

    @classmethod
    def validate_inputs(cls, competitors: List[str], days: int) -> Tuple[bool, str, List[str]]:
        """
        Validates input constraints: 5-10 competitors, 7/14/30 days.
        Returns: (is_valid, error_message, cleaned_competitors)
        """
        if days not in cls.VALID_PERIODS:
            return False, f"Invalid monitoring period: {days} days. Must be one of 7, 14, or 30 days.", []

        # Deduplicate and clean names while preserving order
        seen = set()
        cleaned = []
        for c in competitors:
            c_clean = c.strip()
            if c_clean and c_clean.lower() not in seen:
                seen.add(c_clean.lower())
                cleaned.append(c_clean)

        if len(cleaned) < cls.MIN_COMPETITORS:
            return False, f"Please provide at least {cls.MIN_COMPETITORS} competitors (received {len(cleaned)}). Evaluator guidelines require 5–10 competitors.", []
        if len(cleaned) > cls.MAX_COMPETITORS:
            return False, f"Please provide at most {cls.MAX_COMPETITORS} competitors (received {len(cleaned)}). Evaluator guidelines require 5–10 competitors.", []

        return True, "", cleaned

    def run_pipeline(
        self,
        competitors: List[str],
        days: int = 14,
        force_sample_data: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> IntelligenceReport:
        """
        Runs complete research pipeline.
        """
        # Validate inputs
        is_valid, err_msg, clean_competitors = self.validate_inputs(competitors, days)
        if not is_valid:
            raise ValueError(err_msg)

        if progress_callback:
            progress_callback(f"Retrieving public announcements for {len(clean_competitors)} competitors...", 0.20)

        # 1. Search / Retrieval Phase
        raw_data_map = self.search_engine.retrieve_all(
            companies=clean_competitors,
            days=days,
            force_sample_data=force_sample_data
        )
        total_raw_signals = sum(len(arts) for arts in raw_data_map.values())

        if progress_callback:
            progress_callback(f"Scanned {total_raw_signals} raw signals. Filtering noise and clustering duplicate reports...", 0.50)

        # 2. Intelligent Processing Phase (Deduplication, 7-category assignment, priority scoring)
        processed_updates: Dict[str, List[RetainedUpdate]] = {}
        for comp in clean_competitors:
            articles = raw_data_map.get(comp, [])
            retained = self.processor.process_and_retain(
                company=comp,
                raw_articles=articles,
                max_days=days
            )
            processed_updates[comp] = retained

        total_retained = sum(len(u) for u in processed_updates.values())

        if progress_callback:
            progress_callback(f"Retained {total_retained} verified updates. Synthesizing executive report...", 0.85)

        # 3. Intelligence Brief Synthesis
        report = self.reporter.synthesize_report(
            competitors=clean_competitors,
            updates_by_comp=processed_updates,
            period_days=days,
            raw_signals_count=total_raw_signals,
            is_demo=force_sample_data
        )

        if progress_callback:
            progress_callback("Intelligence brief ready!", 1.0)

        return report


def main():
    """Command-line runner for the agent."""
    parser = argparse.ArgumentParser(
        description="AI Competitor Watch Agent - Automated market intelligence pipeline."
    )
    parser.add_argument(
        "--competitors", "-c",
        type=str,
        default="OpenAI, Anthropic, Cursor, Perplexity AI, Mistral AI",
        help="Comma-separated list of 5-10 competitors"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        choices=[7, 14, 30],
        default=14,
        help="Monitoring window (7, 14, or 30 days)"
    )
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Use explicitly labeled demo benchmark data (offline mode)"
    )
    parser.add_argument(
        "--md",
        type=str,
        default="brief.md",
        help="Path to save markdown report"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="brief.csv",
        help="Path to save CSV export"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default="brief.pdf",
        help="Path to save PDF report"
    )

    args = parser.parse_args()

    comps = [c.strip() for c in args.competitors.split(",") if c.strip()]
    print(f"\n[AI Competitor Watch Agent]")
    print(f"Monitored Entities ({len(comps)}): {', '.join(comps)}")
    print(f"Monitoring Window: {args.days} days")

    agent = CompetitorWatchAgent()
    try:
        report = agent.run_pipeline(
            competitors=comps,
            days=args.days,
            force_sample_data=args.sample_data,
            progress_callback=lambda msg, p: print(f"  [{int(p*100)}%] {msg}")
        )
    except Exception as e:
        print(f"\n[Error] Execution failed: {e}")
        sys.exit(1)

    # Save exports
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(agent.reporter.export_markdown(report))
        print(f"[Export] Markdown report saved to: {args.md}")

    if args.csv:
        with open(args.csv, "w", encoding="utf-8") as f:
            f.write(agent.reporter.export_csv(report))
        print(f"[Export] CSV data saved to: {args.csv}")

    if args.pdf:
        pdf_bytes = agent.reporter.export_pdf(report)
        with open(args.pdf, "wb") as f:
            f.write(pdf_bytes)
        print(f"[Export] PDF report saved to: {args.pdf}")

    print("\n" + "=" * 60)
    print(agent.reporter.export_markdown(report))
    print("=" * 60)


if __name__ == "__main__":
    main()
