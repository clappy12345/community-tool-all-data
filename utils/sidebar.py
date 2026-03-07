import streamlit as st
from utils.data_loader import (
    load_post_performance,
    load_profile_performance,
    load_affogata,
    load_inbox_export,
    load_looker_sentiment,
    check_default_data,
    load_all_defaults,
)
from utils.sample_data import generate_sample_data
from utils.titles import TITLES, DEFAULT_TITLE, get_title_config
from utils.data_store import (
    save_dataset,
    list_saved_datasets,
    load_saved_dataset,
    delete_saved_dataset,
    get_default_label,
)

def _auto_save(title_key):
    """Silently save the current session data so it survives page refresh."""
    try:
        label = get_default_label()
        save_dataset(label, title_key)
    except Exception:
        pass


_CLEAR_KEYS = [
    "post_performance", "profile_performance", "affogata", "inbox",
    "looker_sentiment",
    "themes", "classified_affogata", "classified_inbox", "chat_messages",
    "conversation_drivers", "full_report",
    "full_report_exec", "full_report_perf", "full_report_themes", "full_report_drivers",
    "compare_narrative", "ai_topic_buckets",
    "filter_date_range", "filter_networks",
]


def render_sidebar():
    with st.sidebar:
        if "active_title" not in st.session_state:
            st.session_state["active_title"] = DEFAULT_TITLE

        title_options = list(TITLES.keys())
        labels = [f"{TITLES[k]['icon']} {TITLES[k]['full_name']}" for k in title_options]
        current_idx = title_options.index(st.session_state["active_title"])

        selected_label = st.selectbox("Title", labels, index=current_idx)
        selected_key = title_options[labels.index(selected_label)]

        if selected_key != st.session_state["active_title"]:
            for key in _CLEAR_KEYS:
                st.session_state.pop(key, None)
            st.session_state["active_title"] = selected_key
            st.rerun()

        cfg = get_title_config()
        st.markdown(f"## {cfg['icon']} {cfg['full_name']} Community Insights")
        st.divider()

        has_data = "post_performance" in st.session_state and st.session_state["post_performance"] is not None
        title_key = st.session_state["active_title"]

        # ── Upload / Save Data ──────────────────────────────────
        with st.expander("Upload Data", expanded=not has_data):
            if has_data:
                st.success("Data loaded")

                save_label = st.text_input("Dataset label", value=get_default_label(), key="save_label")
                if st.button("Save Dataset", use_container_width=True):
                    with st.spinner("Saving..."):
                        save_dataset(save_label, title_key)
                    st.success(f"Saved: **{save_label}**")

                if st.button("Clear & Re-upload", use_container_width=True):
                    for key in _CLEAR_KEYS:
                        st.session_state.pop(key, None)
                    st.rerun()
            else:
                defaults = check_default_data()
                if defaults:
                    st.info(f"Found {len(defaults)} data file(s)")
                    if st.button("Load Desktop Data", type="primary", use_container_width=True):
                        with st.spinner("Loading data files..."):
                            loaded = load_all_defaults()
                            for k, v in loaded.items():
                                if v is not None:
                                    st.session_state[k] = v
                        _auto_save(title_key)
                        st.rerun()

                if st.button("Load Sample Data", use_container_width=True):
                    with st.spinner("Generating sample data..."):
                        for k, v in generate_sample_data(st.session_state["active_title"]).items():
                            st.session_state[k] = v
                    _auto_save(title_key)
                    st.rerun()

                st.markdown("**— or upload manually —**")

                pp = st.file_uploader("Post Performance (Sprout)", type=["csv"], key="pp_up")
                prof = st.file_uploader("Profile Performance (Sprout)", type=["csv"], key="prof_up")
                aff = st.file_uploader("Affogata Export", type=["csv"], key="aff_up")
                inbox = st.file_uploader("Inbox Export (Sprout)", type=["csv", "zip"], key="inbox_up")
                looker = st.file_uploader("Looker Sentiment Score", type=["csv"], key="looker_up")

                any_new = False
                if pp:
                    result = load_post_performance(pp.read(), pp.name)
                    if result is not None:
                        st.session_state["post_performance"] = result
                        any_new = True
                    pp.seek(0)
                if prof:
                    result = load_profile_performance(prof.read(), prof.name)
                    if result is not None:
                        st.session_state["profile_performance"] = result
                        any_new = True
                    prof.seek(0)
                if aff:
                    result = load_affogata(aff.read(), aff.name)
                    if result is not None:
                        st.session_state["affogata"] = result
                        any_new = True
                    aff.seek(0)
                if inbox:
                    result = load_inbox_export(inbox.read(), inbox.name)
                    if result is not None:
                        st.session_state["inbox"] = result
                        any_new = True
                    inbox.seek(0)
                if looker:
                    result = load_looker_sentiment(looker.read(), looker.name)
                    if result is not None:
                        st.session_state["looker_sentiment"] = result
                        any_new = True
                    looker.seek(0)

                if any_new:
                    _auto_save(title_key)

        # ── Saved Datasets ──────────────────────────────────────
        saved = list_saved_datasets(title_key)
        with st.expander(f"Saved Datasets ({len(saved)})", expanded=False):
            if not saved:
                st.caption("No saved datasets yet. Load data and click **Save Dataset** above.")
            else:
                for ds in saved:
                    dr = ds.get("date_range")
                    dr_str = f"{dr[0]} to {dr[1]}" if dr else "unknown range"
                    rc = ds.get("row_counts", {})

                    parts = []
                    if rc.get("post_performance"):
                        parts.append(f"{rc['post_performance']:,} posts")
                    if rc.get("profile_performance"):
                        parts.append(f"{rc['profile_performance']:,} profile")
                    if rc.get("affogata"):
                        parts.append(f"{rc['affogata']:,} community")
                    if rc.get("inbox"):
                        parts.append(f"{rc['inbox']:,} inbox")
                    detail_str = ", ".join(parts) if parts else "no data"

                    col_load, col_del = st.columns([4, 1])
                    with col_load:
                        if st.button(
                            f"📂 {ds['label']}",
                            key=f"load_{ds['label']}",
                            use_container_width=True,
                        ):
                            with st.spinner(f"Loading {ds['label']}..."):
                                loaded = load_saved_dataset(title_key, ds["label"])
                                for key in _CLEAR_KEYS:
                                    st.session_state.pop(key, None)
                                for k, v in loaded.items():
                                    st.session_state[k] = v
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_{ds['label']}", help="Delete this dataset"):
                            delete_saved_dataset(title_key, ds["label"])
                            st.rerun()

                    st.caption(f"{dr_str} — {detail_str}")

        # ── Data Status ─────────────────────────────────────────
        st.markdown("### Data Status")
        sources = {
            "post_performance": ("Post Performance", "posts"),
            "profile_performance": ("Profile Performance", "records"),
            "affogata": ("Affogata", "conversations"),
            "inbox": ("Inbox Export", "messages"),
            "looker_sentiment": ("Looker Sentiment", "days"),
        }
        for key, (name, unit) in sources.items():
            df = st.session_state.get(key)
            if df is not None:
                count = len(df)
                st.caption(f"✅ {name}: {count:,} {unit}")
            else:
                st.caption(f"⬜ {name}")

        # ── Theme Toggle ─────────────────────────────────────────
        st.divider()
        theme = st.toggle("Light mode", value=st.session_state.get("light_mode", False), key="light_mode")

        # ── Filters ─────────────────────────────────────────────
        filters = {}
        if has_data:
            st.divider()
            st.markdown("### Filters")
            pp = st.session_state["post_performance"]

            min_date = pp["Date"].min().date()
            max_date = pp["Date"].max().date()

            if "filter_date_range" not in st.session_state:
                st.session_state["filter_date_range"] = (min_date, max_date)

            date_range = st.date_input(
                "Date Range",
                value=st.session_state["filter_date_range"],
                min_value=min_date,
                max_value=max_date,
                key="filter_date_range",
            )
            filters["date_range"] = date_range

            network_set = set(pp["Network"].unique())
            aff_df = st.session_state.get("affogata")
            if aff_df is not None and "Network Name" in aff_df.columns:
                network_set.update(aff_df["Network Name"].dropna().unique())
            inbox_df = st.session_state.get("inbox")
            if inbox_df is not None and "Network" in inbox_df.columns:
                network_set.update(inbox_df["Network"].dropna().unique())
            all_networks = sorted(network_set)

            if "filter_networks" not in st.session_state:
                st.session_state["filter_networks"] = all_networks

            selected = st.multiselect(
                "Platforms", all_networks,
                default=st.session_state["filter_networks"],
                key="filter_networks",
            )
            filters["networks"] = selected

        return filters


