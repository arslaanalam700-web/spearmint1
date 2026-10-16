"""
AI Competitor Watch Agent Orchestrator.
Orchestrates collection, deduplication, categorization, and synthesis of competitive intelligence.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.models import (
    IntelligenceBrief,
    ProcessedUpdate,
    RawArticle
)
from src.collector import CompetitorDataCollector
from src.deduplicator import UpdateDeduplicator
from src.categorizer import UpdateCategorizer
from src.synthesizer import BriefSynthesizer
from src.config import PRESET_COMPETITOR_GROUPS


class CompetitorWatchAgent:
    """
    Main Agent class for autonomous competitive intelligence monitoring.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        similarity_threshold: float = 0.50,
        request_timeout: int = 12
    ):
        self.collector = CompetitorDataCollector(request_timeout=request_timeout)
        self.deduplicator = UpdateDeduplicator(similarity_threshold=similarity_threshold)
        self.categorizer = UpdateCategorizer(gemini_api_key=gemini_api_key)
        self.synthesizer = BriefSynthesizer()

    def run(
        self,
        competitors: List[str],
        days: int = 14,
        max_updates_per_company: int = 8,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> IntelligenceBrief:
        """
        Executes end-to-end competitive monitoring workflow.
        
        Args:
            competitors: List of 5-10 company/product names.
            days: Historical search window in days.
            max_updates_per_company: Cap on curated updates per competitor to keep brief concise.
            progress_callback: Optional hook for UI progress updates (step_message, fraction).
        """
        # Clean competitor names
        clean_competitors = [c.strip() for c in competitors if c.strip()]
        if not clean_competitors:
            raise ValueError("At least one competitor name must be provided.")

        if progress_callback:
            progress_callback(f"Gathering real-time updates for {len(clean_competitors)} companies...", 0.15)

        # Step 1: Collect raw articles concurrently
        raw_articles_map = self.collector.collect_all(clean_competitors, days=days)
        total_raw_signals = sum(len(arts) for arts in raw_articles_map.values())

        if progress_callback:
            progress_callback(f"Ingested {total_raw_signals} raw signals. Filtering noise and clustering duplicates...", 0.45)

        # Step 2 & 3: Noise filtering, deduplication, and categorization per competitor
        all_curated_updates: List[ProcessedUpdate] = []

        for comp in clean_competitors:
            articles = raw_articles_map.get(comp, [])
            
            # Deduplicate and cluster into canonical events
            clusters = self.deduplicator.deduplicate_and_cluster(articles)
            
            # Convert clusters to ProcessedUpdates
            comp_updates: List[ProcessedUpdate] = []
            for canonical, cluster_members in clusters:
                update = self.categorizer.process_cluster(canonical, cluster_members)
                comp_updates.append(update)

            # Sort by impact (High first) and then recency/confidence
            comp_updates.sort(
                key=lambda u: (
                    1 if u.impact.value == "High" else (2 if u.impact.value == "Medium" else 3),
                    -u.confidence_score
                )
            )

            # Keep top high-signal updates per competitor
            curated_for_comp = comp_updates[:max_updates_per_company]
            all_curated_updates.extend(curated_for_comp)

        if progress_callback:
            progress_callback(f"Synthesizing executive brief and activity matrix...", 0.80)

        # Step 4: Synthesize Intelligence Brief
        brief = self.synthesizer.synthesize(
            competitors=clean_competitors,
            all_updates=all_curated_updates,
            time_window_days=days,
            raw_signals_count=total_raw_signals
        )

        if progress_callback:
            progress_callback("Analysis complete!", 1.0)

        return brief

    def export_markdown(self, brief: IntelligenceBrief, filepath: str) -> None:
        """Exports brief as Markdown document."""
        md_content = self.synthesizer.to_markdown(brief)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

    def export_html(self, brief: IntelligenceBrief, filepath: str) -> None:
        """Exports brief as styled standalone HTML document."""
        html_content = self.synthesizer.to_html(brief)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

    def export_json(self, brief: IntelligenceBrief, filepath: str) -> None:
        """Exports brief as structured JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(brief.model_dump_json(indent=2))


def cli_main():
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(
        description="AI Competitor Watch Agent - Automated market intelligence."
    )
    parser.add_argument(
        "--competitors", "-c",
        type=str,
        help="Comma-separated list of 5-10 competitors (e.g. 'OpenAI, Anthropic, Cursor, Mistral AI')"
    )
    parser.add_argument(
        "--preset", "-p",
        type=str,
        choices=list(PRESET_COMPETITOR_GROUPS.keys()),
        default="Frontier AI Labs",
        help="Select a curated preset competitor group"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=14,
        help="Search window in days (default: 14)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="intelligence_brief.md",
        help="Path to save markdown brief (default: intelligence_brief.md)"
    )
    parser.add_argument(
        "--html",
        type=str,
        default=None,
        help="Optional path to export HTML brief"
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Optional path to export JSON output"
    )

    args = parser.parse_args()

    if args.competitors:
        comps = [c.strip() for c in args.competitors.split(",") if c.strip()]
    else:
        comps = PRESET_COMPETITOR_GROUPS[args.preset]

    print(f"\n🚀 Initializing AI Competitor Watch Agent...")
    print(f"🎯 Target Competitors: {', '.join(comps)}")
    print(f"⏱️  Time Window: Last {args.days} days")

    agent = CompetitorWatchAgent()
    brief = agent.run(
        competitors=comps,
        days=args.days,
        progress_callback=lambda msg, p: print(f"  [{int(p*100)}%] {msg}")
    )

    agent.export_markdown(brief, args.output)
    print(f"\n✅ Markdown Brief saved to: {args.output}")

    if args.html:
        agent.export_html(brief, args.html)
        print(f"✅ HTML Brief saved to: {args.html}")

    if args.json:
        agent.export_json(brief, args.json)
        print(f"✅ JSON Data saved to: {args.json}")

    print("\n" + "=" * 60)
    print(agent.synthesizer.to_markdown(brief))
    print("=" * 60)


if __name__ == "__main__":
    cli_main()
