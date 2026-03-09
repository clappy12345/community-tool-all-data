import streamlit as st
import pandas as pd

st.set_page_config(page_title="Multi-Title Dashboard", layout="wide")

from utils.sidebar import render_sidebar, apply_theme
from utils.theme import (
    render_nav_header,
    render_section_header,
    render_kpi_card,
    render_empty_state,
    inject_global_css,
)
from utils.titles import TITLES
from utils.data_store import list_saved_datasets, load_saved_dataset
from utils.processors import get_kpis_safe, format_number, combine_community_messages
from utils.charts import apply_dark_theme, CHART_CONFIG

filters = render_sidebar()
apply_theme()

render_nav_header(
    "Multi-Title Dashboard",
    "Compare NHL, UFC, and F1 community performance side-by-side",
)
st.markdown("")

# ── Load data for each title ──────────────────────────────────
title_data: dict[str, dict] = {}
active_title = st.session_state.get("active_title", "NHL")

for title_key, cfg in TITLES.items():
    # Use live session data for the currently active title
    if title_key == active_title and st.session_state.get("post_performance") is not None:
        pp = st.session_state["post_performance"]
        prof = st.session_state.get("profile_performance")
        looker = st.session_state.get("looker_sentiment")
        aff = st.session_state.get("affogata")
        inbox = st.session_state.get("inbox")
        kpis = get_kpis_safe(pp, prof)
        title_data[title_key] = {
            "cfg": cfg,
            "kpis": kpis,
            "label": "Current Session",
            "pp": pp,
            "prof": prof,
            "looker": looker,
            "affogata": aff,
            "inbox": inbox,
            "date_range": (pp["Date"].min(), pp["Date"].max()),
            "source": "live",
        }
        continue

    saved = list_saved_datasets(title_key)
    if not saved:
        continue

    # Dataset picker in session state
    picker_key = f"_mt_dataset_{title_key}"
    labels = [ds["label"] for ds in saved]
    if picker_key not in st.session_state:
        st.session_state[picker_key] = labels[0]

    label = st.session_state[picker_key]
    if label not in labels:
        label = labels[0]
        st.session_state[picker_key] = label

    loaded = load_saved_dataset(title_key, label)
    pp = loaded.get("post_performance")
    if pp is None or len(pp) == 0:
        continue

    prof = loaded.get("profile_performance")
    kpis = get_kpis_safe(pp, prof)
    title_data[title_key] = {
        "cfg": cfg,
        "kpis": kpis,
        "label": label,
        "pp": pp,
        "prof": prof,
        "looker": loaded.get("looker_sentiment"),
        "affogata": loaded.get("affogata"),
        "inbox": loaded.get("inbox"),
        "date_range": (pp["Date"].min(), pp["Date"].max()),
        "source": "saved",
        "all_labels": labels,
    }

if not title_data:
    render_empty_state(
        "🎮",
        "No Data Available",
        "Load sample data or upload data for at least one title, "
        "then save a dataset so it appears here. The currently active title's "
        "live session data will also be included.",
    )
    st.stop()

# ── Title / dataset selectors ─────────────────────────────────
title_keys = list(title_data.keys())
n_titles = len(title_keys)

