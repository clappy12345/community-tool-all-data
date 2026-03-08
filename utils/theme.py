"""Centralized design system — tokens, global CSS, reusable card components.

Every page imports `inject_global_css` (once, after sidebar) and uses the
render helpers instead of hand-rolling inline HTML.
"""

from __future__ import annotations

import streamlit as st

# ── Color tokens ────────────────────────────────────────────────
PRIMARY = "#00B4D8"
PRIMARY_LIGHT = "#90E0EF"
POSITIVE = "#06D6A0"
NEGATIVE = "#EF476F"
NEUTRAL = "#FFD166"
MUTED = "#90A4AE"
LINK = "#00B4D8"

# ── Spacing / typography scale (px) ────────────────────────────
CARD_PAD = "16px 20px"
CARD_RADIUS = "10px"
FONT_XS = "0.72rem"
FONT_SM = "0.8rem"
FONT_BASE = "0.9rem"
FONT_LG = "1.1rem"
FONT_KPI = "2rem"

# ── Global CSS ──────────────────────────────────────────────────
_GLOBAL_CSS = """
<style>
:root {
    --bg-card: #1A1D23;
    --bg-card-alt: #1E2028;
    --bg-page: #0E1117;
    --text-primary: #FAFAFA;
    --text-secondary: #90A4AE;
    --text-heading: #FAFAFA;
    --border-subtle: rgba(0,180,216,0.15);
    --accent: #00B4D8;
    --positive: #06D6A0;
    --negative: #EF476F;
    --neutral: #FFD166;
    --link: #00B4D8;
    --shadow: 0 1px 3px rgba(0,0,0,0.3);
}

/* KPI card */
.t-kpi {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
    box-shadow: var(--shadow);
    transition: border-color 0.15s;
}
.t-kpi:hover { border-color: var(--accent); }
.t-kpi-label {
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.t-kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    margin: 4px 0 0 0;
    line-height: 1.1;
}
.t-kpi-delta {
    font-size: 0.75rem;
    margin: 4px 0 0 0;
    font-weight: 600;
}
.t-kpi-delta.up   { color: var(--positive); }
.t-kpi-delta.down { color: var(--negative); }
.t-kpi-delta.flat { color: var(--text-secondary); }

/* Post card (collapsed preview) */
.t-post {
    padding: 14px 18px;
    margin: 6px 0;
    background: var(--bg-card);
    border-radius: 10px;
    border-left: 4px solid var(--accent);
    box-shadow: var(--shadow);
    transition: transform 0.1s, box-shadow 0.15s;
}
.t-post:hover { transform: translateY(-1px); box-shadow: 0 3px 8px rgba(0,0,0,0.35); }
.t-post-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.t-post-meta span { font-size: 0.8rem; font-weight: 600; }
.t-post-meta .left  { color: var(--text-secondary); }
.t-post-meta .right { color: var(--accent); }
.t-post-body { font-size: 0.9rem; color: var(--text-primary); line-height: 1.4; }

/* Message card (community messages) */
.t-msg {
    padding: 12px 16px;
    margin: 5px 0;
    background: var(--bg-card);
    border-radius: 8px;
    box-shadow: var(--shadow);
    transition: transform 0.1s;
}
.t-msg:hover { transform: translateY(-1px); }
.t-msg-head {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}
.t-msg-head span { font-size: 0.73rem; color: var(--text-secondary); }
.t-msg-text { font-size: 0.88rem; color: var(--text-primary); line-height: 1.4; }
.t-msg-link {
    margin-top: 5px;
}
.t-msg-link a {
    font-size: 0.73rem;
    color: var(--link);
    text-decoration: none;
}
.t-msg-link a:hover { text-decoration: underline; }

/* Quote card (report theme quotes) */
.t-quote {
    padding: 10px 16px;
    margin: 4px 0;
    background: var(--bg-card);
    border-radius: 8px;
    font-size: 0.88rem;
    font-style: italic;
    color: var(--text-primary);
    box-shadow: var(--shadow);
}

/* Section header */
.t-section {
    margin: 0 0 4px 0;
}
.t-section h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-heading);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.t-section-sub {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin: 2px 0 0 0;
}

/* Platform summary card */
.t-platform {
    text-align: center;
    padding: 14px;
    background: var(--bg-card);
    border-radius: 10px;
    box-shadow: var(--shadow);
    transition: transform 0.1s;
}
.t-platform:hover { transform: translateY(-1px); }
.t-platform-name { font-size: 1.05rem; font-weight: 600; color: var(--text-primary); }
.t-platform-label { color: var(--text-secondary); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.4px; }
.t-platform-value { font-size: 1.25rem; font-weight: 700; }
.t-platform-sub { margin-top: 6px; }

/* Comparison card */
.t-compare {
    background: var(--bg-card);
    border-radius: 10px;
    padding: 16px;
    margin: 8px 0;
    box-shadow: var(--shadow);
}
.t-compare-title { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; }
.t-compare-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-top: 8px;
}
.t-compare-period { font-size: 0.75rem; color: var(--text-secondary); }
.t-compare-val { font-size: 1.35rem; font-weight: 700; }
.t-compare-delta { font-size: 1.15rem; font-weight: 700; }

/* Trending line */
.t-trend {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-top: -6px;
    margin-bottom: 8px;
}

/* Metric widget override */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 10px 14px;
    box-shadow: var(--shadow);
}
</style>
"""

