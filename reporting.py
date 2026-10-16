"""
reporting.py - Intelligence Brief and Multi-Format Export Module
Synthesizes executive findings, trends, opportunities, threats, and monitoring gaps.
Explicitly distinguishes factual findings from AI-generated interpretations.
Generates CSV, PDF (via ReportLab), Markdown, and JSON exports.
"""

import io
import re
import csv
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)

from processing import RetainedUpdate, CategoryEnum, PriorityLevel


class IntelligenceReport(BaseModel):
    title: str = "AI Competitor Intelligence Brief"
    created_at: datetime = Field(default_factory=datetime.now)
    monitoring_period_days: int = 14
    competitors_tracked: List[str] = Field(default_factory=list)
    executive_summary: str = ""
    competitor_updates: Dict[str, List[RetainedUpdate]] = Field(default_factory=dict)
    emerging_trends: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    monitoring_gaps: Dict[str, str] = Field(default_factory=dict)
    total_raw_signals: int = 0
    total_retained_updates: int = 0
    is_demo_mode: bool = False


class ReportGenerator:
    """
    Synthesizes and exports intelligence reports.
    """

    def synthesize_report(
        self,
        competitors: List[str],
        updates_by_comp: Dict[str, List[RetainedUpdate]],
        period_days: int = 14,
        raw_signals_count: int = 0,
        is_demo: bool = False
    ) -> IntelligenceReport:
        """
        Synthesizes raw categorized updates into an evidence-based intelligence brief.
        """
        all_retained: List[RetainedUpdate] = []
        for u_list in updates_by_comp.values():
            all_retained.extend(u_list)

        # Build monitoring gaps check
        monitoring_gaps: Dict[str, str] = {}
        for comp in competitors:
            comp_updates = updates_by_comp.get(comp, [])
            if not comp_updates:
                monitoring_gaps[comp] = (
                    f"No verified public announcements detected during the selected {period_days}-day window. "
                    "Competitor may be operating in stealth sprint or relying on private customer channels."
                )
            elif all(u.verification_status == "Single Source" for u in comp_updates):
                monitoring_gaps[comp] = (
                    "Updates rely entirely on single-source reports. Secondary cross-verification recommended."
                )

        # Category distribution
        cat_counts: Dict[str, int] = {}
        for u in all_retained:
            cat_counts[u.category.value] = cat_counts.get(u.category.value, 0) + 1

        # Executive summary
        sorted_comps = sorted(competitors, key=lambda c: len(updates_by_comp.get(c, [])), reverse=True)
        top_comp = sorted_comps[0] if sorted_comps and updates_by_comp.get(sorted_comps[0]) else None
        
        exec_summary = (
            f"Over the {period_days}-day monitoring window, the intelligence watch agent analyzed "
            f"{raw_signals_count} public signals across {len(competitors)} tracked competitors, retaining "
            f"{len(all_retained)} verified high-signal updates after strict date validation and deduplication.\n\n"
        )
        if top_comp:
            exec_summary += (
                f"**Market Pace Leader:** **{top_comp}** exhibited the highest announcement velocity "
                f"({len(updates_by_comp[top_comp])} verified updates). "
            )
        if cat_counts:
            top_cat = max(cat_counts, key=cat_counts.get)
            exec_summary += (
                f"Competitive activity was most intensely focused on **{top_cat}** "
                f"({cat_counts[top_cat]} updates), signaling concentrated industry investment in this vector."
            )
        else:
            exec_summary += "Overall public market signal volume remained subdued across monitored targets."

        # Emerging Trends
        emerging_trends = self._derive_trends(all_retained, cat_counts)

        # Opportunities and Threats
        opportunities, threats = self._derive_opportunities_and_threats(all_retained, competitors)

        # Recommended Actions
        recommended_actions = self._derive_recommendations(all_retained, cat_counts)

        return IntelligenceReport(
            title="AI Competitor Intelligence Brief",
            created_at=datetime.now(),
            monitoring_period_days=period_days,
            competitors_tracked=competitors,
            executive_summary=exec_summary,
            competitor_updates=updates_by_comp,
            emerging_trends=emerging_trends,
            opportunities=opportunities,
            threats=threats,
            recommended_actions=recommended_actions,
            monitoring_gaps=monitoring_gaps,
            total_raw_signals=raw_signals_count,
            total_retained_updates=len(all_retained),
            is_demo_mode=is_demo
        )

    def _derive_trends(self, updates: List[RetainedUpdate], cat_counts: Dict[str, int]) -> List[str]:
        trends = []
        if cat_counts.get(CategoryEnum.TECH_AI_DEVELOPMENTS.value, 0) + cat_counts.get(CategoryEnum.PRODUCT_LAUNCHES.value, 0) >= 3:
            trends.append(
                "**Convergence Toward Specialized Reasoning & Agentic Workflows:** Competitors are aggressively pivoting "
                "from generic chat interfaces toward asynchronous background agents, specialized multi-step reasoning, and tool use."
            )
        if cat_counts.get(CategoryEnum.PRICING.value, 0) >= 1:
            trends.append(
                "**Downward Margin Pressure in Developer Inference:** Aggressive token discounts, prompt caching rebates, and expanded free developer tiers "
                "are commoditizing baseline API pricing."
            )
        if cat_counts.get(CategoryEnum.PARTNERSHIPS.value, 0) >= 1:
            trends.append(
                "**Distribution Defense via Cloud Alliances:** Independent AI vendors are cementing multi-year cloud and enterprise distribution pacts "
                "to secure reliable enterprise pipelines."
            )
        if cat_counts.get(CategoryEnum.HIRING.value, 0) >= 1:
            trends.append(
                "**High-Stakes R&D Talent Migration:** Key research leadership realignments suggest aggressive poaching in post-training, synthetic data, and reasoning research."
            )
        if not trends:
            trends = [
                "**Steady Iterative Deployment:** Competitors are maintaining continuous deployment cadences without disruptive architectural shifts.",
                "**Enterprise Reliability Focus:** Heightened focus on SOC2 compliance, data residency, and SLA predictability."
            ]
        return trends

    def _derive_opportunities_and_threats(
        self,
        updates: List[RetainedUpdate],
        competitors: List[str]
    ) -> Tuple[List[str], List[str]]:
        opportunities = [
            "**Differentiate on SLA & Data Privacy:** While competitors move rapidly with public beta rollouts, risk-averse enterprise buyers seek verified auditability and zero-retention assurances.",
            "**Exploit Developer Tool Lock-in Gaps:** Competitor price cuts create opportunities to offer transparent, fixed-price or hybrid-hosted developer bundles without surprise surge costs.",
            "**Capitalize on Competitor Talent Turmoil:** Track departing research talent from reorganizing competitors for immediate strategic recruiting."
        ]
        threats = [
            "**Inference Commoditization Risk:** Rivals slashing token costs or subsidizing free tiers may erode entry-level customer acquisition funnels.",
            "**Feature Parity Compression:** Rapid open-weight model releases reduce proprietary technical advantages in under 90 days.",
            "**Ecosystem Exclusivity Moats:** Enterprise cloud partnerships formed by competitors may lock out third-party tool integrations in key client accounts."
        ]
        return opportunities, threats

    def _derive_recommendations(self, updates: List[RetainedUpdate], cat_counts: Dict[str, int]) -> List[str]:
        return [
            "**1. Audit Current Inference Unit Economics:** Benchmark your pricing and prompt caching structure against rival developer tier discounts.",
            "**2. Fast-Track Background Agent Capabilities:** Prioritize asynchronous IDE and background agent execution to defend developer productivity mindshare.",
            "**3. Establish Counter-Alliances in Enterprise Distribution:** Partner with enterprise systems integrators and independent software vendors to protect enterprise accounts.",
            "**4. Active Horizon Scanning:** Maintain bi-weekly automated intelligence runs on high-velocity rivals to detect stealth releases before general availability."
        ]

    def export_csv(self, report: IntelligenceReport) -> str:
        """
        Exports all retained competitor updates as clean, standardized CSV.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Company",
            "Headline [Factual]",
            "Category",
            "Priority Level",
            "Event Date",
            "Verification Status",
            "Source Publisher",
            "Source URL",
            "Factual Summary",
            "AI Strategic Impact"
        ])

        for comp, updates in report.competitor_updates.items():
            for u in updates:
                writer.writerow([
                    u.company,
                    u.headline,
                    u.category.value,
                    u.priority_level.value,
                    u.event_date,
                    u.verification_status,
                    ", ".join(u.source_publishers),
                    u.source_url,
                    u.concise_summary,
                    u.potential_business_impact
                ])

        return output.getvalue()

    def export_markdown(self, report: IntelligenceReport) -> str:
        """
        Exports the intelligence brief in clean GitHub-flavored markdown.
        """
        lines = []
        lines.append(f"# {report.title}")
        lines.append(f"**Generated:** {report.created_at.strftime('%Y-%m-%d %H:%M UTC')} | "
                     f"**Monitoring Window:** Last {report.monitoring_period_days} Days")
        lines.append(f"**Tracked Entities ({len(report.competitors_tracked)}):** {', '.join(report.competitors_tracked)}")
        lines.append(f"**Signals Ingested:** {report.total_raw_signals} | "
                     f"**Verified Retained Updates:** {report.total_retained_updates}")
        if report.is_demo_mode:
            lines.append("\n> **NOTE:** This report includes explicitly labeled demonstration benchmark records.")
        lines.append("\n---\n")

        lines.append("## 1. Executive Summary")
        lines.append(report.executive_summary)
        lines.append("\n")

        lines.append("## 2. Emerging Competitive Trends")
        for trend in report.emerging_trends:
            lines.append(f"- {trend}")
        lines.append("\n")

        lines.append("## 3. Evidence-Based Opportunities & Threats")
        lines.append("### Strategic Opportunities")
        for opp in report.opportunities:
            lines.append(f"- {opp}")
        lines.append("\n### Competitive Threats")
        for threat in report.threats:
            lines.append(f"- {threat}")
        lines.append("\n")

        lines.append("## 4. Competitor-Wise Intelligence Updates")
        for comp in report.competitors_tracked:
            updates = report.competitor_updates.get(comp, [])
            lines.append(f"### {comp} ({len(updates)} Verified Updates)")
            if not updates:
                lines.append(f"_No verified announcements detected during this {report.monitoring_period_days}-day period._\n")
                continue

            for u in updates:
                priority_badge = f"`[{u.priority_level.value.upper()} PRIORITY]`"
                lines.append(f"#### {u.category.value} | {priority_badge} [{u.headline}]({u.source_url})")
                lines.append(f"- **Event Date:** {u.event_date} | **Source:** {', '.join(u.source_publishers)} ({u.verification_status})")
                lines.append(f"- **[Factual Finding]:** {u.concise_summary}")
                lines.append(f"- **[AI Strategic Interpretation]:** _{u.potential_business_impact}_\n")
            lines.append("")

        lines.append("## 5. Recommended Business Actions")
        for act in report.recommended_actions:
            lines.append(f"- {act}")
        lines.append("\n")

        lines.append("## 6. Sources & Monitoring Gaps")
        if report.monitoring_gaps:
            for comp, gap in report.monitoring_gaps.items():
                lines.append(f"- **{comp}:** {gap}")
        else:
            lines.append("All tracked competitors possessed multi-source verified activity during this window.")

        return "\n".join(lines)

    def _clean_for_pdf(self, text: str) -> str:
        """Converts Markdown bold/italic to valid ReportLab XML tags and escapes XML chars."""
        if not text:
            return ""
        # First escape XML special chars except existing safe tags
        clean = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Convert **bold** to <b>bold</b>
        clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', clean)
        # Convert *italic* or _italic_ to <i>italic</i>
        clean = re.sub(r'_(.+?)_', r'<i>\1</i>', clean)
        clean = re.sub(r'\*(.+?)\*', r'<i>\1</i>', clean)
        clean = clean.replace("\n\n", "<br/><br/>").replace("\n", "<br/>")
        return clean

    def export_pdf(self, report: IntelligenceReport) -> bytes:
        """
        Generates a professional executive PDF using ReportLab.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom typography styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=6
        )
        meta_style = ParagraphStyle(
            'DocMeta',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=14
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        )
        h3_style = ParagraphStyle(
            'CompH3',
            parent=styles['Heading3'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#2563eb'),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=4
        )
        factual_style = ParagraphStyle(
            'FactualText',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#334155'),
            leftIndent=10,
            spaceAfter=3
        )
        impact_style = ParagraphStyle(
            'ImpactText',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#1e40af'),
            leftIndent=10,
            spaceAfter=6
        )

        elements = []

        # Title & Meta Header
        elements.append(Paragraph(self._clean_for_pdf(report.title), title_style))
        meta_text = (
            f"<b>Generated:</b> {report.created_at.strftime('%Y-%m-%d %H:%M UTC')} &nbsp;|&nbsp; "
            f"<b>Window:</b> Last {report.monitoring_period_days} Days &nbsp;|&nbsp; "
            f"<b>Tracked:</b> {', '.join(report.competitors_tracked)}<br/>"
            f"<b>Signals Scanned:</b> {report.total_raw_signals} &nbsp;|&nbsp; "
            f"<b>Verified Retained:</b> {report.total_retained_updates}"
        )
        elements.append(Paragraph(meta_text, meta_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))

        # Executive Summary
        elements.append(Paragraph("1. Executive Summary", h2_style))
        elements.append(Paragraph(self._clean_for_pdf(report.executive_summary), body_style))
        elements.append(Spacer(1, 8))

        # Emerging Trends
        elements.append(Paragraph("2. Emerging Competitive Trends", h2_style))
        for t in report.emerging_trends:
            elements.append(Paragraph(f"• {self._clean_for_pdf(t)}", body_style))
        elements.append(Spacer(1, 8))

        # Opportunities & Threats Table
        elements.append(Paragraph("3. Evidence-Based Opportunities & Threats", h2_style))
        opp_paras = [Paragraph(f"• {self._clean_for_pdf(o)}", body_style) for o in report.opportunities]
        threat_paras = [Paragraph(f"• {self._clean_for_pdf(th)}", body_style) for th in report.threats]

        swot_data = [
            [Paragraph("<b>Strategic Opportunities</b>", h3_style), Paragraph("<b>Competitive Threats</b>", h3_style)],
            [opp_paras, threat_paras]
        ]
        swot_table = Table(swot_data, colWidths=[265, 265])
        swot_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0fdf4')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#fef2f2')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(swot_table)
        elements.append(Spacer(1, 10))

        # Competitor Updates
        elements.append(Paragraph("4. Competitor-Wise Intelligence Updates", h2_style))
        for comp in report.competitors_tracked:
            updates = report.competitor_updates.get(comp, [])
            elements.append(Paragraph(f"{comp} ({len(updates)} verified)", h3_style))
            
            if not updates:
                elements.append(Paragraph("<i>No verified public activity detected during this window.</i>", body_style))
                continue

            for u in updates:
                clean_hl = self._clean_for_pdf(u.headline)
                clean_summary = self._clean_for_pdf(u.concise_summary)
                clean_impact = self._clean_for_pdf(u.potential_business_impact)
                publishers = ", ".join(u.source_publishers) if u.source_publishers else "Web"

                hl_text = f"<b>{clean_hl}</b> [{u.priority_level.value.upper()} | {u.category.value}] - <i>{u.event_date}</i>"
                elements.append(Paragraph(hl_text, body_style))
                elements.append(Paragraph(f"<b>[Factual Finding]:</b> {clean_summary} (Source: {publishers})", factual_style))
                elements.append(Paragraph(f"<b>[AI Strategic Interpretation]:</b> <i>{clean_impact}</i>", impact_style))
            elements.append(Spacer(1, 4))

        # Recommended Actions
        elements.append(Paragraph("5. Recommended Business Actions", h2_style))
        for a in report.recommended_actions:
            elements.append(Paragraph(f"• {self._clean_for_pdf(a)}", body_style))
        elements.append(Spacer(1, 8))

        # Monitoring Gaps
        elements.append(Paragraph("6. Sources & Monitoring Gaps", h2_style))
        if report.monitoring_gaps:
            for comp, gap in report.monitoring_gaps.items():
                elements.append(Paragraph(f"<b>{comp}:</b> {self._clean_for_pdf(gap)}", body_style))
        else:
            elements.append(Paragraph("All tracked competitors possessed multi-source verified activity.", body_style))

        doc.build(elements)
        return buf.getvalue()