_LIGHT_CSS = """
<style>
    .stApp { background-color: #FFFFFF; color: #1a1a2e; }
    [data-testid="stSidebar"] { background-color: #F0F2F6; }
    [data-testid="stSidebar"] * { color: #1a1a2e; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #1a1a2e; }
    .stApp p, .stApp span, .stApp label, .stApp div { color: #1a1a2e; }
    [data-testid="stMetricValue"] { color: #1a1a2e !important; }
    [data-testid="stMetricLabel"] { color: #555 !important; }
    .stApp .stCaption { color: #666; }
    [data-testid="stExpander"] { background-color: #F9F9F9; border-color: #ddd; }
    .stSelectbox label, .stMultiSelect label { color: #1a1a2e; }
    .stDataFrame { color: #1a1a2e; }
    [data-testid="stMarkdownContainer"] div[style*="background:#1A1D23"],
    [data-testid="stMarkdownContainer"] div[style*="background:#12141A"],
    [data-testid="stMarkdownContainer"] div[style*="background:#252830"] {
        background: #F5F7FA !important;
        color: #1a1a2e !important;
    }
    [data-testid="stMarkdownContainer"] div[style*="background:#1A1D23"] span,
    [data-testid="stMarkdownContainer"] div[style*="background:#12141A"] span,
    [data-testid="stMarkdownContainer"] div[style*="background:#252830"] span {
        color: #1a1a2e !important;
    }
</style>
"""


def apply_theme():
    """Inject light-mode CSS if the toggle is active."""
    if st.session_state.get("light_mode", False):
        st.markdown(_LIGHT_CSS, unsafe_allow_html=True)


def require_data():
    if "post_performance" not in st.session_state or st.session_state["post_performance"] is None:
        st.warning("Please upload data on the **Home** page first.")
        st.stop()
