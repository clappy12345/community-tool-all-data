import pandas as pd
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
from utils.sample_data import generate_sample_data, generate_sample_saved_campaigns
from utils.titles import TITLES, DEFAULT_TITLE, get_title_config
from utils.data_store import (
    save_dataset,
    list_saved_datasets,
    load_saved_dataset,
    delete_saved_dataset,
    get_default_label,
    update_dataset_phases,
    update_dataset_events,
)
from utils.theme import render_status_row

def _auto_save(title_key):
    """Silently save the current session data so it survives page refresh."""
    try:
        label = get_default_label()
        events_draft = st.session_state.get("campaign_events_draft", [])
        events = [e for e in events_draft if e.get("name", "").strip()]
        save_dataset(label, title_key, campaign_events=events if events else None)
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
        st.markdown(
            f'<div style="padding:4px 0 8px 0;">'
            f'<span style="font-size:1.4rem;">{cfg["icon"]}</span> '
            f'<span style="font-size:1.05rem; font-weight:700; letter-spacing:-0.01em;">'
            f'{cfg["full_name"]}</span>'
            f'<br><span style="font-size:0.7rem; color:var(--text-secondary); '
            f'text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">'
            f'Community Insights</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        has_data = "post_performance" in st.session_state and st.session_state["post_performance"] is not None
        title_key = st.session_state["active_title"]

        # ── Filters (date range + platforms) ─────────────────────
        filters = {}
        if has_data:
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

        st.divider()

        # ── Upload / Save Data ──────────────────────────────────
        with st.expander("Upload Data", expanded=not has_data):
            if has_data:
                st.success("Data loaded")

                save_label = st.text_input("Dataset label", value=get_default_label(), key="save_label")

                _title_cfg = TITLES.get(title_key, TITLES[DEFAULT_TITLE])
                _gv_col, _ct_col = st.columns(2)
                with _gv_col:
                    game_version = st.text_input(
                        "Game version",
                        value=_title_cfg["full_name"],
                        help="e.g. NHL 25, NHL 26, UFC 5",
                        key="save_game_version",
                    )
                with _ct_col:
                    _CAMPAIGN_TYPES = [
                        "Cover Reveal", "Launch Week", "Beta / Early Access",
                        "Full Season", "Other",
                    ]
                    campaign_type = st.selectbox(
                        "Campaign type",
                        _CAMPAIGN_TYPES,
                        help="What phase of the marketing cycle is this data from?",
                        key="save_campaign_type",
                    )

                pp_dates = st.session_state["post_performance"]
                _min_d = pp_dates["Date"].min().date()
                campaign_date = st.date_input(
                    "Campaign start (Day 0)",
                    value=_min_d,
                    help="Anchor date for relative-day comparisons (e.g. reveal day, launch day)",
                    key="save_campaign_start",
                )

                # ── AI Campaign Phase Detection ──────────────
                if st.button("Auto-detect campaign phases", use_container_width=True, type="secondary"):
                    from utils.ai_analysis import detect_campaign_phases
                    with st.spinner("Analyzing data + searching the web for campaign dates..."):
                        phases = detect_campaign_phases(pp_dates)
                        if phases:
                            st.session_state["detected_phases"] = phases
                        else:
                            st.warning("Could not detect campaign phases. You can add them manually below.")
                            st.session_state["detected_phases"] = []

                detected = st.session_state.get("detected_phases")
                phases_to_save = []
                if detected is not None:
                    if len(detected) > 0:
                        st.caption(f"**{len(detected)} phase(s) detected** — edit names/dates below:")
                        for i, phase in enumerate(detected):
                            conf = phase.get("confidence", "")
                            conf_icon = {"high": "H", "medium": "M", "low": "L"}.get(conf, "-")
                            pc1, pc2, pc3 = st.columns([3, 2, 2])
                            with pc1:
                                name = st.text_input(
                                    "Phase", value=phase["name"],
                                    key=f"phase_name_{i}", label_visibility="collapsed",
                                )
                            with pc2:
                                start = st.date_input(
                                    "Start", value=pd.Timestamp(phase["start"]).date(),
                                    key=f"phase_start_{i}", label_visibility="collapsed",
                                )
                            with pc3:
                                end = st.date_input(
                                    "End", value=pd.Timestamp(phase.get("end", phase["start"])).date(),
                                    key=f"phase_end_{i}", label_visibility="collapsed",
                                )
                            evidence = phase.get("evidence", "")
                            if evidence:
                                st.caption(f"{conf_icon} {evidence}")
                            phases_to_save.append({
                                "name": name,
                                "start": start.strftime("%Y-%m-%d"),
                                "end": end.strftime("%Y-%m-%d"),
                            })
                    else:
                        st.caption("No phases detected. Save without phases or try again.")

                # ── Campaign Events (milestones) ──────────────
                st.markdown(
                    '<p style="font-size:0.72rem; text-transform:uppercase; '
                    'letter-spacing:0.8px; color:var(--text-secondary); '
                    'font-weight:600; margin:12px 0 4px 0;">Campaign Events</p>',
                    unsafe_allow_html=True,
                )
                st.caption("Mark key moments (reveal, trailer, launch) so they appear as indicators on charts.")

                if "campaign_events_draft" not in st.session_state:
                    st.session_state["campaign_events_draft"] = []

                _EVENT_COLORS = [
                    "#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3",
                    "#F38181", "#AA96DA", "#FCBAD3", "#A8D8EA",
                ]

                events_draft = st.session_state["campaign_events_draft"]
                events_to_remove = []
                for ei, ev in enumerate(events_draft):
                    ec1, ec2, ec3 = st.columns([3, 2, 1])
                    with ec1:
                        ev["name"] = st.text_input(
                            "Event", value=ev.get("name", ""),
                            key=f"evt_name_{ei}", label_visibility="collapsed",
                            placeholder="e.g. Cover Reveal",
                        )
                    with ec2:
                        ev["date"] = st.date_input(
                            "Date", value=pd.Timestamp(ev["date"]).date() if ev.get("date") else _min_d,
                            key=f"evt_date_{ei}", label_visibility="collapsed",
                        ).strftime("%Y-%m-%d")
                    with ec3:
                        if st.button("✕", key=f"evt_del_{ei}", help="Remove event"):
                            events_to_remove.append(ei)

                if events_to_remove:
                    for idx in sorted(events_to_remove, reverse=True):
                        events_draft.pop(idx)
                    st.session_state["campaign_events_draft"] = events_draft
                    st.rerun()

                if st.button("＋ Add Event", key="add_campaign_event", use_container_width=True):
                    color = _EVENT_COLORS[len(events_draft) % len(_EVENT_COLORS)]
                    events_draft.append({"name": "", "date": _min_d.strftime("%Y-%m-%d"), "color": color})
                    st.session_state["campaign_events_draft"] = events_draft
                    st.rerun()

                events_to_save = [
                    {"name": e["name"], "date": e["date"], "color": _EVENT_COLORS[i % len(_EVENT_COLORS)]}
                    for i, e in enumerate(events_draft) if e.get("name", "").strip()
                ]

                if st.button("Save Dataset", use_container_width=True):
                    cs_str = campaign_date.strftime("%Y-%m-%d") if campaign_date else None
                    with st.spinner("Saving..."):
                        save_dataset(
                            save_label, title_key,
                            campaign_start=cs_str,
                            campaign_phases=phases_to_save if phases_to_save else None,
                            campaign_events=events_to_save if events_to_save else None,
                            game_version=game_version or None,
                            campaign_type=campaign_type or None,
                        )
                    st.success(f"Saved: **{save_label}**")

                if st.button("Clear & Re-upload", use_container_width=True):
                    for key in _CLEAR_KEYS:
                        st.session_state.pop(key, None)
                    st.session_state.pop("detected_phases", None)
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
                        generate_sample_saved_campaigns(st.session_state["active_title"])
                    _auto_save(title_key)
                    st.rerun()

                st.markdown(
                    '<div style="text-align:center; margin:12px 0 8px; font-size:0.72rem; '
                    'color:var(--text-secondary); text-transform:uppercase; letter-spacing:1px; '
                    'font-weight:600;">or upload manually</div>',
                    unsafe_allow_html=True,
                )

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
                            f"{ds['label']}",
                            key=f"load_{ds['label']}",
                            use_container_width=True,
                        ):
                            with st.spinner(f"Loading {ds['label']}..."):
                                loaded = load_saved_dataset(title_key, ds["label"])
                                for key in _CLEAR_KEYS:
                                    st.session_state.pop(key, None)
                                for k, v in loaded.items():
                                    st.session_state[k] = v
                                st.session_state["campaign_events_draft"] = ds.get("campaign_events", [])
                            st.rerun()
                    with col_del:
                        if st.button("Delete", key=f"del_{ds['label']}", help="Delete this dataset"):
                            delete_saved_dataset(title_key, ds["label"])
                            st.rerun()

                    cs = ds.get("campaign_start")
                    cs_str = f" · Day 0: {cs}" if cs else ""
                    n_phases = len(ds.get("campaign_phases", []))
                    phase_str = f" · {n_phases} phase{'s' if n_phases != 1 else ''}" if n_phases > 0 else ""
                    n_events = len(ds.get("campaign_events", []))
                    event_str = f" · {n_events} event{'s' if n_events != 1 else ''}" if n_events > 0 else ""
                    st.caption(f"{dr_str}{cs_str}{phase_str}{event_str} — {detail_str}")

        # ── Data Status ─────────────────────────────────────────
        st.markdown(
            '<p style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.8px; '
            'color:var(--text-secondary); font-weight:600; margin:12px 0 6px 0;">Data Sources</p>',
            unsafe_allow_html=True,
        )
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
                render_status_row(name, count=len(df), unit=unit)
            else:
                render_status_row(name)

        # ── Theme Toggle ─────────────────────────────────────────
        st.markdown("")
        theme = st.toggle("Light mode", value=st.session_state.get("light_mode", False), key="light_mode")

        return filters


def apply_theme():
    """Inject global CSS (and light-mode overrides if toggled).

    Delegates to utils.theme.inject_global_css() which handles both modes
    via CSS custom properties.
    """
    from utils.theme import inject_global_css
    inject_global_css()


def require_data():
    if "post_performance" not in st.session_state or st.session_state["post_performance"] is None:
        st.warning("Please upload data on the **Home** page first.")
        st.stop()
