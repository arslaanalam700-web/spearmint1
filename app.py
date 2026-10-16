"""
app.py - AI Competitor Watch Agent (Professional Streamlit Dashboard)
A modern, corporate-grade executive intelligence platform.
Features:
- Enterprise color palette (Slate, Navy, Neutral Grays)
- Strict typography without informal emojis
- Robust 5-10 competitor validation
- 7, 14, 30 days monitoring window
- Real-time search retrieval (Google News RSS + Hacker News) and offline demo mode
- Clean distinction: [Factual Finding] vs [AI Strategic Interpretation]
- Executive Plotly visualizations
- PDF (ReportLab), CSV, Markdown, and JSON export center
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from agent import CompetitorWatchAgent
from search import RawArticle
from processing import CategoryEnum, PriorityLevel, RetainedUpdate
from reporting import IntelligenceReport, ReportGenerator

# Page Configuration
st.set_page_config(
    page_title="AI Competitor Watch Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Executive Styling (Subtle corporate slate palette, clean borders, professional tags)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main .block-container {
        max-width: 1240px;
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    .header-container {
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.025em;
        margin: 0 0 0.35rem 0;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #475569;
        margin: 0;
        line-height: 1.5;
    }
    .stat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.9rem 1rem;
        border-top: 3px solid #2563eb;
    }
    .stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    .card-update {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    }
    .badge-critical {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fee2e2;
        padding: 2px 7px;
        border-radius: 3px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-high {
        background-color: #fff7ed;
        color: #9a3412;
        border: 1px solid #ffedd5;
        padding: 2px 7px;
        border-radius: 3px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-medium {
        background-color: #fefce8;
        color: #854d0e;
        border: 1px solid #fef08a;
        padding: 2px 7px;
        border-radius: 3px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-low {
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
        padding: 2px 7px;
        border-radius: 3px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-cat {
        background-color: #f1f5f9;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        padding: 2px 7px;
        border-radius: 3px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-verification {
        background-color: #f8fafc;
        color: #64748b;
        border: 1px solid #e2e8f0;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    .factual-callout {
        background: #f8fafc;
        border-left: 3px solid #64748b;
        border-radius: 0 4px 4px 0;
        padding: 0.55rem 0.85rem;
        font-size: 0.88rem;
        color: #1e293b;
        margin-top: 0.6rem;
    }
    .impact-callout {
        background: #f0f7ff;
        border-left: 3px solid #2563eb;
        border-radius: 0 4px 4px 0;
        padding: 0.55rem 0.85rem;
        font-size: 0.88rem;
        color: #1e3a8a;
        margin-top: 0.45rem;
    }
    .demo-notice {
        background-color: #fefce8;
        color: #854d0e;
        border: 1px solid #fef08a;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin-bottom: 1.25rem;
        font-size: 0.88rem;
    }
    .meta-tag {
        font-size: 0.8rem;
        color: #64748b;
    }
    .article-title-link {
        color: #0f172a;
        text-decoration: none;
        font-weight: 600;
        font-size: 1.05rem;
    }
    .article-title-link:hover {
        color: #2563eb;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Curated Industry Presets (Guaranteed 5-6 competitors each)
PRESETS = {
    "Frontier AI Labs": [
        "OpenAI",
        "Anthropic",
        "Google DeepMind",
        "Mistral AI",
        "Meta AI",
        "xAI"
    ],
    "AI Code Assistants": [
        "Cursor",
        "GitHub Copilot",
        "Replit",
        "Cognition AI",
        "Tabnine",
        "Windsurf"
    ],
    "AI Search & Productivity": [
        "Perplexity AI",
        "Cohere",
        "Glean",
        "Notion AI",
        "You.com"
    ],
    "Enterprise AI & Cloud Infrastructure": [
        "Databricks",
        "Snowflake",
        "Scale AI",
        "Hugging Face",
        "Together AI"
    ]
}


def main():
    # Header Section
    st.markdown("""
    <div class="header-container">
        <h1 class="main-title">AI Competitor Watch Agent</h1>
        <p class="sub-title">
            Autonomous competitive intelligence platform for tracking verified public market updates across 5–10 entities. 
            Automates multi-source ingestion, duplicate consolidation, 7-category taxonomy assignment, and executive brief synthesis.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # State Initialization
    if "report" not in st.session_state:
        st.session_state.report = None
    if "agent" not in st.session_state:
        st.session_state.agent = CompetitorWatchAgent()

    # Sidebar Controls
    with st.sidebar:
        st.subheader("Configuration")

        # Preset selection
        preset_choice = st.selectbox(
            "Industry Preset",
            list(PRESETS.keys()) + ["Custom Competitor List"],
            index=0
        )

        if preset_choice != "Custom Competitor List":
            default_list = PRESETS[preset_choice]
            competitors_input = st.multiselect(
                "Tracked Entities (5–10 required)",
                options=list(set(default_list + [
                    "OpenAI", "Anthropic", "Google DeepMind", "Mistral AI",
                    "Meta AI", "Cursor", "Perplexity AI", "Cohere", "Databricks", "Replit"
                ])),
                default=default_list,
                help="Select between 5 and 10 competitor companies or products."
            )
        else:
            custom_text = st.text_area(
                "Competitor Names (comma-separated)",
                value="OpenAI, Anthropic, Cursor, Perplexity AI, Mistral AI",
                help="Enter 5 to 10 comma-separated competitor names."
            )
            competitors_input = [c.strip() for c in custom_text.split(",") if c.strip()]

        comp_count = len(competitors_input)
        if 5 <= comp_count <= 10:
            st.caption(f"Status: **{comp_count} entities configured** (Compliant)")
        else:
            st.caption(f"Status: **{comp_count} entities configured** (Must be 5 to 10)")

        st.markdown("---")

        # Monitoring Window
        period_days = st.radio(
            "Monitoring Window",
            options=[7, 14, 30],
            index=1,
            format_func=lambda x: f"Last {x} Days",
            horizontal=True
        )

        # Retrieval Mode
        retrieval_mode = st.radio(
            "Retrieval Mode",
            options=["Live Web Intelligence", "Offline Benchmark Mode"],
            index=0,
            help="Live Web Intelligence queries real-time Google News RSS and Hacker News. Offline Benchmark Mode loads explicitly labeled test records."
        )
        use_sample = (retrieval_mode == "Offline Benchmark Mode")

        # Optional LLM Key
        with st.expander("Advanced LLM Settings", expanded=False):
            gemini_key = st.text_input(
                "Gemini API Key",
                type="password",
                value=os.environ.get("GEMINI_API_KEY", ""),
                help="Optional. Leave blank to run deterministic NLP analysis with zero external token requirements."
            )

        st.markdown("---")
        run_clicked = st.button("Execute Analysis", type="primary", use_container_width=True)

    # Validation on Trigger
    if run_clicked:
        is_valid, err_msg, cleaned_comps = CompetitorWatchAgent.validate_inputs(competitors_input, period_days)
        if not is_valid:
            st.error(f"Input Validation Error: {err_msg}")
            return

        progress_bar = st.progress(0.0)
        status_box = st.empty()

        def update_progress(msg: str, frac: float):
            status_box.info(msg)
            progress_bar.progress(frac)

        try:
            agent = CompetitorWatchAgent(gemini_api_key=gemini_key if gemini_key else None)
            report = agent.run_pipeline(
                competitors=cleaned_comps,
                days=period_days,
                force_sample_data=use_sample,
                progress_callback=update_progress
            )
            st.session_state.report = report
            st.session_state.agent = agent
            status_box.success("Research pipeline execution completed successfully.")
            progress_bar.empty()
        except Exception as e:
            status_box.error(f"Pipeline execution encountered an error: {str(e)}")
            return

    report = st.session_state.report

    # Empty State Display
    if not report:
        st.info("Select target competitors in the configuration sidebar and click **Execute Analysis** to generate the intelligence brief.")
        
        st.markdown("### Research Pipeline Architecture")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-label">Phase 1</div>
                <div style="font-weight:600; color:#0f172a; margin-bottom:4px;">Multi-Source Ingestion</div>
                <div style="font-size:0.83rem; color:#475569;">Queries Google News RSS and Hacker News Algolia in parallel threads.</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-label">Phase 2</div>
                <div style="font-weight:600; color:#0f172a; margin-bottom:4px;">Cleansing & Deduplication</div>
                <div style="font-size:0.83rem; color:#475569;">Filters stock noise, validates timestamps, and clusters duplicate press coverage.</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-label">Phase 3</div>
                <div style="font-weight:600; color:#0f172a; margin-bottom:4px;">7-Category Taxonomy</div>
                <div style="font-size:0.83rem; color:#475569;">Assigns official category, priority level, and strategic business impact.</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-label">Phase 4</div>
                <div style="font-weight:600; color:#0f172a; margin-bottom:4px;">Executive Briefing</div>
                <div style="font-size:0.83rem; color:#475569;">Synthesizes macro trends, SWOT matrices, and multi-format exports.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("### Available Industry Presets")
        cols = st.columns(2)
        idx = 0
        for name, comps in PRESETS.items():
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"**{name}**")
                    st.write(", ".join(comps))
            idx += 1
        return

    # Banner for Benchmark Mode
    if report.is_demo_mode:
        st.markdown(
            '<div class="demo-notice">'
            '<b>Notice: Offline Benchmark Mode Active.</b> Displaying representative benchmark records for technical review. '
            'Switch to <i>Live Web Intelligence</i> in the sidebar to stream real-time web announcements.'
            '</div>',
            unsafe_allow_html=True
        )

    # Executive Summary Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Tracked Entities</div>
            <div class="stat-value">{len(report.competitors_tracked)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Signals Scanned</div>
            <div class="stat-value">{report.total_raw_signals}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Verified Retained</div>
            <div class="stat-value">{report.total_retained_updates}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        noise_pct = 0
        if report.total_raw_signals > 0:
            noise_pct = int(((report.total_raw_signals - report.total_retained_updates) / report.total_raw_signals) * 100)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Noise Filtered</div>
            <div class="stat-value">{noise_pct}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Monitoring Window</div>
            <div class="stat-value">{report.monitoring_period_days} Days</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Dashboard Tabs
    tab_report, tab_matrix, tab_feed, tab_export = st.tabs([
        "Executive Summary",
        "Activity Matrix & Analytics",
        "Intelligence Feed",
        "Export Reports"
    ])

    # TAB 1: EXECUTIVE SUMMARY
    with tab_report:
        st.markdown("### Executive Summary")
        st.markdown(report.executive_summary)

        st.markdown("---")
        st.markdown("### Emerging Competitive Trends")
        for trend in report.emerging_trends:
            st.markdown(f"- {trend}")

        st.markdown("---")
        st.markdown("### Evidence-Based Opportunities & Threats")
        col_opp, col_thr = st.columns(2)
        with col_opp:
            st.markdown("#### Strategic Opportunities")
            for opp in report.opportunities:
                st.markdown(f"- {opp}")
        with col_thr:
            st.markdown("#### Competitive Threats")
            for thr in report.threats:
                st.markdown(f"- {thr}")

        st.markdown("---")
        st.markdown("### Recommended Business Actions")
        for rec in report.recommended_actions:
            st.markdown(f"- {rec}")

        st.markdown("---")
        st.markdown("### Sources & Monitoring Gaps")
        if report.monitoring_gaps:
            for comp, gap in report.monitoring_gaps.items():
                st.warning(f"**{comp}:** {gap}")
        else:
            st.success("All monitored competitors possessed multi-source verified activity during this window.")

    # TAB 2: ACTIVITY MATRIX & ANALYTICS
    with tab_matrix:
        st.markdown("### Competitive Activity Matrix")
        
        all_cats = [c.value for c in CategoryEnum]
        rows = []
        for comp in report.competitors_tracked:
            comp_updates = report.competitor_updates.get(comp, [])
            cat_counts = {cat: 0 for cat in all_cats}
            for u in comp_updates:
                cat_counts[u.category.value] = cat_counts.get(u.category.value, 0) + 1
            row = {"Competitor": comp}
            row.update(cat_counts)
            row["Total Verified"] = len(comp_updates)
            rows.append(row)

        df_matrix = pd.DataFrame(rows)
        st.dataframe(df_matrix, use_container_width=True)

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### Activity by Competitor & Category")
            melted = df_matrix.melt(
                id_vars=["Competitor"],
                value_vars=all_cats,
                var_name="Category",
                value_name="Count"
            )
            # Enterprise Slate Palette for Plotly
            fig_bar = px.bar(
                melted,
                x="Competitor",
                y="Count",
                color="Category",
                barmode="stack",
                color_discrete_sequence=[
                    "#1e3a8a", "#2563eb", "#0284c7", "#0d9488", "#475569", "#64748b", "#94a3b8", "#cbd5e1"
                ]
            )
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11, color="#334155"),
                margin=dict(l=20, r=20, t=30, b=20),
                height=360,
                legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_c2:
            st.markdown("#### Priority Level Distribution")
            p_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for u_list in report.competitor_updates.values():
                for u in u_list:
                    p_counts[u.priority_level.value] = p_counts.get(u.priority_level.value, 0) + 1

            df_p = pd.DataFrame(list(p_counts.items()), columns=["Priority", "Count"])
            fig_pie = px.pie(
                df_p,
                names="Priority",
                values="Count",
                hole=0.5,
                color="Priority",
                color_discrete_map={
                    "Critical": "#991b1b",
                    "High": "#ea580c",
                    "Medium": "#d97706",
                    "Low": "#64748b"
                }
            )
            fig_pie.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11, color="#334155"),
                margin=dict(l=20, r=20, t=30, b=20),
                height=360,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # TAB 3: INTELLIGENCE FEED
    with tab_feed:
        st.markdown("### Intelligence Feed")
        
        # Filter controls
        f1, f2, f3 = st.columns(3)
        with f1:
            filter_comp = st.selectbox("Competitor", ["All Competitors"] + report.competitors_tracked)
        with f2:
            filter_cat = st.selectbox("Category", ["All Categories"] + [c.value for c in CategoryEnum])
        with f3:
            filter_prio = st.selectbox("Priority Level", ["All Priorities", "Critical", "High", "Medium", "Low"])

        search_kw = st.text_input("Filter updates by keyword...", "")

        # Collect and filter updates
        all_updates = []
        for comp, u_list in report.competitor_updates.items():
            all_updates.extend(u_list)

        filtered = all_updates
        if filter_comp != "All Competitors":
            filtered = [u for u in filtered if u.company == filter_comp]
        if filter_cat != "All Categories":
            filtered = [u for u in filtered if u.category.value == filter_cat]
        if filter_prio != "All Priorities":
            filtered = [u for u in filtered if u.priority_level.value == filter_prio]
        if search_kw:
            q = search_kw.lower()
            filtered = [
                u for u in filtered
                if q in u.headline.lower() or q in u.concise_summary.lower() or q in u.potential_business_impact.lower()
            ]

        st.caption(f"Showing **{len(filtered)}** verified announcements")

        if not filtered:
            st.info("No updates match the selected filter criteria.")

        for u in filtered:
            p_class = f"badge-{u.priority_level.value.lower()}"
            publishers_str = ", ".join(u.source_publishers) if u.source_publishers else "Web Source"
            
            # Clickable Citations
            citations_html = ", ".join([f"<a href='{c}' target='_blank' style='color:#2563eb;'>Source Link</a>" for c in u.all_citations[:3]])

            st.markdown(f"""
            <div class="card-update">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div>
                        <span class="badge-cat">{u.category.value}</span>
                        <span class="{p_class}">{u.priority_level.value.upper()}</span>
                        <span class="badge-verification">{u.verification_status}</span>
                        <strong style="margin-left: 8px; font-size: 1.0rem; color: #0f172a;">{u.company}</strong>
                    </div>
                    <span class="meta-tag">{u.event_date}</span>
                </div>
                <div style="margin: 6px 0 4px 0;">
                    <a href="{u.source_url}" target="_blank" class="article-title-link">{u.headline}</a>
                </div>
                <div class="factual-callout">
                    <b>[Factual Finding]:</b> {u.concise_summary}
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                        Publisher: <b>{publishers_str}</b>
                    </div>
                </div>
                <div class="impact-callout">
                    <b>[AI Strategic Interpretation]:</b> {u.potential_business_impact}
                </div>
                <div style="margin-top: 8px; font-size: 0.82rem; color: #64748b;">
                    Citations: {citations_html if citations_html else '<a href=\"' + u.source_url + '\" target=\"_blank\" style=\"color:#2563eb;\">Primary URL</a>'}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # TAB 4: EXPORT CENTER
    with tab_export:
        st.markdown("### Export Reports")
        st.write("Generate and download formal intelligence reports across multiple file formats.")

        csv_data = st.session_state.agent.reporter.export_csv(report)
        pdf_bytes = st.session_state.agent.reporter.export_pdf(report)
        md_data = st.session_state.agent.reporter.export_markdown(report)
        json_data = report.model_dump_json(indent=2)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")

        e1, e2, e3, e4 = st.columns(4)
        with e1:
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"intelligence_brief_{timestamp_str}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with e2:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"competitor_updates_{timestamp_str}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with e3:
            st.download_button(
                label="Download Markdown",
                data=md_data,
                file_name=f"intelligence_brief_{timestamp_str}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with e4:
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"intelligence_report_{timestamp_str}.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("---")
        with st.expander("Preview Markdown Content", expanded=False):
            st.text_area("Markdown Report", value=md_data, height=380)


if __name__ == "__main__":
    main()
