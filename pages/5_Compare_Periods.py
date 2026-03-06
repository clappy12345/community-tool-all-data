import streamlit as st
import pandas as pd

st.set_page_config(page_title="Compare Periods", page_icon="🔄", layout="wide")

from utils.sidebar import render_sidebar, require_data
from utils.data_loader import load_post_performance, load_profile_performance, load_affogata
from utils.processors import get_kpis, get_sentiment_distribution, format_number
from utils.charts import comparison_bar, sentiment_donut, CHART_CONFIG, SENTIMENT_COLORS

filters = render_sidebar()
require_data()

st.title("🔄 Compare Periods")
st.markdown("*Upload a second dataset to compare side-by-side*")
st.divider()

# --- Period A (current data) ---
pp_a = st.session_state["post_performance"]
prof_a = st.session_state.get("profile_performance")
aff_a = st.session_state.get("affogata")

date_a_min = pp_a["Date"].min().strftime("%b %d, %Y")
date_a_max = pp_a["Date"].max().strftime("%b %d, %Y")
label_a = st.text_input("Period A Label", value=f"{date_a_min} — {date_a_max}")

# --- Period B upload ---
st.markdown("### Upload Comparison Data (Period B)")
st.markdown("Upload the same CSV types from a different date range (e.g., NHL 25 launch).")

col1, col2, col3 = st.columns(3)
with col1:
    pp_b_file = st.file_uploader("Post Performance", type=["csv"], key="compare_pp")
with col2:
    prof_b_file = st.file_uploader("Profile Performance", type=["csv"], key="compare_prof")
with col3:
    aff_b_file = st.file_uploader("Affogata Export", type=["csv"], key="compare_aff")

if pp_b_file:
    st.session_state["compare_post_performance"] = load_post_performance(
        pp_b_file.read(), pp_b_file.name
    )
    pp_b_file.seek(0)
if prof_b_file:
    st.session_state["compare_profile_performance"] = load_profile_performance(
        prof_b_file.read(), prof_b_file.name
    )
    prof_b_file.seek(0)
if aff_b_file:
    st.session_state["compare_affogata"] = load_affogata(
        aff_b_file.read(), aff_b_file.name
    )
    aff_b_file.seek(0)

pp_b = st.session_state.get("compare_post_performance")
prof_b = st.session_state.get("compare_profile_performance")
aff_b = st.session_state.get("compare_affogata")

if pp_b is None:
    st.info("Upload Period B data above to see comparisons.")
    st.stop()

date_b_min = pp_b["Date"].min().strftime("%b %d, %Y")
date_b_max = pp_b["Date"].max().strftime("%b %d, %Y")
label_b = st.text_input("Period B Label", value=f"{date_b_min} — {date_b_max}")

st.divider()

# --- Calculate KPIs ---
if prof_a is not None:
    kpis_a = get_kpis(pp_a, prof_a)
else:
    kpis_a = {
        "total_impressions": pp_a["Impressions"].sum(),
        "total_engagements": pp_a["Engagements"].sum(),
        "avg_engagement_rate": 0,
        "audience_growth": 0,
        "total_posts": len(pp_a),
        "total_comments": pp_a["Comments"].sum(),
        "total_shares": pp_a["Shares"].sum(),
        "total_video_views": pp_a["Video Views"].sum(),
    }

if prof_b is not None:
    kpis_b = get_kpis(pp_b, prof_b)
else:
    kpis_b = {
        "total_impressions": pp_b["Impressions"].sum(),
        "total_engagements": pp_b["Engagements"].sum(),
        "avg_engagement_rate": 0,
        "audience_growth": 0,
        "total_posts": len(pp_b),
        "total_comments": pp_b["Comments"].sum(),
        "total_shares": pp_b["Shares"].sum(),
        "total_video_views": pp_b["Video Views"].sum(),
    }

# --- Comparison Cards ---
st.markdown("### Key Metrics Comparison")


def delta_pct(a, b):
    if b == 0:
        return "N/A"
    pct = (a - b) / b * 100
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.1f}%"


def delta_color(a, b):
    if a > b:
        return "#06D6A0"
    elif a < b:
        return "#EF476F"
    return "#FFD166"


