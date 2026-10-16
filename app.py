"""
app.py - AI Competitor Watch Agent (Streamlit Dashboard)
A professional, deployment-ready competitive intelligence dashboard.
Features:
- 5-10 competitor input validation
- 7, 14, 30 days monitoring window
- Live search retrieval (Google News RSS + Hacker News) and explicit demo mode
- Intelligent deduplication, 7-category taxonomy, priority classification
- Executive brief with factual vs AI interpretation distinction
- Interactive Plotly analytics
- Multi-format exports: PDF (ReportLab), CSV, Markdown, JSON
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
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Styling
st.markdown("""
<style>
    .reportview-container .main .block-container {
        max-width: 1200px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 1.2rem;
        line-height: 1.5;
    }
    .metric-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        text-align: center;
    }
    .card-update {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .badge-critical {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #fecaca;
    }
    .badge-high {
        background-color: #ffedd5;
        color: #9a3412;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid #fed7aa;
    }
    .badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid #fde68a;
    }
    .badge-low {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid #bae6fd;
    }
    .badge-cat {
        background-color: #f1f5f9;
        color: #334155;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .factual-box {
        background: #f8fafc;
        border-left: 3px solid #64748b;
        padding: 0.5rem 0.8rem;
        font-size: 0.9rem;
        color: #1e293b;
        margin-top: 0.5rem;
        border-radius: 0 4px 4px 0;
    }
    .impact-box {
        background: #eff6ff;
        border-left: 3px solid #2563eb;
        padding: 0.5rem 0.8rem;
        font-size: 0.9rem;
        color: #1e40af;
        margin-top: 0.4rem;
        border-radius: 0 4px 4px 0;
    }
    .demo-banner {
        background-color: #fffbeb;
        color: #92400e;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        border: 1px solid #fde68a;
        margin-bottom: 1rem;
        font-size: 0.92rem;
    }