cols_header = st.columns(n_titles)
for i, tk in enumerate(title_keys):
    td = title_data[tk]
    with cols_header[i]:
        dr = td["date_range"]
        date_str = f"{dr[0].strftime('%b %d')} — {dr[1].strftime('%b %d, %Y')}"
        source_badge = "LIVE" if td.get("source") == "live" else td["label"]

        st.markdown(
            f'<div class="t-title-card" style="border-top:3px solid var(--accent);">'
            f'<div class="t-title-card-name">{td["cfg"]["icon"]} {td["cfg"]["full_name"]}</div>'
            f'<div class="t-title-card-date">{source_badge} · {date_str}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if td.get("source") == "saved" and td.get("all_labels"):
            selected = st.selectbox(
                "Dataset",
                td["all_labels"],
                index=td["all_labels"].index(td["label"]),
                key=f"_mt_dataset_{tk}",
                label_visibility="collapsed",
            )
            if selected != td["label"]:
                st.rerun()

st.markdown("")

# ── KPI Comparison Grid ───────────────────────────────────────
render_section_header("Key Metrics Comparison")

_KPI_ROWS = [
    ("Total Impressions", "total_impressions"),
    ("Total Engagements", "total_engagements"),
    ("Engagement Rate", "avg_engagement_rate"),
    ("Video Views", "total_video_views"),
    ("Audience Growth", "audience_growth"),
    ("Total Audience", "total_audience"),
    ("Total Posts", "total_posts"),
    ("Comments", "total_comments"),
    ("Shares", "total_shares"),
]

for display_name, key in _KPI_ROWS:
    is_rate = "rate" in key.lower()
    cols = st.columns(n_titles)
    for i, tk in enumerate(title_keys):
        val = title_data[tk]["kpis"].get(key, 0)
        with cols[i]:
            if is_rate:
                fmt_val = f"{val:.2f}%"
            elif key == "audience_growth":
                fmt_val = f"{'+' if val > 0 else ''}{format_number(val)}"
            else:
                fmt_val = format_number(val)
            render_kpi_card(
                f"{display_name}",
                fmt_val,
                help=f"{title_data[tk]['cfg']['full_name']}",
            )

st.markdown("")

# ── Visual Comparison ─────────────────────────────────────────
render_section_header("Visual Comparison")

import plotly.graph_objects as go
from plotly.subplots import make_subplots

_VIS_METRICS = [
    ("Impressions", "total_impressions"),
    ("Engagements", "total_engagements"),
    ("Video Views", "total_video_views"),
    ("Comments", "total_comments"),
    ("Shares", "total_shares"),
]

_TITLE_COLORS = {
    "NHL": "#00B4D8",
    "UFC": "#EF476F",
    "F1": "#06D6A0",
}

fig = go.Figure()

for tk in title_keys:
    vals = [title_data[tk]["kpis"].get(m[1], 0) for m in _VIS_METRICS]
    fig.add_trace(go.Bar(
        x=[m[0] for m in _VIS_METRICS],
        y=vals,
        name=title_data[tk]["cfg"]["full_name"],
        marker_color=_TITLE_COLORS.get(tk, "#8899A6"),
        marker_cornerradius=4,
        text=[format_number(v) for v in vals],
        textposition="outside",
        textfont=dict(size=10),
    ))

fig.update_layout(barmode="group", xaxis=dict(showgrid=False))
fig = apply_dark_theme(fig, height=420)
st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.markdown("")

# ── Engagement Rate Comparison ────────────────────────────────
render_section_header("Engagement Rate Comparison")

er_cols = st.columns(n_titles)
for i, tk in enumerate(title_keys):
    er = title_data[tk]["kpis"].get("avg_engagement_rate", 0)
    with er_cols[i]:
        render_kpi_card(
            f"{title_data[tk]['cfg']['full_name']}",
            f"{er:.2f}%",
        )

st.markdown("")

# ── Sentiment Comparison ──────────────────────────────────────
has_any_sentiment = any(
    td.get("looker") is not None and len(td["looker"]) > 0
    for td in title_data.values()
)

if has_any_sentiment:
    render_section_header("Sentiment Comparison")

    sent_cols = st.columns(n_titles)
    for i, tk in enumerate(title_keys):
        looker = title_data[tk].get("looker")
        with sent_cols[i]:
            if looker is not None and len(looker) > 0:
                avg = looker["Impact Score"].mean()
                high = looker["Impact Score"].max()
                low = looker["Impact Score"].min()
                render_kpi_card(f"Avg Sentiment — {title_data[tk]['cfg']['name']}", f"{avg:.1f}")
                st.caption(f"High: {high:.1f} · Low: {low:.1f}")
            else:
                st.caption(f"No sentiment data for {title_data[tk]['cfg']['name']}")

    # Overlay sentiment timelines
    titles_with_sent = [tk for tk in title_keys
                        if title_data[tk].get("looker") is not None
                        and len(title_data[tk]["looker"]) > 0]

    if len(titles_with_sent) >= 2:
        fig_sent = go.Figure()
        for tk in titles_with_sent:
            lk = title_data[tk]["looker"].copy()
            lk["Day"] = (lk["Date"] - lk["Date"].min()).dt.days
            daily_sent = lk.groupby("Day")["Impact Score"].mean().reset_index()
            fig_sent.add_trace(go.Scatter(
                x=daily_sent["Day"],
                y=daily_sent["Impact Score"],
                mode="lines+markers",
                name=title_data[tk]["cfg"]["full_name"],
                line=dict(color=_TITLE_COLORS.get(tk, "#8899A6"), width=2.5, shape="spline"),
                marker=dict(size=4),
            ))
        fig_sent.update_layout(
            title="Sentiment — aligned by period start",
            xaxis_title="Day",
            yaxis_title="Impact Score",
        )
        fig_sent = apply_dark_theme(fig_sent)
        st.plotly_chart(fig_sent, use_container_width=True, config=CHART_CONFIG)

    st.markdown("")

# ── Community Volume ──────────────────────────────────────────
render_section_header("Community Volume")

vol_cols = st.columns(n_titles)
for i, tk in enumerate(title_keys):
    td = title_data[tk]
    aff_count = len(td["affogata"]) if td.get("affogata") is not None else 0
    inbox_count = len(td["inbox"]) if td.get("inbox") is not None else 0
    total = aff_count + inbox_count

    with vol_cols[i]:
        render_kpi_card(
            f"{td['cfg']['full_name']} Messages",
            format_number(total) if total > 0 else "N/A",
        )
        if total > 0:
            parts = []
            if aff_count > 0:
                parts.append(f"{aff_count:,} community")
            if inbox_count > 0:
                parts.append(f"{inbox_count:,} inbox")
            st.caption(" · ".join(parts))

st.markdown("")

# ── Platform Distribution per Title ───────────────────────────
render_section_header("Platform Distribution")

plat_cols = st.columns(n_titles)
for i, tk in enumerate(title_keys):
    pp = title_data[tk]["pp"]
    platform_counts = pp.groupby("Network")["Impressions"].sum().sort_values(ascending=False)
    total_imp = platform_counts.sum()

    with plat_cols[i]:
        st.markdown(f"**{title_data[tk]['cfg']['full_name']}**")
        for network, imp in platform_counts.items():
            pct = imp / total_imp * 100 if total_imp > 0 else 0
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:4px 0;'
                f'border-bottom:1px solid var(--border-subtle);">'
                f'<span style="font-size:0.82rem;">{network}</span>'
                f'<span style="font-size:0.82rem;color:var(--accent);font-weight:600;">'
                f'{pct:.1f}%</span></div>',
                unsafe_allow_html=True,
            )

# ── Missing titles note ───────────────────────────────────────
missing = [k for k in TITLES if k not in title_data]
if missing:
    st.markdown("")
    missing_names = ", ".join(TITLES[k]["full_name"] for k in missing)
    st.caption(
        f"No data available for {missing_names}. "
        "Load data for those titles and save a dataset to include them here."
    )
