"""Centralized design system — tokens, global CSS, reusable card components.

Every page imports `inject_global_css` (once, after sidebar) and uses the
render helpers instead of hand-rolling inline HTML.
"""
from __future__ import annotations

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
CARD_PAD = "20px 24px"
CARD_RADIUS = "14px"
FONT_XS = "0.72rem"
FONT_SM = "0.8rem"
FONT_BASE = "0.9rem"
FONT_LG = "1.1rem"
FONT_KPI = "2.2rem"

# ── Global CSS ──────────────────────────────────────────────────
_GLOBAL_CSS = """
<style>
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

:root {
    --bg-card: rgba(26, 29, 35, 0.72);
    --bg-card-alt: rgba(30, 32, 40, 0.65);
    --bg-card-solid: #1A1D23;
    --bg-page: #0E1117;
    --text-primary: #FAFAFA;
    --text-secondary: #8899A6;
    --text-heading: #FAFAFA;
    --border-subtle: rgba(0,180,216,0.10);
    --border-hover: rgba(0,180,216,0.35);
    --accent: #00B4D8;
    --accent-light: #90E0EF;
    --accent-glow: rgba(0,180,216,0.08);
    --positive: #06D6A0;
    --negative: #EF476F;
    --neutral: #FFD166;
    --link: #00B4D8;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.25);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.3);
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 18px;
    --glass-blur: blur(16px);
}

/* ── Hide Streamlit chrome ─────────────────────────────────── */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
div[data-testid="stDecoration"] { display: none; }

/* ── Custom scrollbar ──────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(0,180,216,0.18);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(0,180,216,0.35); }

/* ── Sidebar refinement ────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12151C 0%, #0E1117 100%);
    border-right: 1px solid rgba(0,180,216,0.08);
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] h2 {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}

/* ── Global typography ─────────────────────────────────────── */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.stApp h1 {
    font-weight: 800;
    letter-spacing: -0.02em;
    font-size: 1.75rem;
}

/* ── KPI card ──────────────────────────────────────────────── */
/* ── KPI metric card (wraps st.metric) ─────────────────────── */
.kpi-card [data-testid="stMetric"] {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 20px 24px 18px;
    text-align: center;
    box-shadow: var(--shadow-sm);
    position: relative;
    overflow: visible;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    animation: fadeInUp 0.35s ease both;
}
.kpi-card [data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent-light));
    border-radius: var(--radius-md) var(--radius-md) 0 0;
}
.kpi-card [data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md), 0 0 20px var(--accent-glow);
}
.kpi-card [data-testid="stMetricLabel"] {
    justify-content: center;
}
.kpi-card [data-testid="stMetricLabel"] p {
    font-size: 0.7rem !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
}
.kpi-card [data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: var(--accent) !important;
    justify-content: center;
    line-height: 1.05;
    letter-spacing: -0.02em;
}
.kpi-card [data-testid="stMetricDelta"] {
    justify-content: center;
    font-weight: 700;
}
.kpi-card [data-testid="stMetricDelta"] svg { display: none; }
.kpi-card [data-testid="stMetricDelta"][style*="--delta-color-normal"] span,
.kpi-card [data-testid="stMetricDelta"] span {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    line-height: 1.5;
}

/* ── Post card ─────────────────────────────────────────────── */
.t-post {
    padding: 16px 20px;
    margin: 8px 0;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-radius: var(--radius-md);
    border-left: 4px solid var(--accent);
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: fadeInUp 0.35s ease both;
}
.t-post:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.t-post-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.t-post-meta span { font-size: 0.78rem; font-weight: 600; }
.t-post-meta .left  { color: var(--text-secondary); }
.t-post-meta .right { color: var(--accent); font-weight: 700; }
.t-post-body {
    font-size: 0.88rem;
    color: var(--text-primary);
    line-height: 1.5;
    opacity: 0.92;
}

/* ── Message card ──────────────────────────────────────────── */
.t-msg {
    padding: 14px 18px;
    margin: 6px 0;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: fadeInUp 0.3s ease both;
}
.t-msg:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}
.t-msg-head {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
}
.t-msg-head span { font-size: 0.73rem; color: var(--text-secondary); font-weight: 500; }
.t-msg-text { font-size: 0.86rem; color: var(--text-primary); line-height: 1.5; }
.t-msg-link { margin-top: 8px; }
.t-msg-link a {
    font-size: 0.73rem;
    color: var(--link);
    text-decoration: none;
    font-weight: 600;
    transition: color 0.15s;
}
.t-msg-link a:hover { color: var(--accent-light); text-decoration: underline; }

/* ── Quote card ────────────────────────────────────────────── */
.t-quote {
    padding: 14px 20px;
    margin: 6px 0;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-radius: var(--radius-sm);
    font-size: 0.88rem;
    font-style: italic;
    color: var(--text-primary);
    box-shadow: var(--shadow-sm);
    line-height: 1.55;
    animation: fadeInUp 0.3s ease both;
}

/* ── Section header ────────────────────────────────────────── */
.t-section {
    margin: 0 0 6px 0;
}
.t-section h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-heading);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    letter-spacing: -0.01em;
}
.t-section-sub {
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin: 3px 0 0 0;
    line-height: 1.4;
}

/* ── Platform summary card ─────────────────────────────────── */
.t-platform {
    text-align: center;
    padding: 18px 16px;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: fadeInUp 0.35s ease both;
}
.t-platform:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.t-platform-name {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4px;
}
.t-platform-label {
    color: var(--text-secondary);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
}
.t-platform-value { font-size: 1.3rem; font-weight: 800; }
.t-platform-sub { margin-top: 8px; }

/* ── Comparison card ───────────────────────────────────────── */
.t-compare {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-radius: var(--radius-md);
    padding: 18px 20px;
    margin: 8px 0;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease;
    animation: fadeInUp 0.35s ease both;
}
.t-compare:hover { transform: translateY(-1px); }
.t-compare-title {
    font-size: 0.72rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
}
.t-compare-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-top: 10px;
}
.t-compare-period { font-size: 0.73rem; color: var(--text-secondary); }
.t-compare-val { font-size: 1.4rem; font-weight: 800; }
.t-compare-delta { font-size: 1.2rem; font-weight: 800; }

/* ── Trending line ─────────────────────────────────────────── */
.t-trend {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: -4px;
    margin-bottom: 10px;
}

/* ── Card container (chart/section wrapper) ────────────────── */
.t-card-container {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin: 12px 0;
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.4s ease both;
}
.t-card-container-title {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-secondary);
    font-weight: 600;
    margin: 0 0 16px 0;
}

/* ── Status badge ──────────────────────────────────────────── */
.t-status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 0;
}
.t-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.t-status-dot.active { background: var(--positive); box-shadow: 0 0 6px rgba(6,214,160,0.4); }
.t-status-dot.inactive { background: #3a3f4a; }
.t-status-name {
    font-size: 0.78rem;
    font-weight: 500;
}
.t-status-name.active { color: var(--text-primary); }
.t-status-name.inactive { color: var(--text-secondary); opacity: 0.6; }
.t-status-badge {
    font-size: 0.65rem;
    font-weight: 700;
    padding: 1px 8px;
    border-radius: 10px;
    background: rgba(0,180,216,0.12);
    color: var(--accent);
    margin-left: auto;
}

/* ── Chip / pill ───────────────────────────────────────────── */
.t-chip {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 6px 16px;
    border-radius: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}
.t-chip:hover {
    border-color: var(--accent);
    background: rgba(0,180,216,0.08);
    color: var(--accent);
}

/* ── Navigation header ─────────────────────────────────────── */
.t-nav-header {
    margin-bottom: 8px;
    animation: fadeInUp 0.3s ease both;
}
.t-nav-header h1 {
    font-size: 1.65rem;
    font-weight: 800;
    color: var(--text-heading);
    margin: 0;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.t-nav-header-sub {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin: 4px 0 0 0;
    line-height: 1.4;
}

/* ── Empty state ───────────────────────────────────────────── */
.t-empty-state {
    text-align: center;
    padding: 60px 40px;
    animation: fadeInUp 0.4s ease both;
}
.t-empty-icon {
    font-size: 3.5rem;
    margin-bottom: 16px;
    line-height: 1;
}
.t-empty-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text-heading);
    margin: 0 0 8px 0;
}
.t-empty-text {
    font-size: 0.88rem;
    color: var(--text-secondary);
    max-width: 500px;
    margin: 0 auto;
    line-height: 1.55;
}

/* ── Step indicator ────────────────────────────────────────── */
.t-steps {
    display: flex;
    gap: 24px;
    justify-content: center;
    margin: 32px auto;
    max-width: 700px;
    flex-wrap: wrap;
}
.t-step {
    flex: 1;
    min-width: 180px;
    text-align: center;
    padding: 24px 16px;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    transition: border-color 0.2s;
}
.t-step:hover { border-color: var(--border-hover); }
.t-step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--accent-light));
    color: #0E1117;
    font-weight: 800;
    font-size: 0.85rem;
    margin-bottom: 12px;
}
.t-step-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 4px 0;
}
.t-step-desc {
    font-size: 0.73rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.4;
}

/* ── Page feature cards (onboarding) ───────────────────────── */
.t-feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin: 16px 0;
}
.t-feature-card {
    padding: 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    transition: border-color 0.2s;
}
.t-feature-card:hover { border-color: var(--border-hover); }
.t-feature-card-icon { font-size: 1.3rem; margin-bottom: 6px; }
.t-feature-card-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 4px 0;
}
.t-feature-card-desc {
    font-size: 0.72rem;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.4;
}

/* ── Chat bubbles ──────────────────────────────────────────── */
.t-chat-user {
    background: linear-gradient(135deg, rgba(0,180,216,0.15), rgba(0,180,216,0.06));
    border: 1px solid rgba(0,180,216,0.18);
    border-radius: var(--radius-md) var(--radius-md) 4px var(--radius-md);
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.88rem;
    color: var(--text-primary);
    line-height: 1.5;
}
.t-chat-assistant {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.88rem;
    color: var(--text-primary);
    line-height: 1.5;
}

/* ── Scrollable message list ───────────────────────────────── */
.t-msg-scroll {
    max-height: 600px;
    overflow-y: auto;
    padding-right: 4px;
}

/* ── Metric widget override ────────────────────────────────── */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.2s;
}
div[data-testid="stMetric"]:hover { border-color: var(--border-hover); }

/* ── Expander refinement ───────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--bg-card-alt) !important;
}

/* ── Tab refinement ────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    font-size: 1.05rem;
    font-weight: 600;
    padding: 10px 20px;
}

/* ── Button refinement ─────────────────────────────────────── */
.stApp button[kind="primary"] {
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* ── Powered-by badge ──────────────────────────────────────── */
.t-powered-by {
    text-align: center;
    font-size: 0.68rem;
    color: var(--text-secondary);
    opacity: 0.5;
    margin-top: 20px;
    letter-spacing: 0.3px;
}
</style>
"""