</style>
""", unsafe_allow_html=True)

# Curated Industry Presets (guaranteed 5-6 competitors each)
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
    "AI Search & Workspace": [
        "Perplexity AI",
        "Cohere",
        "Glean",
        "Notion AI",
        "You.com"
    ],
    "Enterprise AI & Cloud": [
        "Databricks",
        "Snowflake",
        "Scale AI",
        "Hugging Face",
        "Together AI"
    ]
}


def main():
    # Header
    st.markdown('<div class="main-title">🛡️ AI Competitor Watch Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">'
        'Autonomous market intelligence system: retrieves verified public updates across 5–10 competitors, '
        'filters noise, dedupes multi-source coverage, categorizes business moves, and synthesizes an executive brief.'
        '</div>',
        unsafe_allow_html=True
    )

    # Initialize Session State
    if "report" not in st.session_state:
        st.session_state.report = None
    if "agent" not in st.session_state:
        st.session_state.agent = CompetitorWatchAgent()

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Agent Configuration")

        # Preset selection
        preset_choice = st.selectbox(
            "Select Industry Preset",
            list(PRESETS.keys()) + ["Custom Competitor List"],
            index=0
        )

        if preset_choice != "Custom Competitor List":
            default_list = PRESETS[preset_choice]
            competitors_input = st.multiselect(
                "Tracked Competitors (5–10 required)",
                options=list(set(default_list + [
                    "OpenAI", "Anthropic", "Google DeepMind", "Mistral AI",
                    "Meta AI", "Cursor", "Perplexity AI", "Cohere", "Databricks", "Replit"
                ])),
                default=default_list,
                help="Select between 5 and 10 competitor companies or products."
            )
        else:
            custom_text = st.text_area(
                "Enter 5–10 Competitor Names (comma-separated)",
                value="OpenAI, Anthropic, Cursor, Perplexity AI, Mistral AI",
                help="Comma-separated list of competitor companies or products."
            )
            competitors_input = [c.strip() for c in custom_text.split(",") if c.strip()]

        comp_count = len(competitors_input)
        if 5 <= comp_count <= 10:
            st.caption(f"✅ Target Count: **{comp_count} competitors** (Valid)")
        else:
            st.caption(f"⚠️ Target Count: **{comp_count} competitors** (Must be 5–10)")

        st.markdown("---")

        # Period Filter
        period_days = st.radio(
            "📅 Monitoring Window",
            options=[7, 14, 30],
            index=1,
            format_func=lambda x: f"Last {x} Days",
            horizontal=True
        )

        # Retrieval Mode
        retrieval_mode = st.radio(
            "📡 Retrieval Mode",
            options=["Live Web Intelligence", "Offline Demo Benchmark"],
            index=0,
            help="Live Web Intelligence queries real-time Google News RSS & Hacker News. Offline Demo Benchmark displays pre-curated test records."
        )
        use_sample = (retrieval_mode == "Offline Demo Benchmark")

        # Optional LLM API Key
        with st.expander("🔑 Optional LLM Settings", expanded=False):
            gemini_key = st.text_input(
                "Gemini API Key",
                type="password",
                value=os.environ.get("GEMINI_API_KEY", ""),
                help="Optional. If left blank, deterministic NLP heuristics are used with zero downtime."
            )

        st.markdown("---")
        run_clicked = st.button("🚀 Run Competitor Watch Agent", type="primary", use_container_width=True)

    # Validation on Click
    if run_clicked:
        is_valid, err_msg, cleaned_comps = CompetitorWatchAgent.validate_inputs(competitors_input, period_days)
        if not is_valid:
            st.error(f"❌ Input Validation Error: {err_msg}")
            return

        progress_bar = st.progress(0.0)
        status_box = st.empty()

        def update_progress(msg: str, frac: float):
            status_box.info(f"⏳ {msg}")
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
            status_box.success("✅ Intelligence Research Pipeline Completed!")
            progress_bar.empty()
        except Exception as e:
            status_box.error(f"❌ Pipeline Failed: {str(e)}")
            return

    report = st.session_state.report

    # Empty State
    if not report:
        st.info("👈 Select your target competitors in the sidebar and click **'Run Competitor Watch Agent'** to generate your intelligence brief.")
        
        st.subheader("💡 What the Agent Performs")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("#### 1. Ingestion")
            st.write("Searches Google News RSS and Hacker News Algolia for real-time announcements.")
        with c2:
            st.markdown("#### 2. Cleansing")
            st.write("Filters out stock spam, validates publication dates, and dedupes syndicated coverage.")
        with c3:
            st.markdown("#### 3. Classification")
            st.write("Categorizes moves into 7 key verticals, scoring Priority and Potential Business Impact.")
        with c4:
            st.markdown("#### 4. Briefing")
            st.write("Synthesizes executive findings, macro trends, and exports to PDF, CSV, and Markdown.")

        st.markdown("---")
        st.subheader("📌 Industry Presets Available")
        cols = st.columns(2)
        idx = 0
        for name, comps in PRESETS.items():
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"**{name}**")
                    st.write(", ".join(comps))
            idx += 1
        return

    # Banner for Demo Mode
    if report.is_demo_mode:
        st.markdown(
            '<div class="demo-banner">'
            '⚠️ <b>DEMO BENCHMARK MODE ACTIVE:</b> Currently displaying representative benchmark records for offline technical evaluation. '
            'Switch to <i>Live Web Intelligence</i> in the sidebar for live real-time coverage.'
            '</div>',
            unsafe_allow_html=True
        )

    # Top KPI Metrics Bar
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Tracked Competitors", len(report.competitors_tracked))
    with m2:
        st.metric("Raw Signals Scanned", report.total_raw_signals)
    with m3:
        st.metric("Verified Retained", report.total_retained_updates)
    with m4:
        noise_pct = 0
        if report.total_raw_signals > 0:
            noise_pct = int(((report.total_raw_signals - report.total_retained_updates) / report.total_raw_signals) * 100)
        st.metric("Noise Filtered", f"{noise_pct}%")
    with m5:
        st.metric("Period Window", f"{report.monitoring_period_days} Days")

    st.markdown("---")

    # Main Tabs
    tab_report, tab_matrix, tab_feed, tab_export = st.tabs([
        "📋 Executive Intelligence Report",
        "📊 Competitive Activity Matrix",
        "🔍 Granular Updates Feed",
        "📥 Export Center (PDF, CSV, MD)"
    ])

    # TAB 1: EXECUTIVE INTELLIGENCE REPORT
    with tab_report:
        st.subheader("1. Executive Summary")
        st.markdown(report.executive_summary)

        st.markdown("---")
        st.subheader("2. Emerging Competitive Trends")
        for trend in report.emerging_trends:
            st.markdown(f"- {trend}")

        st.markdown("---")
        st.subheader("3. Evidence-Based Opportunities & Threats")
        col_opp, col_thr = st.columns(2)
        with col_opp:
            st.markdown("##### 💡 Strategic Opportunities")
            for opp in report.opportunities:
                st.markdown(f"- {opp}")
        with col_thr:
            st.markdown("##### ⚠️ Competitive Threats")
            for thr in report.threats:
                st.markdown(f"- {thr}")

        st.markdown("---")
        st.subheader("4. Recommended Business Actions")
        for rec in report.recommended_actions:
            st.markdown(f"- {rec}")

        st.markdown("---")
        st.subheader("5. Sources & Monitoring Gaps")
        if report.monitoring_gaps:
            for comp, gap in report.monitoring_gaps.items():
                st.warning(f"**{comp}:** {gap}")
        else:
            st.success("All monitored competitors possessed multi-source verified activity during this window.")

    # TAB 2: COMPETITIVE ACTIVITY MATRIX & CHARTS
    with tab_matrix:
        st.subheader("Competitive Activity Matrix")
        
        # Build matrix table
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
            st.markdown("##### Activity by Competitor & Category")
            melted = df_matrix.melt(
                id_vars=["Competitor"],
                value_vars=all_cats,
                var_name="Category",
                value_name="Count"
            )
            fig_bar = px.bar(
                melted,
                x="Competitor",
                y="Count",
                color="Category",
                barmode="stack",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_bar.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=380)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_c2:
            st.markdown("##### Priority Level Distribution")
            p_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for u_list in report.competitor_updates.values():
                for u in u_list:
                    p_counts[u.priority_level.value] = p_counts.get(u.priority_level.value, 0) + 1

            df_p = pd.DataFrame(list(p_counts.items()), columns=["Priority", "Count"])
            fig_pie = px.pie(
                df_p,
                names="Priority",
                values="Count",
                hole=0.45,
                color="Priority",
                color_discrete_map={
                    "Critical": "#dc2626",
                    "High": "#ea580c",
                    "Medium": "#d97706",
                    "Low": "#2563eb"
                }
            )
            fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=380)
            st.plotly_chart(fig_pie, use_container_width=True)

    # TAB 3: GRANULAR UPDATES FEED
    with tab_feed:
        st.subheader("Granular Updates Feed")
        
        # Interactive Filter Bar
        f1, f2, f3 = st.columns(3)
        with f1:
            filter_comp = st.selectbox("Filter by Competitor", ["All"] + report.competitors_tracked)
        with f2:
            filter_cat = st.selectbox("Filter by Category", ["All"] + [c.value for c in CategoryEnum])
        with f3:
            filter_prio = st.selectbox("Filter by Priority", ["All", "Critical", "High", "Medium", "Low"])

        search_kw = st.text_input("🔍 Search update keywords...", "")

        # Collect and filter updates
        all_updates: List[RetainedUpdate] = []
        for comp, u_list in report.competitor_updates.items():
            all_updates.extend(u_list)

        filtered = all_updates
        if filter_comp != "All":
            filtered = [u for u in filtered if u.company == filter_comp]
        if filter_cat != "All":
            filtered = [u for u in filtered if u.category.value == filter_cat]
        if filter_prio != "All":
            filtered = [u for u in filtered if u.priority_level.value == filter_prio]
        if search_kw:
            q = search_kw.lower()
            filtered = [
                u for u in filtered
                if q in u.headline.lower() or q in u.concise_summary.lower() or q in u.potential_business_impact.lower()
            ]

        st.caption(f"Displaying **{len(filtered)}** verified updates")

        if not filtered:
            st.info("No updates match the selected filter criteria.")

        for u in filtered:
            p_class = f"badge-{u.priority_level.value.lower()}"
            publishers_str = ", ".join(u.source_publishers) if u.source_publishers else "Web Source"
            
            # Clickable citations
            citations_html = ", ".join([f"<a href='{c}' target='_blank'>[Source]</a>" for c in u.all_citations[:3]])

            st.markdown(f"""
            <div class="card-update">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div>
                        <span class="badge-cat">{u.category.emoji} {u.category.value}</span>
                        <span class="{p_class}">{u.priority_level.value.upper()} PRIORITY</span>
                        <strong style="margin-left: 8px; font-size: 1.05rem; color: #0f172a;">{u.company}</strong>
                    </div>
                    <span style="color: #64748b; font-size: 0.85rem;">{u.event_date}</span>
                </div>
                <h4 style="margin: 6px 0 4px 0;">
                    <a href="{u.source_url}" target="_blank" style="color: #0f172a; text-decoration: none;">{u.headline}</a>
                </h4>
                <div class="factual-box">
                    <strong>[Factual Finding]:</strong> {u.concise_summary}
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                        Reported by: <b>{publishers_str}</b> ({u.verification_status})
                    </div>
                </div>
                <div class="impact-box">
                    <strong>[AI Strategic Interpretation]:</strong> {u.potential_business_impact}
                </div>
                <div style="margin-top: 8px; font-size: 0.82rem; color: #64748b;">
                    Citations: {citations_html if citations_html else 'Direct Link'}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # TAB 4: EXPORT CENTER
    with tab_export:
        st.subheader("📥 Export Intelligence Brief")
        st.write("Export your curated intelligence brief in professional formats for stakeholders and downstream workflows.")

        csv_data = st.session_state.agent.reporter.export_csv(report)
        pdf_bytes = st.session_state.agent.reporter.export_pdf(report)
        md_data = st.session_state.agent.reporter.export_markdown(report)
        json_data = report.model_dump_json(indent=2)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")

        e1, e2, e3, e4 = st.columns(4)
        with e1:
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"intelligence_brief_{timestamp_str}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with e2:
            st.download_button(
                label="📊 Download CSV Data",
                data=csv_data,
                file_name=f"competitor_updates_{timestamp_str}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with e3:
            st.download_button(
                label="📝 Download Markdown",
                data=md_data,
                file_name=f"intelligence_brief_{timestamp_str}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with e4:
            st.download_button(
                label="📦 Download JSON",
                data=json_data,
                file_name=f"intelligence_report_{timestamp_str}.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("---")
        with st.expander("👁️ Preview Raw Markdown Report", expanded=False):
            st.text_area("Markdown Report Content", value=md_data, height=400)


if __name__ == "__main__":
    main()