_LIGHT_OVERRIDES = """
<style>
:root {
    --bg-card: #F5F7FA;
    --bg-card-alt: #FFFFFF;
    --bg-page: #FFFFFF;
    --text-primary: #1a1a2e;
    --text-secondary: #5a6577;
    --text-heading: #1a1a2e;
    --border-subtle: rgba(0,0,0,0.08);
    --shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.stApp { background-color: var(--bg-page); color: var(--text-primary); }
[data-testid="stSidebar"] { background-color: #F0F2F6; }
[data-testid="stSidebar"] * { color: var(--text-primary); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--text-heading); }
.stApp p, .stApp label { color: var(--text-primary); }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; }
[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }
[data-testid="stExpander"] { background-color: #FAFAFA; border-color: #e0e0e0; }
.t-kpi-value { color: var(--accent); }
.t-post-body, .t-msg-text, .t-quote { color: var(--text-primary); }
</style>
"""


def inject_global_css():
    """Call once per page, right after render_sidebar + apply_theme."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    if st.session_state.get("light_mode", False):
        st.markdown(_LIGHT_OVERRIDES, unsafe_allow_html=True)


# ── Reusable render helpers ────────────────────────────────────


def render_kpi_card(label: str, value: str, delta: float | None = None):
    """Styled KPI card. *delta* is a percentage change (e.g. 12.3 means +12.3%)."""
    delta_html = ""
    if delta is not None:
        if abs(delta) < 0.5:
            cls, arrow = "flat", "→"
        elif delta > 0:
            cls, arrow = "up", "↑"
        else:
            cls, arrow = "down", "↓"
        delta_html = f'<p class="t-kpi-delta {cls}">{arrow} {abs(delta):.1f}%</p>'
    st.markdown(
        f'<div class="t-kpi">'
        f'<p class="t-kpi-label">{label}</p>'
        f'<p class="t-kpi-value">{value}</p>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_post_card(
    rank: int,
    channel_str: str,
    date_str: str,
    text: str,
    impressions: str,
    engagements: str,
):
    """Collapsed preview card for a grouped post."""
    st.markdown(
        f'<div class="t-post">'
        f'<div class="t-post-meta">'
        f'<span class="left">#{rank} · {channel_str} · {date_str}</span>'
        f'<span class="right">{impressions} imp · {engagements} eng</span>'
        f'</div>'
        f'<div class="t-post-body">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_message_card(
    network: str,
    source: str,
    text: str,
    sentiment: str,
    engagements: int = 0,
    link: str = "",
    timestamp: str = "",
):
    """Community message card with sentiment-colored left border."""
    from utils.charts import SENTIMENT_COLORS

    sent_color = SENTIMENT_COLORS.get(str(sentiment).lower(), "#808080")
    eng_str = f" · {engagements:,} eng" if engagements > 0 else ""
    link_html = ""
    if link and link not in ("", "nan"):
        link_html = (
            f'<div class="t-msg-link">'
            f'<a href="{link}" target="_blank">View ↗</a>'
            f'</div>'
        )
    ts_html = f"<span>{timestamp}</span>" if timestamp else ""

    st.markdown(
        f'<div class="t-msg" style="border-left: 3px solid {sent_color};">'
        f'<div class="t-msg-head">'
        f'<span>{network} · {source}{eng_str}</span>'
        f'{ts_html}'
        f'</div>'
        f'<div class="t-msg-text">{text}</div>'
        f'{link_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_quote_card(text: str, accent_color: str = POSITIVE):
    """Styled quote block for report theme quotes."""
    st.markdown(
        f'<div class="t-quote" style="border-left: 3px solid {accent_color};">'
        f'"{text}"'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str | None = None):
    """Consistent section header replacing raw ### markdown + divider."""
    sub = f'<p class="t-section-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="t-section">'
        f'<h3>{title}</h3>'
        f'{sub}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_platform_card(
    network: str,
    audience: str,
    growth: str,
    color: str = PRIMARY,
):
    """Platform summary card for Platform Breakdown page."""
    st.markdown(
        f'<div class="t-platform" style="border-top: 3px solid {color};">'
        f'<div class="t-platform-name">{network}</div>'
        f'<div class="t-platform-label">AUDIENCE</div>'
        f'<div class="t-platform-value" style="color:{color};">{audience}</div>'
        f'<div class="t-platform-sub">'
        f'<div class="t-platform-label">GROWTH</div>'
        f'<div style="font-size:1rem; font-weight:600; color:var(--text-primary);">+{growth}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_compare_card(
    display_name: str,
    fmt_a: str,
    fmt_b: str,
    label_a: str,
    label_b: str,
    delta: str,
    color: str,
):
    """Comparison card for Compare Periods page."""
    st.markdown(
        f'<div class="t-compare" style="border-top: 3px solid {color};">'
        f'<div class="t-compare-title">{display_name}</div>'
        f'<div class="t-compare-row">'
        f'<div><span class="t-compare-period">{label_a[:20]}</span><br>'
        f'<span class="t-compare-val" style="color:var(--accent);">{fmt_a}</span></div>'
        f'<div class="t-compare-delta" style="color:{color};">{delta}</div>'
        f'<div style="text-align:right;"><span class="t-compare-period">{label_b[:20]}</span><br>'
        f'<span class="t-compare-val" style="color:#90E0EF;">{fmt_b}</span></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def render_trend_line(parts: list[str]):
    """Trending topics line below topic chart."""
    if parts:
        st.markdown(
            '<div class="t-trend">'
            "Trending (1st half → 2nd half): " + " &nbsp;·&nbsp; ".join(parts)
            + "</div>",
            unsafe_allow_html=True,
        )
