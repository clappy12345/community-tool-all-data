import streamlit as st

st.set_page_config(page_title="Platform Breakdown", page_icon="📱", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.processors import (
    apply_filters,
    get_platform_summary,
    format_number,
)
from utils.charts import (
    platform_bar,
    platform_share_pie,
    daily_platform_lines,
    CHART_CONFIG,
    PLATFORM_COLORS,
)
from utils.theme import render_section_header, render_platform_card

filters = render_sidebar()
apply_theme()
require_data()

st.title("📱 Platform Breakdown")
st.markdown("*Cross-platform comparison and audience trends*")
st.divider()

prof_raw = st.session_state.get("profile_performance")
pp = apply_filters(st.session_state["post_performance"], filters)

if prof_raw is None:
    st.warning("Upload Profile Performance data for full platform analysis.")
    st.stop()

prof = apply_filters(prof_raw, filters)

# --- Platform Summary ---
render_section_header("Platform Summary")
platform = get_platform_summary(prof)

cols = st.columns(len(platform))
for i, (_, row) in enumerate(platform.iterrows()):
    with cols[i]:
        color = PLATFORM_COLORS.get(row["Network"], "#00B4D8")
        render_platform_card(
            network=row["Network"],
            audience=format_number(row.get("Audience", 0)),
            growth=format_number(row["Net Audience Growth"]),
            color=color,
        )

st.divider()

# --- Share of Voice ---
render_section_header("Share of Voice")
col1, col2 = st.columns(2)
with col1:
    fig = platform_share_pie(platform, "Impressions", "Share of Impressions")
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
with col2:
    fig = platform_share_pie(platform, "Engagements", "Share of Engagements")
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.divider()

# --- Engagement Rate by Platform ---
render_section_header("Engagement Rate by Platform")
fig = platform_bar(platform, "Engagement Rate", "Engagement Rate by Platform (%)")
st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.divider()

# --- Daily Trends ---
render_section_header("Daily Trends by Platform")
metric_choice = st.selectbox(
    "Metric", ["Impressions", "Engagements", "Video Views", "Net Audience Growth"]
)

fig = daily_platform_lines(prof, metric_choice, f"Daily {metric_choice} by Platform")
st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.divider()

# --- Audience Growth Over Time ---
render_section_header("Cumulative Audience Growth")
import plotly.graph_objects as go
from utils.charts import apply_dark_theme

cumulative = prof.copy()
cumulative = cumulative.sort_values("Date")

fig = go.Figure()
for network in sorted(cumulative["Network"].unique()):
    ndf = cumulative[cumulative["Network"] == network].sort_values("Date")
    ndf["Cumulative"] = ndf["Net Audience Growth"].cumsum()
    fig.add_trace(
        go.Scatter(
            x=ndf["Date"],
            y=ndf["Cumulative"],
            mode="lines",
            name=network,
            line=dict(color=PLATFORM_COLORS.get(network, "#00B4D8"), width=2),
        )
    )
fig.update_layout(title="Cumulative Audience Growth by Platform", yaxis_title="Net Growth")
fig = apply_dark_theme(fig)
st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.divider()

# --- Detailed Platform Table ---
render_section_header("Detailed Metrics")
st.dataframe(
    platform[["Network", "Audience", "Net Audience Growth", "Impressions", "Engagements", "Engagement Rate", "Video Views"]]
    .sort_values("Engagements", ascending=False)
    .style.format(
        {
            "Audience": "{:,.0f}",
            "Net Audience Growth": "{:+,.0f}",
            "Impressions": "{:,.0f}",
            "Engagements": "{:,.0f}",
            "Engagement Rate": "{:.2f}%",
            "Video Views": "{:,.0f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

csv = platform.to_csv(index=False)
st.download_button(
    "Download Platform Data (CSV)", csv, "platform_breakdown.csv", "text/csv", use_container_width=True
)