_LIGHT_OVERRIDES = """
<style>
:root {
    --bg-card: rgba(245, 247, 250, 0.85);
    --bg-card-alt: #FFFFFF;
    --bg-card-solid: #F5F7FA;
    --bg-page: #FFFFFF;
    --text-primary: #1a1a2e;
    --text-secondary: #5a6577;
    --text-heading: #1a1a2e;
    --border-subtle: rgba(0,0,0,0.07);
    --border-hover: rgba(0,180,216,0.35);
    --accent-glow: rgba(0,180,216,0.06);
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.10);
    --glass-blur: blur(0px);
}
.stApp { background-color: var(--bg-page); color: var(--text-primary); }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F5F7FA 0%, #EDF0F5 100%) !important;
    border-right: 1px solid rgba(0,0,0,0.06);
}
[data-testid="stSidebar"] * { color: var(--text-primary); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--text-heading); }
.stApp p, .stApp label { color: var(--text-primary); }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; }
[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }
[data-testid="stExpander"] {
    background-color: #FAFAFA !important;
    border-color: rgba(0,0,0,0.08) !important;
}
.kpi-card [data-testid="stMetricValue"] { color: var(--accent) !important; }
.kpi-card [data-testid="stMetric"]::before { background: linear-gradient(90deg, var(--accent), var(--accent-light)); }
.t-post-body, .t-msg-text, .t-quote { color: var(--text-primary); }
.t-status-dot.inactive { background: #ccd1d9; }
.t-chip { background: #F0F2F6; border-color: rgba(0,0,0,0.08); color: var(--text-primary); }
.t-chip:hover { background: rgba(0,180,216,0.06); border-color: var(--accent); color: var(--accent); }
.t-step { background: #F5F7FA; border-color: rgba(0,0,0,0.07); }
.t-feature-card { background: #F5F7FA; border-color: rgba(0,0,0,0.07); }
.t-chat-user { background: rgba(0,180,216,0.08); border-color: rgba(0,180,216,0.15); }
.t-chat-assistant { background: #F5F7FA; border-color: rgba(0,0,0,0.07); }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); }
::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.22); }
</style>
"""


