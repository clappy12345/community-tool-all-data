import streamlit as st
import pandas as pd

st.set_page_config(page_title="Compare Periods", page_icon="🔄", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.data_loader import (
    load_post_performance,
    load_profile_performance,
    load_affogata,
    load_inbox_export,
    load_looker_sentiment,
)
from utils.processors import get_kpis_safe, format_number, get_network_content_performance
from utils.charts import comparison_bar, looker_sentiment_timeline, CHART_CONFIG
from utils.titles import get_title_config
from utils.data_store import list_saved_datasets, load_saved_dataset
from utils.sample_data import generate_sample_comparison_data

filters = render_sidebar()
apply_theme()
require_data()

st.title("🔄 Compare Periods")
st.markdown("*Compare your current data side-by-side with a past period*")
st.divider()

_cfg = get_title_config()
title_key = st.session_state.get("active_title", "NHL")

# ── Period A (current data) ────────────────────────────────────
pp_a = st.session_state["post_performance"]
prof_a = st.session_state.get("profile_performance")
aff_a = st.session_state.get("affogata")
inbox_a = st.session_state.get("inbox")
looker_a = st.session_state.get("looker_sentiment")

date_a_min = pp_a["Date"].min().strftime("%b %d, %Y")
date_a_max = pp_a["Date"].max().strftime("%b %d, %Y")
label_a = st.text_input("Period A Label", value=f"{date_a_min} — {date_a_max}")

# ── Period B: sample, saved, or uploaded ───────────────────────
st.markdown("### Period B — Comparison Data")

saved = list_saved_datasets(title_key)
source_options = ["Load sample data", "Upload new files"]
if saved:
    source_options.append("Load from saved datasets")

source = st.radio("Period B source", source_options, horizontal=True)

if source == "Load sample data":
    if st.button("Load Sample Comparison Data", type="primary", use_container_width=True):
        with st.spinner("Generating sample comparison data..."):
            sample = generate_sample_comparison_data(title_key)
            for k, v in sample.items():
                st.session_state[f"compare_{k}"] = v
        st.rerun()

elif source == "Load from saved datasets" and saved:
    saved_labels = [ds["label"] for ds in saved]
    chosen = st.selectbox("Select a saved dataset", saved_labels)

    if st.button("Load Period B", use_container_width=True):
        with st.spinner(f"Loading {chosen}..."):
            loaded = load_saved_dataset(title_key, chosen)
            for k, v in loaded.items():
                st.session_state[f"compare_{k}"] = v
        st.rerun()
else:
    st.markdown(f"Upload the same CSV types from a different date range ({_cfg['compare_hint']}).")
    col1, col2, col3 = st.columns(3)
    with col1:
        pp_b_file = st.file_uploader("Post Performance", type=["csv"], key="compare_pp")
        inbox_b_file = st.file_uploader("Inbox Export", type=["csv", "zip"], key="compare_inbox")
    with col2:
        prof_b_file = st.file_uploader("Profile Performance", type=["csv"], key="compare_prof")
        looker_b_file = st.file_uploader("Looker Sentiment", type=["csv"], key="compare_looker")
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
    if inbox_b_file:
        st.session_state["compare_inbox"] = load_inbox_export(
            inbox_b_file.read(), inbox_b_file.name
        )
        inbox_b_file.seek(0)
    if looker_b_file:
        st.session_state["compare_looker_sentiment"] = load_looker_sentiment(
            looker_b_file.read(), looker_b_file.name
        )
        looker_b_file.seek(0)

pp_b = st.session_state.get("compare_post_performance")
prof_b = st.session_state.get("compare_profile_performance")
aff_b = st.session_state.get("compare_affogata")
inbox_b = st.session_state.get("compare_inbox")
looker_b = st.session_state.get("compare_looker_sentiment")

if pp_b is None:
    st.info("Select or upload Period B data above to see comparisons.")
    st.stop()

date_b_min = pp_b["Date"].min().strftime("%b %d, %Y")
date_b_max = pp_b["Date"].max().strftime("%b %d, %Y")
label_b = st.text_input("Period B Label", value=f"{date_b_min} — {date_b_max}")

st.divider()

# ── Calculate KPIs ─────────────────────────────────────────────
kpis_a = get_kpis_safe(pp_a, prof_a)
kpis_b = get_kpis_safe(pp_b, prof_b)


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


# ── Comparison Cards ───────────────────────────────────────────
st.markdown("### Key Metrics Comparison")

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

# ── Visual Comparison ──────────────────────────────────────────
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

# ── Sentiment Comparison (Looker) ──────────────────────────────
st.markdown("### Sentiment Comparison (Looker)")

col_s1, col_s2 = st.columns(2)

with col_s1:
    st.markdown(f"**{label_a}**")
    if looker_a is not None and len(looker_a) > 0:
        avg_a = looker_a["Impact Score"].mean()
        high_a = looker_a["Impact Score"].max()
        low_a = looker_a["Impact Score"].min()
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Impact Score", f"{avg_a:.1f}")
        m2.metric("Highest", f"{high_a:.1f}")
        m3.metric("Lowest", f"{low_a:.1f}")
        fig = looker_sentiment_timeline(looker_a, f"Sentiment — {label_a[:25]}")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
    else:
        st.caption("No Looker Sentiment data for Period A")

with col_s2:
    st.markdown(f"**{label_b}**")
    if looker_b is not None and len(looker_b) > 0:
        avg_b = looker_b["Impact Score"].mean()
        high_b = looker_b["Impact Score"].max()
        low_b = looker_b["Impact Score"].min()
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg Impact Score", f"{avg_b:.1f}")
        m2.metric("Highest", f"{high_b:.1f}")
        m3.metric("Lowest", f"{low_b:.1f}")
        fig = looker_sentiment_timeline(looker_b, f"Sentiment — {label_b[:25]}")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
    else:
        st.caption("No Looker Sentiment data for Period B")

if (looker_a is not None and len(looker_a) > 0) and (looker_b is not None and len(looker_b) > 0):
    avg_a = looker_a["Impact Score"].mean()
    avg_b = looker_b["Impact Score"].mean()
    diff = avg_a - avg_b
    direction = "higher" if diff > 0 else "lower"
    color = delta_color(avg_a, avg_b)
    st.markdown(
        f"<div style='background:#1A1D23; border-radius:10px; padding:16px; "
        f"border-left: 4px solid {color};'>"
        f"Period A avg impact score is <strong style='color:{color};'>{abs(diff):.1f} points {direction}</strong> "
        f"than Period B ({avg_a:.1f} vs {avg_b:.1f})"
        f"</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Community Volume Comparison ────────────────────────────────
st.markdown("### Community Volume Comparison")

col_v1, col_v2 = st.columns(2)

with col_v1:
    st.markdown(f"**{label_a}**")
    vol_parts = []
    if aff_a is not None and len(aff_a) > 0:
        vol_parts.append(f"**{len(aff_a):,}** community conversations (Affogata)")
    if inbox_a is not None and len(inbox_a) > 0:
        vol_parts.append(f"**{len(inbox_a):,}** inbox messages (Sprout)")
    if vol_parts:
        for p in vol_parts:
            st.markdown(p)
    else:
        st.caption("No community data for Period A")

with col_v2:
    st.markdown(f"**{label_b}**")
    vol_parts = []
    if aff_b is not None and len(aff_b) > 0:
        vol_parts.append(f"**{len(aff_b):,}** community conversations (Affogata)")
    if inbox_b is not None and len(inbox_b) > 0:
        vol_parts.append(f"**{len(inbox_b):,}** inbox messages (Sprout)")
    if vol_parts:
        for p in vol_parts:
            st.markdown(p)
    else:
        st.caption("No community data for Period B")

st.divider()

# ── Platform Comparison ────────────────────────────────────────
st.markdown("### Platform Comparison")

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

# ── AI Analysis ───────────────────────────────────────────────
st.divider()
st.markdown("### AI Analysis: What Changed and Why")

from utils.ai_analysis import generate_comparison_narrative

narrative_key = "compare_narrative"
narrative_ready = narrative_key in st.session_state and st.session_state[narrative_key] is not None

col_ai_btn, col_ai_status = st.columns([1, 3])
with col_ai_btn:
    run_analysis = st.button(
        "Generate Analysis" if not narrative_ready else "Regenerate Analysis",
        type="primary" if not narrative_ready else "secondary",
        use_container_width=True,
        key="btn_compare_ai",
    )
with col_ai_status:
    if narrative_ready:
        st.success("Analysis ready")
    else:
        st.caption("Requires Google API key — takes 10-20 seconds")

if run_analysis:
    with st.spinner("Analyzing differences between periods..."):
        result = generate_comparison_narrative(
            label_a, label_b, kpis_a, kpis_b, looker_a, looker_b
        )
        if result:
            st.session_state[narrative_key] = result
            st.rerun()

if narrative_ready:
    st.markdown(st.session_state[narrative_key])

# ── Export ─────────────────────────────────────────────────────
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

if (looker_a is not None and len(looker_a) > 0) and (looker_b is not None and len(looker_b) > 0):
    summary_data.append({
        "Metric": "Avg Sentiment Score (Looker)",
        label_a: round(looker_a["Impact Score"].mean(), 1),
        label_b: round(looker_b["Impact Score"].mean(), 1),
        "Delta": delta_pct(looker_a["Impact Score"].mean(), looker_b["Impact Score"].mean()),
    })

summary_df = pd.DataFrame(summary_data)
csv = summary_df.to_csv(index=False)
st.download_button(
    "Download Comparison Summary (CSV)",
    csv,
    "period_comparison.csv",
    "text/csv",
    use_container_width=True,
)