metrics_to_compare = [
    ("Total Impressions", "total_impressions"),
    ("Total Engagements", "total_engagements"),
    ("Avg Engagement Rate", "avg_engagement_rate"),
    ("Audience Growth", "audience_growth"),
    ("Total Posts", "total_posts"),
    ("Total Comments", "total_comments"),
]

cols = st.columns(3)
for i, (display_name, key) in enumerate(metrics_to_compare):
    val_a = kpis_a.get(key, 0)
    val_b = kpis_b.get(key, 0)
    delta = delta_pct(val_a, val_b)
    color = delta_color(val_a, val_b)

    is_rate = "rate" in key.lower()
    fmt_a = f"{val_a:.2f}%" if is_rate else format_number(val_a)
    fmt_b = f"{val_b:.2f}%" if is_rate else format_number(val_b)

    with cols[i % 3]:
        st.markdown(
            f"<div style='background:#1A1D23; border-radius:10px; padding:16px; margin:8px 0; "
            f"border-top: 3px solid {color};'>"
            f"<div style='font-size:0.8rem; color:#90A4AE; text-transform:uppercase;'>{display_name}</div>"
            f"<div style='display:flex; justify-content:space-between; align-items:baseline; margin-top:8px;'>"
            f"<div><span style='font-size:0.75rem; color:#90A4AE;'>{label_a[:20]}</span><br>"
            f"<span style='font-size:1.4rem; font-weight:700; color:#00B4D8;'>{fmt_a}</span></div>"
            f"<div style='font-size:1.2rem; font-weight:700; color:{color};'>{delta}</div>"
            f"<div style='text-align:right;'><span style='font-size:0.75rem; color:#90A4AE;'>{label_b[:20]}</span><br>"
            f"<span style='font-size:1.4rem; font-weight:700; color:#90E0EF;'>{fmt_b}</span></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

st.divider()

# --- Visual Comparison ---
st.markdown("### Visual Comparison")

metric_names = ["total_impressions", "total_engagements", "total_posts", "total_comments", "total_shares"]
display_names = ["Impressions", "Engagements", "Posts", "Comments", "Shares"]

fig = comparison_bar(label_a, label_b, kpis_a, kpis_b, metric_names)
fig.update_layout(
    xaxis=dict(
        ticktext=display_names,
        tickvals=metric_names,
    )
)
st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.divider()

# --- Sentiment Comparison ---
st.markdown("### Sentiment Comparison")
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**{label_a}**")
    if aff_a is not None:
        sent_a = get_sentiment_distribution(aff_a)
        fig = sentiment_donut(sent_a, f"Sentiment — {label_a[:25]}")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
    else:
        st.caption("No Affogata data for Period A")

with col2:
    st.markdown(f"**{label_b}**")
    if aff_b is not None:
        sent_b = get_sentiment_distribution(aff_b)
        fig = sentiment_donut(sent_b, f"Sentiment — {label_b[:25]}")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
    else:
        st.caption("No Affogata data for Period B")

st.divider()

# --- Platform Comparison ---
st.markdown("### Platform Comparison")

from utils.processors import get_network_content_performance

net_a = get_network_content_performance(pp_a)
net_b = get_network_content_performance(pp_b)

comparison_metric = st.selectbox("Compare by", ["Engagements", "Impressions", "Comments", "Shares"])

merged = pd.merge(
    net_a[["Network", comparison_metric]],
    net_b[["Network", comparison_metric]],
    on="Network",
    how="outer",
    suffixes=(f" ({label_a[:15]})", f" ({label_b[:15]})"),
).fillna(0)

st.dataframe(
    merged.style.format(
        {col: "{:,.0f}" for col in merged.columns if col != "Network"}
    ),
    use_container_width=True,
    hide_index=True,
)

# --- Export ---
st.divider()
summary_data = []
for display_name, key in metrics_to_compare:
    summary_data.append(
        {
            "Metric": display_name,
            label_a: kpis_a.get(key, 0),
            label_b: kpis_b.get(key, 0),
            "Delta": delta_pct(kpis_a.get(key, 0), kpis_b.get(key, 0)),
        }
    )
summary_df = pd.DataFrame(summary_data)
csv = summary_df.to_csv(index=False)
st.download_button(
    "Download Comparison Summary (CSV)",
    csv,
    "period_comparison.csv",
    "text/csv",
    use_container_width=True,
)
