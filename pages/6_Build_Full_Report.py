import streamlit as st

st.set_page_config(page_title="Build Full Report", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.titles import get_title_config
from utils.processors import combine_community_messages, format_number, get_kpis_safe
from utils.ai_analysis import (
    build_report_context,
    generate_executive_summary,
    generate_performance_report,
    generate_pos_neg_themes,
    generate_conversation_drivers,
)
from utils.theme import render_section_header, render_quote_card, render_nav_header, POSITIVE, NEGATIVE

filters = render_sidebar()
apply_theme()
require_data()

cfg = get_title_config()
pp = st.session_state["post_performance"]
prof = st.session_state.get("profile_performance")
aff = st.session_state.get("affogata")
inbox = st.session_state.get("inbox")
looker = st.session_state.get("looker_sentiment")

date_min = pp["Date"].min().strftime("%b %d, %Y")
date_max = pp["Date"].max().strftime("%b %d, %Y")

render_nav_header(
    "Build Full Report",
    f"Generate an AI-powered comprehensive report for {cfg['full_name']} ({date_min} — {date_max})",
)
st.markdown("")

has_community = (aff is not None and len(aff) > 0) or (inbox is not None and len(inbox) > 0)

report_keys = ["full_report_exec", "full_report_perf", "full_report_themes", "full_report_drivers"]
report_ready = all(k in st.session_state and st.session_state[k] is not None for k in report_keys[:2])

if not report_ready:
    st.markdown(
        "Click the button below to generate a full AI report covering:\n"
        "- **Executive Summary** — high-level takeaways\n"
        "- **Performance Narrative** — what the numbers say\n"
        "- **Community Coverage Themes** — positive and negative sentiment themes with quotes\n"
        "- **Conversation Drivers** — what the community is talking about and why\n"
    )

col_btn, col_status = st.columns([1, 3])
with col_btn:
    generate = st.button(
        "Generate Full Report" if not report_ready else "Regenerate Report",
        type="primary" if not report_ready else "secondary",
        use_container_width=True,
    )
with col_status:
    if report_ready:
        st.success("Report ready")
    else:
        st.caption("Requires Google API key — generation takes 60-90 seconds")

if generate:
    progress = st.progress(0, text="Building data context...")
    context = build_report_context()

    progress.progress(10, text="Generating executive summary...")
    st.session_state["full_report_exec"] = generate_executive_summary(context)

    progress.progress(30, text="Generating performance narrative...")
    st.session_state["full_report_perf"] = generate_performance_report(context)

    if has_community:
        messages_df = combine_community_messages(aff, inbox)
        if messages_df is not None and len(messages_df) > 0:
            progress.progress(55, text="Identifying positive & negative themes...")
            st.session_state["full_report_themes"] = generate_pos_neg_themes(messages_df)

            progress.progress(75, text="Generating conversation drivers...")
            st.session_state["full_report_drivers"] = generate_conversation_drivers(messages_df)
        else:
            st.session_state["full_report_themes"] = None
            st.session_state["full_report_drivers"] = None
    else:
        st.session_state["full_report_themes"] = None
        st.session_state["full_report_drivers"] = None

    progress.progress(100, text="Done!")
    st.rerun()

# ── Render Report ──────────────────────────────────────────────
if report_ready:
    report_parts = []

    exec_text = st.session_state.get("full_report_exec")
    if exec_text:
        st.markdown("")
        render_section_header("Executive Summary")
        st.markdown(exec_text)
        report_parts.append(f"## Executive Summary\n\n{exec_text}")

    perf_text = st.session_state.get("full_report_perf")
    if perf_text:
        st.markdown("")
        st.markdown(perf_text)
        report_parts.append(perf_text)

    themes_data = st.session_state.get("full_report_themes")
    if themes_data:
        st.markdown("")
        render_section_header("Community Coverage Themes")

        pos_themes = themes_data.get("positive_themes", [])
        neg_themes = themes_data.get("negative_themes", [])
        themes_md = "## Community Coverage Themes\n\n"

        if pos_themes:
            st.markdown("### Positive Themes")
            themes_md += "### Positive Themes\n\n"
            for theme in pos_themes:
                st.markdown(f"**{theme['theme']}** — {theme.get('summary', '')}")
                themes_md += f"**{theme['theme']}** — {theme.get('summary', '')}\n\n"
                quotes = theme.get("quotes", [])
                if quotes:
                    st.markdown("**Notable Quotes:**")
                    themes_md += "**Notable Quotes:**\n\n"
                    for q in quotes:
                        render_quote_card(q, POSITIVE)
                        themes_md += f"- \"{q}\"\n"
                    themes_md += "\n"
                st.markdown("")

        if neg_themes:
            st.markdown("### Critical / Negative Themes")
            themes_md += "### Critical / Negative Themes\n\n"
            for theme in neg_themes:
                st.markdown(f"**{theme['theme']}** — {theme.get('summary', '')}")
                themes_md += f"**{theme['theme']}** — {theme.get('summary', '')}\n\n"
                quotes = theme.get("quotes", [])
                if quotes:
                    st.markdown("**Notable Quotes:**")
                    themes_md += "**Notable Quotes:**\n\n"
                    for q in quotes:
                        render_quote_card(q, NEGATIVE)
                        themes_md += f"- \"{q}\"\n"
                    themes_md += "\n"
                st.markdown("")

        report_parts.append(themes_md)

    drivers_text = st.session_state.get("full_report_drivers")
    if drivers_text:
        st.markdown("")
        st.markdown(drivers_text)
        report_parts.append(drivers_text)

    st.markdown("")
    full_md = "\n\n---\n\n".join(report_parts)
    filename = (
        f"{cfg['name']}_Full_Report_{date_min}_{date_max}.md"
        .replace(" ", "_").replace(",", "")
    )
    st.download_button(
        "Download Full Report (.md)",
        full_md,
        file_name=filename,
        mime="text/markdown",
        use_container_width=True,
    )
