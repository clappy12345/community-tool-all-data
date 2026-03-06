import streamlit as st
from utils.data_loader import (
    load_post_performance,
    load_profile_performance,
    load_affogata,
    load_inbox_export,
    check_default_data,
    load_all_defaults,
)


def render_sidebar():
    with st.sidebar:
        st.markdown("## NHL Community Insights")
        st.divider()

        has_data = "post_performance" in st.session_state and st.session_state["post_performance"] is not None

        # --- Data Upload ---
        with st.expander("Upload Data", expanded=not has_data):
            if has_data:
                st.success("Data loaded")
                if st.button("Clear & Re-upload", use_container_width=True):
                    for key in [
                        "post_performance",
                        "profile_performance",
                        "affogata",
                        "inbox",
                        "themes",
                        "classified_affogata",
                        "classified_inbox",
                    ]:
                        st.session_state.pop(key, None)
                    st.rerun()
            else:
                defaults = check_default_data()
                if defaults:
                    st.info(f"Found {len(defaults)} data file(s) on Desktop")
                    if st.button("Load Desktop Data", type="primary", use_container_width=True):
                        with st.spinner("Loading data files..."):
                            loaded = load_all_defaults()
                            for k, v in loaded.items():
                                st.session_state[k] = v
                        st.rerun()

                    st.markdown("**— or upload manually —**")

                pp = st.file_uploader("Post Performance (Sprout)", type=["csv"], key="pp_up")
                prof = st.file_uploader("Profile Performance (Sprout)", type=["csv"], key="prof_up")
                aff = st.file_uploader("Affogata Export", type=["csv"], key="aff_up")
                inbox = st.file_uploader("Inbox Export (Sprout)", type=["csv", "zip"], key="inbox_up")

                if pp:
                    st.session_state["post_performance"] = load_post_performance(
                        pp.read(), pp.name
                    )
                    pp.seek(0)
                if prof:
                    st.session_state["profile_performance"] = load_profile_performance(
                        prof.read(), prof.name
                    )
                    prof.seek(0)
                if aff:
                    st.session_state["affogata"] = load_affogata(aff.read(), aff.name)
                    aff.seek(0)
                if inbox:
                    st.session_state["inbox"] = load_inbox_export(
                        inbox.read(), inbox.name
                    )
                    inbox.seek(0)

        # --- Data Status ---
        st.markdown("### Data Status")
        sources = {
            "post_performance": ("Post Performance", "posts"),
            "profile_performance": ("Profile Performance", "records"),
            "affogata": ("Affogata", "conversations"),
            "inbox": ("Inbox Export", "messages"),
        }
        for key, (name, unit) in sources.items():
            df = st.session_state.get(key)
            if df is not None:
                count = len(df)
                st.caption(f"✅ {name}: {count:,} {unit}")
            else:
                st.caption(f"⬜ {name}")

        # --- Filters ---
        filters = {}
        if has_data:
            st.divider()
            st.markdown("### Filters")
            pp = st.session_state["post_performance"]

            min_date = pp["Date"].min().date()
            max_date = pp["Date"].max().date()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            filters["date_range"] = date_range

            all_networks = sorted(pp["Network"].unique().tolist())
            selected = st.multiselect("Platforms", all_networks, default=all_networks)
            filters["networks"] = selected

        return filters


def require_data():
    if "post_performance" not in st.session_state or st.session_state["post_performance"] is None:
        st.warning("Please upload data on the **Home** page first.")
        st.stop()