def inject_global_css():
    """Call once per page, right after render_sidebar + apply_theme."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    if st.session_state.get("light_mode", False):
        st.markdown(_LIGHT_OVERRIDES, unsafe_allow_html=True)


# ── Reusable render helpers ────────────────────────────────────


def render_kpi_card(label: str, value: str, delta: float | None = None, help: str | None = None):
    """Styled KPI card using native st.metric for built-in tooltip support."""
    delta_str = None
    delta_color = "off"
    if delta is not None:
        if abs(delta) < 0.5:
            delta_str = f"→ {abs(delta):.1f}%"
            delta_color = "off"
        elif delta > 0:
            delta_str = f"{abs(delta):.1f}%"
            delta_color = "normal"
        else:
            delta_str = f"-{abs(delta):.1f}%"
            delta_color = "normal"

    kwargs = {"label": label, "value": value}
    if delta_str is not None:
        kwargs["delta"] = delta_str
        kwargs["delta_color"] = delta_color
    if help is not None:
        kwargs["help"] = help

    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.metric(**kwargs)
    st.markdown('</div>', unsafe_allow_html=True)


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
    likes: int = 0,
    shares: int = 0,
    comments: int = 0,
    views: int = 0,
):
    """Community message card with sentiment-colored left border."""
    from utils.charts import SENTIMENT_COLORS

    sent_color = SENTIMENT_COLORS.get(str(sentiment).lower(), "#808080")
    eng_str = f" · {engagements:,} eng" if engagements > 0 else ""
    breakdown_parts = []
    if likes > 0:
        breakdown_parts.append(f"♥ {likes:,}")
    if comments > 0:
        breakdown_parts.append(f"Comments {comments:,}")
    if shares > 0:
        breakdown_parts.append(f"↗ {shares:,}")
    if views > 0:
        breakdown_parts.append(f"Views {views:,}")
    breakdown_html = ""
    if breakdown_parts:
        breakdown_html = (
            f'<div style="font-size:0.72rem; color:var(--text-secondary); margin-top:4px;">'
            f'{" &nbsp;·&nbsp; ".join(breakdown_parts)}'
            f'</div>'
        )
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
        f'{breakdown_html}'
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
    gained: str | None = None,
    lost: str | None = None,
    video_view_rate: str | None = None,
):
    """Platform summary card for Platform Breakdown page."""
    extra_html = ""
    if gained is not None:
        extra_html += (
            f'<div class="t-platform-sub">'
            f'<div class="t-platform-label">GAINED</div>'
            f'<div style="font-size:0.9rem; font-weight:600; color:#2DC653;">+{gained}</div>'
            f'</div>'
        )
    if lost is not None:
        extra_html += (
            f'<div class="t-platform-sub">'
            f'<div class="t-platform-label">LOST</div>'
            f'<div style="font-size:0.9rem; font-weight:600; color:#EF476F;">-{lost}</div>'
            f'</div>'
        )
    if video_view_rate is not None:
        extra_html += (
            f'<div class="t-platform-sub">'
            f'<div class="t-platform-label">VIDEO VIEW RATE</div>'
            f'<div style="font-size:0.9rem; font-weight:600; color:var(--text-primary);">{video_view_rate}</div>'
            f'</div>'
        )
    st.markdown(
        f'<div class="t-platform" style="border-top: 3px solid {color};">'
        f'<div class="t-platform-name">{network}</div>'
        f'<div class="t-platform-label">AUDIENCE</div>'
        f'<div class="t-platform-value" style="color:{color};">{audience}</div>'
        f'<div class="t-platform-sub">'
        f'<div class="t-platform-label">NET GROWTH</div>'
        f'<div style="font-size:1rem; font-weight:600; color:var(--text-primary);">+{growth}</div>'
        f'</div>'
        f'{extra_html}'
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


# ── New render helpers ─────────────────────────────────────────


def render_card_container(title: str | None = None):
    """Open a styled card wrapper. Returns None — use with st.markdown for content."""
    title_html = f'<p class="t-card-container-title">{title}</p>' if title else ""
    st.markdown(
        f'<div class="t-card-container">{title_html}',
        unsafe_allow_html=True,
    )


def render_card_container_end():
    """Close a card container opened by render_card_container."""
    st.markdown("</div>", unsafe_allow_html=True)


def render_status_row(name: str, count: int | None = None, unit: str = ""):
    """Sidebar data-status row with coloured dot and optional count badge."""
    active = count is not None
    dot_cls = "active" if active else "inactive"
    name_cls = "active" if active else "inactive"
    badge = ""
    if active:
        badge = f'<span class="t-status-badge">{count:,} {unit}</span>'
    st.markdown(
        f'<div class="t-status-row">'
        f'<span class="t-status-dot {dot_cls}"></span>'
        f'<span class="t-status-name {name_cls}">{name}</span>'
        f'{badge}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_nav_header(title: str, subtitle: str | None = None):
    """Premium page header replacing st.title."""
    sub_html = f'<p class="t-nav-header-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="t-nav-header">'
        f'<h1>{title}</h1>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_empty_state(icon: str, title: str, text: str):
    """Centered empty-state placeholder."""
    st.markdown(
        f'<div class="t-empty-state">'
        f'<div class="t-empty-icon">{icon}</div>'
        f'<p class="t-empty-title">{title}</p>'
        f'<p class="t-empty-text">{text}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_steps(steps: list[tuple[str, str]]):
    """Numbered step cards. *steps* is [(label, description), ...]."""
    cards = ""
    for i, (label, desc) in enumerate(steps, 1):
        cards += (
            f'<div class="t-step">'
            f'<div class="t-step-num">{i}</div>'
            f'<p class="t-step-label">{label}</p>'
            f'<p class="t-step-desc">{desc}</p>'
            f'</div>'
        )
    st.markdown(f'<div class="t-steps">{cards}</div>', unsafe_allow_html=True)


def render_feature_grid(features: list[tuple[str, str, str]]):
    """Grid of feature cards. *features* is [(icon, title, desc), ...]."""
    cards = ""
    for icon, title, desc in features:
        cards += (
            f'<div class="t-feature-card">'
            f'<div class="t-feature-card-icon">{icon}</div>'
            f'<p class="t-feature-card-title">{title}</p>'
            f'<p class="t-feature-card-desc">{desc}</p>'
            f'</div>'
        )
    st.markdown(f'<div class="t-feature-grid">{cards}</div>', unsafe_allow_html=True)


def render_powered_by(text: str = "Powered by Gemini"):
    """Subtle footer badge."""
    st.markdown(f'<div class="t-powered-by">{text}</div>', unsafe_allow_html=True)
