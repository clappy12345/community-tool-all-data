import streamlit as st
import pandas as pd

st.set_page_config(page_title="Compare Periods", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.theme import render_section_header, render_compare_card, render_nav_header
from utils.processors import get_kpis_safe, format_number, get_network_content_performance
from utils.charts import comparison_bar, looker_sentiment_timeline, CHART_CONFIG
from utils.data_store import load_saved_dataset, get_dataset_manifest


_CW_KEYS = ["cw_pick_a_start", "cw_pick_a_end", "cw_pick_b_start", "cw_pick_b_end"]


def _reset_comparison_window():
    """Clear window date picker state so they reset to full-range defaults."""
    for k in _CW_KEYS:
        st.session_state.pop(k, None)


def _filter_by_date_range(df, date_col, start, end):
    """Filter a DataFrame to rows within [start, end] inclusive."""
    if df is None:
        return None
    if not len(df):
        return df
    mask = (df[date_col].dt.date >= start) & (df[date_col].dt.date <= end)
    return df[mask]

filters = render_sidebar()
apply_theme()
require_data()

render_nav_header("Compare Periods", "Compare your current data side-by-side with a past period or campaign")
st.markdown("")

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

# ── Period B: NHL 25 Full Season ───────────────────────────────
st.markdown("### Period B — NHL 25 Full Season")

_PERIOD_B_DATASET = f"{title_key} 25 Full Season"

_b_loaded = st.session_state.get("compare_post_performance") is not None

if not _b_loaded:
    st.caption("Load the NHL 25 full-season dataset to compare against your current data.")
    if st.button(f"Load {_PERIOD_B_DATASET}", type="primary", use_container_width=True):
        with st.spinner(f"Loading {_PERIOD_B_DATASET}..."):
            loaded = load_saved_dataset(title_key, _PERIOD_B_DATASET)
            for k, v in loaded.items():
                st.session_state[f"compare_{k}"] = v
            manifest = get_dataset_manifest(title_key, _PERIOD_B_DATASET)
            cs = manifest.get("campaign_start") if manifest else None
            st.session_state["compare_campaign_start"] = cs
            st.session_state["compare_campaign_events"] = manifest.get("campaign_events", []) if manifest else []
            _reset_comparison_window()
        st.rerun()

pp_b = st.session_state.get("compare_post_performance")
prof_b = st.session_state.get("compare_profile_performance")
aff_b = st.session_state.get("compare_affogata")
inbox_b = st.session_state.get("compare_inbox")
looker_b = st.session_state.get("compare_looker_sentiment")

if pp_b is None:
    st.info("Select Period B data above to see comparisons.")
    st.stop()

date_b_min = pp_b["Date"].min().strftime("%b %d, %Y")
date_b_max = pp_b["Date"].max().strftime("%b %d, %Y")
label_b = st.text_input("Period B Label", value=f"{date_b_min} — {date_b_max}")

# ── Key Dates reminder for Period B ──────────────────────────
_reminder_events = st.session_state.get("compare_campaign_events", [])
_reminder_events = [e for e in _reminder_events if e.get("name") and e.get("date")]
if _reminder_events:
    _sorted_evts = sorted(_reminder_events, key=lambda e: e["date"])
    _pill_parts = []
    for e in _sorted_evts:
        _ec = e.get("color", "#4ECDC4")
        _en = e["name"]
        _ed = pd.Timestamp(e["date"]).strftime("%b %d, %Y")
        _pill_parts.append(
            f"<span style='display:inline-block; padding:2px 10px; margin:2px 0; "
            f"border-left:3px solid {_ec}; font-size:0.82rem;'>"
            f"<strong>{_en}</strong> &mdash; {_ed}</span>"
        )
    _pills = "  ".join(_pill_parts)
    st.markdown(
        f"<div style='background:rgba(78,205,196,0.08); border-radius:8px; "
        f"padding:10px 14px; margin:4px 0 12px 0;'>"
        f"<span style='font-size:0.72rem; text-transform:uppercase; letter-spacing:0.8px; "
        f"color:var(--text-secondary); font-weight:600;'>Key Dates</span><br>"
        f"{_pills}</div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# ═══════════════════════════════════════════════════════════════
# Compare Window — one section, two modes
# ═══════════════════════════════════════════════════════════════

full_a_start = pp_a["Date"].min().date()
full_a_end = pp_a["Date"].max().date()
full_b_start = pp_b["Date"].min().date()
full_b_end = pp_b["Date"].max().date()

# Clamp stale session values
for _key, _min, _max in [
    ("cw_pick_a_start", full_a_start, full_a_end),
    ("cw_pick_a_end", full_a_start, full_a_end),
    ("cw_pick_b_start", full_b_start, full_b_end),
    ("cw_pick_b_end", full_b_start, full_b_end),
]:
    if _key in st.session_state:
        v = st.session_state[_key]
        if v < _min or v > _max:
            del st.session_state[_key]

_dp1, _dp2 = st.columns(2)
with _dp1:
    st.markdown("**Period A dates**")
    window_a_start = st.date_input("Start", value=full_a_start, min_value=full_a_start, max_value=full_a_end, key="cw_pick_a_start")
    window_a_end = st.date_input("End", value=full_a_end, min_value=full_a_start, max_value=full_a_end, key="cw_pick_a_end")
with _dp2:
    st.markdown("**Period B dates**")
    window_b_start = st.date_input("Start", value=full_b_start, min_value=full_b_start, max_value=full_b_end, key="cw_pick_b_start")
    window_b_end = st.date_input("End", value=full_b_end, min_value=full_b_start, max_value=full_b_end, key="cw_pick_b_end")

_sel_a = (window_a_end - window_a_start).days + 1
_sel_b = (window_b_end - window_b_start).days + 1
st.caption(f"Comparing **{_sel_a} days** (A) vs **{_sel_b} days** (B)")

# ── Apply window filter to all dataframes ──────────────────────
pp_a_w = _filter_by_date_range(pp_a, "Date", window_a_start, window_a_end)
pp_b_w = _filter_by_date_range(pp_b, "Date", window_b_start, window_b_end)
prof_a_w = _filter_by_date_range(prof_a, "Date", window_a_start, window_a_end)
prof_b_w = _filter_by_date_range(prof_b, "Date", window_b_start, window_b_end)
looker_a_w = _filter_by_date_range(looker_a, "Date", window_a_start, window_a_end)
looker_b_w = _filter_by_date_range(looker_b, "Date", window_b_start, window_b_end)
aff_a_w = _filter_by_date_range(aff_a, "Created At", window_a_start, window_a_end)
aff_b_w = _filter_by_date_range(aff_b, "Created At", window_b_start, window_b_end)
inbox_a_w = _filter_by_date_range(inbox_a, "Timestamp", window_a_start, window_a_end)
inbox_b_w = _filter_by_date_range(inbox_b, "Timestamp", window_b_start, window_b_end)

pp_a_sliced = pp_a_w
pp_b_sliced = pp_b_w
prof_a_sliced = prof_a_w
prof_b_sliced = prof_b_w
looker_a_sliced = looker_a_w if looker_a_w is not None and len(looker_a_w) > 0 else None
looker_b_sliced = looker_b_w if looker_b_w is not None and len(looker_b_w) > 0 else None

st.markdown("")

# ── Calculate KPIs ─────────────────────────────────────────────
kpis_a = get_kpis_safe(pp_a_sliced, prof_a_sliced)
kpis_b = get_kpis_safe(pp_b_sliced, prof_b_sliced)


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
render_section_header("Key Metrics Comparison")

metrics_to_compare = [
    ("Total Impressions", "total_impressions"),
    ("Total Engagements", "total_engagements"),
    ("Avg Engagement Rate", "avg_engagement_rate"),
    ("Audience Growth", "audience_growth"),
    ("Total Posts", "total_posts"),
    ("Total Comments", "total_comments"),
    ("Saves", "total_saves"),
    ("Link Clicks", "total_link_clicks"),
    ("Video View Rate", "video_view_rate"),
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
        render_compare_card(display_name, fmt_a, fmt_b, label_a, label_b, delta, color)

st.markdown("")

# ── Visual Comparison ──────────────────────────────────────────
render_section_header("Visual Comparison")

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

st.markdown("")

# ── Sentiment Comparison ───────────────────────────────────────
render_section_header("Sentiment Comparison")

_has_looker_a = looker_a_sliced is not None and len(looker_a_sliced) > 0
_has_looker_b = looker_b_sliced is not None and len(looker_b_sliced) > 0

if _has_looker_a or _has_looker_b:
    _metric_cols = st.columns(6)
    if _has_looker_a:
        avg_a = looker_a_sliced["Impact Score"].mean()
        _metric_cols[0].metric(f"Avg ({label_a[:12]})", f"{avg_a:.1f}")
        _metric_cols[1].metric("High", f"{looker_a_sliced['Impact Score'].max():.1f}")
        _metric_cols[2].metric("Low", f"{looker_a_sliced['Impact Score'].min():.1f}")
    if _has_looker_b:
        avg_b = looker_b_sliced["Impact Score"].mean()
        _metric_cols[3].metric(f"Avg ({label_b[:12]})", f"{avg_b:.1f}")
        _metric_cols[4].metric("High", f"{looker_b_sliced['Impact Score'].max():.1f}")
        _metric_cols[5].metric("Low", f"{looker_b_sliced['Impact Score'].min():.1f}")

    if _has_looker_a and _has_looker_b:
        import plotly.graph_objects as go
        from utils.charts import apply_dark_theme

        _la = looker_a_sliced.copy()
        _lb = looker_b_sliced.copy()
        _la["Day"] = (_la["Date"] - _la["Date"].min()).dt.days
        _lb["Day"] = (_lb["Date"] - _lb["Date"].min()).dt.days
        _da = _la.groupby("Day")["Impact Score"].mean().reset_index()
        _db = _lb.groupby("Day")["Impact Score"].mean().reset_index()

        fig_sent = go.Figure()
        fig_sent.add_trace(go.Scatter(
            x=_da["Day"], y=_da["Impact Score"],
            mode="lines+markers", name=label_a,
            line=dict(color="#06D6A0", width=2.5, shape="spline"), marker=dict(size=5),
        ))
        fig_sent.add_trace(go.Scatter(
            x=_db["Day"], y=_db["Impact Score"],
            mode="lines+markers", name=label_b,
            line=dict(color="#90E0EF", width=2.5, shape="spline"), marker=dict(size=5),
        ))
        fig_sent.update_layout(
            title="Sentiment Score — aligned by period start",
            xaxis_title="Day", yaxis_title="Impact Score",
        )
        fig_sent = apply_dark_theme(fig_sent)
    elif _has_looker_a:
        fig_sent = looker_sentiment_timeline(looker_a_sliced, f"Sentiment — {label_a[:25]}")
    else:
        fig_sent = looker_sentiment_timeline(looker_b_sliced, f"Sentiment — {label_b[:25]}")

    st.plotly_chart(fig_sent, use_container_width=True, config=CHART_CONFIG)

    if _has_looker_a and _has_looker_b:
        diff = avg_a - avg_b
        direction = "higher" if diff > 0 else "lower"
        color = delta_color(avg_a, avg_b)
        st.markdown(
            f'<div class="t-compare" style="border-left: 4px solid {color};">'
            f"Period A avg impact score is <strong style='color:{color};'>{abs(diff):.1f} points {direction}</strong> "
            f"than Period B ({avg_a:.1f} vs {avg_b:.1f})"
            f"</div>",
            unsafe_allow_html=True,
        )
else:
    st.caption("No sentiment data available for either period")

st.markdown("")

# ── Community Volume Comparison ────────────────────────────────
render_section_header("Community Volume Comparison")

col_v1, col_v2 = st.columns(2)

with col_v1:
    st.markdown(f"**{label_a}**")
    vol_parts = []
    if aff_a_w is not None and len(aff_a_w) > 0:
        vol_parts.append(f"**{len(aff_a_w):,}** community conversations (Affogata)")
    if inbox_a_w is not None and len(inbox_a_w) > 0:
        vol_parts.append(f"**{len(inbox_a_w):,}** inbox messages (Sprout)")
    if vol_parts:
        for p in vol_parts:
            st.markdown(p)
    else:
        st.caption("No community data for Period A")

with col_v2:
    st.markdown(f"**{label_b}**")
    vol_parts = []
    if aff_b_w is not None and len(aff_b_w) > 0:
        vol_parts.append(f"**{len(aff_b_w):,}** community conversations (Affogata)")
    if inbox_b_w is not None and len(inbox_b_w) > 0:
        vol_parts.append(f"**{len(inbox_b_w):,}** inbox messages (Sprout)")
    if vol_parts:
        for p in vol_parts:
            st.markdown(p)
    else:
        st.caption("No community data for Period B")

st.markdown("")

# ── Platform Comparison ────────────────────────────────────────
render_section_header("Platform Comparison")

net_a = get_network_content_performance(pp_a_sliced)
net_b = get_network_content_performance(pp_b_sliced)

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
st.markdown("")
render_section_header("AI Analysis: What Changed and Why")

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
            label_a, label_b, kpis_a, kpis_b, looker_a_sliced, looker_b_sliced
        )
        if result:
            st.session_state[narrative_key] = result
            st.rerun()

if narrative_ready:
    st.markdown(st.session_state[narrative_key])

# ── Export ─────────────────────────────────────────────────────
st.markdown("")
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

if (looker_a_sliced is not None and len(looker_a_sliced) > 0) and (looker_b_sliced is not None and len(looker_b_sliced) > 0):
    summary_data.append({
        "Metric": "Avg Sentiment Score (Looker)",
        label_a: round(looker_a_sliced["Impact Score"].mean(), 1),
        label_b: round(looker_b_sliced["Impact Score"].mean(), 1),
        "Delta": delta_pct(looker_a_sliced["Impact Score"].mean(), looker_b_sliced["Impact Score"].mean()),
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
