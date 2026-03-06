import streamlit as st

st.set_page_config(
    page_title="NHL Community Insights",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.sidebar import render_sidebar
from utils.processors import format_number

# Custom CSS
st.markdown(
    """
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1A1D23 0%, #252830 100%);
        border: 1px solid rgba(0,180,216,0.2);
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00B4D8;
        margin: 0;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #90A4AE;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-card {
        background: #1A1D23;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #00B4D8;
    }
    div[data-testid="stMetric"] {
        background: #1A1D23;
        border-radius: 10px;
        padding: 12px 16px;
    }
</style>
""",
    unsafe_allow_html=True,
)

filters = render_sidebar()

st.title("🏒 NHL Community Insights")
st.markdown("*Social performance and community analysis across Sprout & Affogata*")
st.divider()

has_data = "post_performance" in st.session_state and st.session_state["post_performance"] is not None

if has_data:
    from utils.processors import get_kpis

    pp = st.session_state["post_performance"]
    prof = st.session_state.get("profile_performance")
    aff = st.session_state.get("affogata")
    inbox = st.session_state.get("inbox")

    if prof is not None:
        kpis = get_kpis(pp, prof)
    else:
        kpis = {
            "total_impressions": pp["Impressions"].sum(),
            "total_engagements": pp["Engagements"].sum(),
            "avg_engagement_rate": 0,
            "audience_growth": 0,
            "total_posts": len(pp),
        }

    date_min = pp["Date"].min().strftime("%b %d, %Y")
    date_max = pp["Date"].max().strftime("%b %d, %Y")
    st.markdown(f"### Reporting Period: {date_min} — {date_max}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""<div class="kpi-card">
            <p class="kpi-label">Total Impressions</p>
            <p class="kpi-value">{format_number(kpis['total_impressions'])}</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="kpi-card">
            <p class="kpi-label">Total Engagements</p>
            <p class="kpi-value">{format_number(kpis['total_engagements'])}</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="kpi-card">
            <p class="kpi-label">Avg Engagement Rate</p>
            <p class="kpi-value">{kpis['avg_engagement_rate']:.2f}%</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c4:
        growth = kpis.get("audience_growth", 0)
        st.markdown(
            f"""<div class="kpi-card">
            <p class="kpi-label">Audience Growth</p>
            <p class="kpi-value">{'+' if growth > 0 else ''}{format_number(growth)}</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Second row of KPIs
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("Total Posts", f"{kpis['total_posts']}")
    with c6:
        st.metric("Total Comments", format_number(kpis.get("total_comments", 0)))
    with c7:
        st.metric("Total Shares", format_number(kpis.get("total_shares", 0)))
    with c8:
        vv = kpis.get("total_video_views", pp["Video Views"].sum())
        st.metric("Video Views", format_number(vv))

    st.divider()

    # Quick data summary
    st.markdown("### Data Sources Loaded")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""<div class="status-card">
            <strong>Sprout Social</strong><br>
            {len(pp):,} posts &nbsp;|&nbsp;
            {len(prof) if prof is not None else 0:,} daily profile records<br>
            {len(inbox) if inbox is not None else 0:,} inbox messages
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="status-card">
            <strong>Affogata</strong><br>
            {len(aff) if aff is not None else 0:,} community conversations<br>
            Platforms: {', '.join(sorted(aff['Network Name'].unique())) if aff is not None else 'N/A'}
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.info("Use the sidebar to navigate to analysis pages: **Launch Scorecard**, **Content Performance**, **Platform Breakdown**, **Community Insights**, and **Compare Periods**.")

else:
    st.markdown("### Getting Started")
    st.markdown(
        """
Upload your social data exports using the sidebar to get started. This tool accepts:

1. **Post Performance** (Sprout Social CSV) — individual post metrics
2. **Profile Performance** (Sprout Social CSV) — daily profile-level metrics
3. **Affogata Export** (CSV) — community conversations and sentiment
4. **Inbox Export** (Sprout Social CSV or ZIP) — player messages and comments

All files should cover the same date range for the most accurate analysis.
"""
    )

    st.markdown("---")
    st.markdown(
        """
#### Pages Available After Upload
| Page | What It Shows |
|------|--------------|
| **Launch Scorecard** | KPIs, engagement timeline, top posts, sentiment overview |
| **Content Performance** | Post rankings, content type analysis, theme breakdowns |
| **Platform Breakdown** | Platform comparison, audience growth, share of voice |
| **Community Insights** | AI-powered theme discovery, player voice, sentiment by topic |
| **Compare Periods** | Side-by-side comparison with a second date range |
"""
    )
