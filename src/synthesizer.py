"""
Intelligence Brief Synthesizer.
Transforms categorized competitor updates into an executive-ready brief,
threat matrix, and cross-competitor strategic recommendations.
"""

from typing import List, Dict
from datetime import datetime
import json

from src.models import (
    IntelligenceBrief,
    CompetitorReport,
    ProcessedUpdate,
    CategoryEnum,
    ImpactLevel
)


class BriefSynthesizer:
    def __init__(self):
        pass

    def synthesize(
        self,
        competitors: List[str],
        all_updates: List[ProcessedUpdate],
        time_window_days: int = 14,
        raw_signals_count: int = 0
    ) -> IntelligenceBrief:
        """
        Synthesizes all updates into a cohesive IntelligenceBrief.
        """
        # Group updates by competitor
        updates_by_comp: Dict[str, List[ProcessedUpdate]] = {c: [] for c in competitors}
        for u in all_updates:
            if u.company in updates_by_comp:
                updates_by_comp[u.company].append(u)

        # Build threat matrix: {company: {category: count}}
        all_cats = [c.value for c in CategoryEnum]
        threat_matrix: Dict[str, Dict[str, int]] = {}
        competitor_reports: Dict[str, CompetitorReport] = {}

        for comp, updates in updates_by_comp.items():
            cat_counts = {cat: 0 for cat in all_cats}
            sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
            
            for u in updates:
                cat_counts[u.category.value] = cat_counts.get(u.category.value, 0) + 1
                sentiment_counts[u.sentiment] = sentiment_counts.get(u.sentiment, 0) + 1

            threat_matrix[comp] = cat_counts

            # Extract top highlights
            high_impact_updates = [u for u in updates if u.impact == ImpactLevel.HIGH]
            highlights = [u.title for u in high_impact_updates[:3]]
            if not highlights and updates:
                highlights = [updates[0].title]

            competitor_reports[comp] = CompetitorReport(
                company=comp,
                total_updates=len(updates),
                updates_by_category=cat_counts,
                updates=updates,
                key_highlights=highlights,
                sentiment_breakdown=sentiment_counts
            )

        # Generate macro trends & executive overview
        macro_trends = self._identify_macro_trends(all_updates, competitors)
        executive_summary = self._generate_executive_summary(competitor_reports, all_updates, time_window_days)
        recommendations = self._generate_recommendations(all_updates, threat_matrix)

        brief = IntelligenceBrief(
            title="AI Competitor Intelligence Brief",
            generated_at=datetime.now(),
            competitors_tracked=competitors,
            time_window_days=time_window_days,
            total_signals_analyzed=raw_signals_count,
            total_meaningful_updates=len(all_updates),
            executive_summary=executive_summary,
            macro_trends=macro_trends,
            competitor_reports=competitor_reports,
            threat_matrix=threat_matrix,
            actionable_recommendations=recommendations,
            all_updates=all_updates
        )

        return brief

    def _generate_executive_summary(
        self,
        reports: Dict[str, CompetitorReport],
        all_updates: List[ProcessedUpdate],
        days: int
    ) -> str:
        """
        Generates an executive narrative highlighting momentum and primary competitive themes.
        """
        if not all_updates:
            return (
                f"During the past {days} days, monitoring revealed low baseline signal activity "
                "across the selected competitors, with no major disruption events detected."
            )

        # Find most active competitor
        sorted_reports = sorted(reports.values(), key=lambda r: r.total_updates, reverse=True)
        top_comp = sorted_reports[0] if sorted_reports else None

        # Category distribution
        cat_counts: Dict[str, int] = {}
        high_impact_count = 0
        for u in all_updates:
            cat_counts[u.category.value] = cat_counts.get(u.category.value, 0) + 1
            if u.impact == ImpactLevel.HIGH:
                high_impact_count += 1

        top_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "Product"

        summary = (
            f"Over the trailing {days}-day cycle, competitive velocity remained concentrated in "
            f"**{top_cat}** ({cat_counts.get(top_cat, 0)} updates), with {high_impact_count} high-impact "
            f"strategic developments identified across {len(reports)} tracked companies.\n\n"
        )

        if top_comp and top_comp.total_updates > 0:
            summary += (
                f"**{top_comp.company}** demonstrated the highest aggregate release velocity with "
                f"{top_comp.total_updates} verified updates. Key activity centered around "
                f"accelerated deployment cycles and expanded ecosystem integrations."
            )

        return summary

    def _identify_macro_trends(self, updates: List[ProcessedUpdate], competitors: List[str]) -> List[str]:
        """
        Extracts strategic cross-cutting patterns across competitors.
        """
        trends = []
        cat_counts = {}
        for u in updates:
            cat_counts[u.category.value] = cat_counts.get(u.category.value, 0) + 1

        if cat_counts.get(CategoryEnum.PRODUCT_TECH.value, 0) >= 3:
            trends.append(
                "**Agentic & Workflow Automation Arms Race:** Competitors are shifting focus from raw foundation model "
                "benchmarks toward autonomous agent workflows, tool calling, and developer canvas integrations."
            )

        if cat_counts.get(CategoryEnum.PRICING_PACKAGING.value, 0) >= 1:
            trends.append(
                "**Aggressive Inference Cost Deflation:** Slashed token pricing and aggressive free/developer tier "
                "expansions are exerting downward pressure on customer acquisition costs across the AI stack."
            )

        if cat_counts.get(CategoryEnum.PARTNERSHIP_MA.value, 0) >= 1:
            trends.append(
                "**Ecosystem Lock-in via Enterprise Partnerships:** Heightened alliance-building with major cloud providers "
                "and enterprise platforms to defend distribution moats against standalone point solutions."
            )

        if cat_counts.get(CategoryEnum.HIRING_LEADERSHIP.value, 0) >= 1:
            trends.append(
                "**Strategic Talent Migration:** High-profile leadership transitions and targeted hiring in post-training "
                "and reasoning research signify key realignment in frontier product roadmaps."
            )

        if not trends:
            trends = [
                "**Incremental Feature Releases:** Continuous integration cadence with steady product iterations.",
                "**Enterprise Compliance Hardening:** Increased emphasis on governance, privacy, and SLA stability."
            ]

        return trends

    def _generate_recommendations(
        self,
        updates: List[ProcessedUpdate],
        threat_matrix: Dict[str, Dict[str, int]]
    ) -> List[str]:
        """
        Produces actionable counter-strategies and watchlist alerts for decision-makers.
        """
        recs = [
            "**Benchmark Core Model Latency & Costs:** Re-evaluate inference cost structure against competitor free tiers and newly discounted context windows.",
            "**Accelerate Agent & Tool Integration Roadmap:** Ensure seamless developer tool-use and IDE/agent extensions to counter rival ecosystem lock-ins.",
            "**Strengthen Enterprise Security & Compliance Positioning:** Capitalize on competitor regulatory scrutiny and privacy probes to win risk-sensitive enterprise logos.",
            "**Monitor Developer Community Sentiment:** Track developer adoption patterns on Hacker News and social channels to identify emerging developer frustration or migration waves."
        ]
        return recs

    def to_markdown(self, brief: IntelligenceBrief) -> str:
        """
        Renders the Intelligence Brief as clean, executive GitHub Markdown.
        """
        lines = []
        lines.append(f"# 🛡️ AI Competitor Intelligence Brief")
        lines.append(f"**Generated:** {brief.generated_at.strftime('%Y-%m-%d %H:%M UTC')} | "
                     f"**Window:** Last {brief.time_window_days} Days | "
                     f"**Tracked Entities:** {', '.join(brief.competitors_tracked)}")
        lines.append(f"**Signals Ingested:** {brief.total_signals_analyzed} | "
                     f"**Curated Updates:** {brief.total_meaningful_updates}")
        lines.append("\n---\n")

        # Executive Summary
        lines.append("## 📌 Executive Summary")
        lines.append(brief.executive_summary)
        lines.append("\n")

        # Macro Trends
        lines.append("## 🌐 Cross-Competitor Macro Trends")
        for trend in brief.macro_trends:
            lines.append(f"- {trend}")
        lines.append("\n")

        # Threat Matrix
        lines.append("## 📊 Competitive Activity Matrix")
        headers = ["Competitor", "Total", "Product 🚀", "Pricing 💰", "Partnership 🤝", "Hiring 👥", "Funding 📈", "Legal ⚖️"]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for comp in brief.competitors_tracked:
            matrix = brief.threat_matrix.get(comp, {})
            total = sum(matrix.values())
            prod = matrix.get(CategoryEnum.PRODUCT_TECH.value, 0)
            price = matrix.get(CategoryEnum.PRICING_PACKAGING.value, 0)
            part = matrix.get(CategoryEnum.PARTNERSHIP_MA.value, 0)
            hire = matrix.get(CategoryEnum.HIRING_LEADERSHIP.value, 0)
            fund = matrix.get(CategoryEnum.FUNDING_FINANCIALS.value, 0)
            legal = matrix.get(CategoryEnum.LEGAL_REGULATORY.value, 0)
            lines.append(f"| **{comp}** | **{total}** | {prod} | {price} | {part} | {hire} | {fund} | {legal} |")
        lines.append("\n")

        # Competitor Deep-Dive
        lines.append("## 🔍 Competitor Breakdown")
        for comp in brief.competitors_tracked:
            report = brief.competitor_reports.get(comp)
            lines.append(f"### {comp} ({report.total_updates if report else 0} Updates)")
            
            if not report or not report.updates:
                lines.append("_No major high-signal updates verified during this period._\n")
                continue

            for u in report.updates:
                impact_badge = f"`[{u.impact.value.upper()} IMPACT]`"
                cat_badge = f"{u.category.emoji} **{u.category.value}**"
                date_str = f" • _{u.published_date}_" if u.published_date else ""
                source_str = f" [{u.source_names[0]}]({u.primary_url})" if u.source_names and u.primary_url else ""
                
                lines.append(f"- {cat_badge} {impact_badge} **[{u.title}]({u.primary_url})**{date_str}{source_str}")
                if u.summary:
                    lines.append(f"  - **Overview:** {u.summary}")
                if u.why_it_matters:
                    lines.append(f"  - **Why It Matters:** _{u.why_it_matters}_")
            lines.append("")

        # Actionable Recommendations
        lines.append("## 🎯 Strategic Action Items & Radar")
        for rec in brief.actionable_recommendations:
            lines.append(f"- {rec}")

        return "\n".join(lines)

    def to_html(self, brief: IntelligenceBrief) -> str:
        """
        Renders the Intelligence Brief as a modern, self-contained HTML document.
        """
        matrix_rows = ""
        for comp in brief.competitors_tracked:
            matrix = brief.threat_matrix.get(comp, {})
            total = sum(matrix.values())
            prod = matrix.get(CategoryEnum.PRODUCT_TECH.value, 0)
            price = matrix.get(CategoryEnum.PRICING_PACKAGING.value, 0)
            part = matrix.get(CategoryEnum.PARTNERSHIP_MA.value, 0)
            hire = matrix.get(CategoryEnum.HIRING_LEADERSHIP.value, 0)
            fund = matrix.get(CategoryEnum.FUNDING_FINANCIALS.value, 0)
            legal = matrix.get(CategoryEnum.LEGAL_REGULATORY.value, 0)
            matrix_rows += f"""
            <tr>
                <td><strong>{comp}</strong></td>
                <td><span class="badge total-badge">{total}</span></td>
                <td>{prod}</td>
                <td>{price}</td>
                <td>{part}</td>
                <td>{hire}</td>
                <td>{fund}</td>
                <td>{legal}</td>
            </tr>
            """

        deep_dive_html = ""
        for comp in brief.competitors_tracked:
            report = brief.competitor_reports.get(comp)
            updates_html = ""
            if not report or not report.updates:
                updates_html = "<p class='no-updates'>No major verified events detected in this window.</p>"
            else:
                for u in report.updates:
                    impact_class = f"impact-{u.impact.value.lower()}"
                    updates_html += f"""
                    <div class="update-card">
                        <div class="update-header">
                            <span class="category-tag">{u.category.emoji} {u.category.value}</span>
                            <span class="impact-tag {impact_class}">{u.impact.value} Impact</span>
                            <span class="date-tag">{u.published_date or 'Recent'}</span>
                        </div>
                        <h4 class="update-title"><a href="{u.primary_url}" target="_blank">{u.title}</a></h4>
                        <p class="update-summary">{u.summary}</p>
                        <div class="why-box">
                            <strong>Why It Matters:</strong> {u.why_it_matters}
                        </div>
                    </div>
                    """

            deep_dive_html += f"""
            <div class="comp-section">
                <h3>{comp} <span class="count-badge">{report.total_updates if report else 0} updates</span></h3>
                {updates_html}
            </div>
            """

        macro_trends_html = "".join([f"<li>{trend}</li>" for trend in brief.macro_trends])
        recs_html = "".join([f"<li>{rec}</li>" for rec in brief.actionable_recommendations])

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{brief.title}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --accent: #10b981;
            --high-impact: #ef4444;
            --med-impact: #f59e0b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 2.5rem 1rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        h1 {{
            margin: 0 0 0.5rem 0;
            font-size: 2rem;
            color: #60a5fa;
        }}
        .meta-bar {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        .section-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        h2 {{
            color: #38bdf8;
            font-size: 1.3rem;
            margin-top: 0;
            border-bottom: 1px solid #334155;
            padding-bottom: 0.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        .update-card {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .update-header {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
        }}
        .category-tag {{
            background: #1e3a8a;
            color: #93c5fd;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .impact-tag {{
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .impact-high {{ background: #7f1d1d; color: #fca5a5; }}
        .impact-medium {{ background: #78350f; color: #fde68a; }}
        .impact-low {{ background: #1e293b; color: #cbd5e1; }}
        .date-tag {{ color: var(--text-muted); margin-left: auto; }}
        .update-title a {{
            color: #f8fafc;
            text-decoration: none;
        }}
        .update-title a:hover {{ text-decoration: underline; color: #60a5fa; }}
        .update-summary {{ color: #cbd5e1; font-size: 0.95rem; }}
        .why-box {{
            background: rgba(59, 130, 246, 0.1);
            border-left: 3px solid var(--primary);
            padding: 0.5rem 0.75rem;
            font-size: 0.9rem;
            border-radius: 0 4px 4px 0;
            margin-top: 0.5rem;
        }}
        .count-badge {{
            font-size: 0.8rem;
            background: #334155;
            padding: 2px 8px;
            border-radius: 12px;
            color: #cbd5e1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ {brief.title}</h1>
            <div class="meta-bar">
                Generated {brief.generated_at.strftime('%b %d, %Y %H:%M UTC')} | 
                Tracking {len(brief.competitors_tracked)} entities | 
                Window: Last {brief.time_window_days} Days
            </div>
        </header>

        <div class="section-card">
            <h2>📌 Executive Summary</h2>
            <p>{brief.executive_summary}</p>
        </div>

        <div class="section-card">
            <h2>🌐 Cross-Competitor Macro Trends</h2>
            <ul>{macro_trends_html}</ul>
        </div>

        <div class="section-card">
            <h2>📊 Competitive Activity Matrix</h2>
            <table>
                <thead>
                    <tr>
                        <th>Competitor</th>
                        <th>Total</th>
                        <th>Product 🚀</th>
                        <th>Pricing 💰</th>
                        <th>Partnerships 🤝</th>
                        <th>Hiring 👥</th>
                        <th>Funding 📈</th>
                        <th>Legal ⚖️</th>
                    </tr>
                </thead>
                <tbody>{matrix_rows}</tbody>
            </table>
        </div>

        <div class="section-card">
            <h2>🔍 Competitor Deep-Dive</h2>
            {deep_dive_html}
        </div>

        <div class="section-card">
            <h2>🎯 Strategic Action Items & Radar</h2>
            <ul>{recs_html}</ul>
        </div>
    </div>
</body>
</html>
        """
        return html_template
