import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Community Insights",
    page_icon="CI",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.sidebar import render_sidebar, apply_theme
from utils.processors import (
    apply_filters,
    format_number,
    get_kpis_safe,
    get_daily_metrics,
    get_top_posts,
    get_top_conversation_topics,
    combine_community_messages,
    get_messages_around_beat,
)
from utils.titles import get_title_config
from utils.charts import (
    daily_bar,
    looker_sentiment_timeline,
    topic_percentage_bar,
    CHART_CONFIG,
    SENTIMENT_COLORS,
)
from utils.ai_analysis import discover_topic_buckets, load_saved_topic_buckets
from utils.data_store import list_saved_datasets
from utils.theme import (
    inject_global_css,
    render_kpi_card,
    render_post_card,
    render_message_card,
    render_section_header,
    render_nav_header,
    render_empty_state,
    render_steps,
    render_feature_grid,
)

filters = render_sidebar()
apply_theme()
cfg = get_title_config()

_icon_prefix = f"{cfg['icon']} " if cfg['icon'] else ""
render_nav_header(
    f"{_icon_prefix}{cfg['full_name']} Dashboard",
    "Social performance + community snapshot — all in one view",
)
st.markdown("")

has_data = "post_performance" in st.session_state and st.session_state["post_performance"] is not None


def _compute_period_deltas(pp_current, pp_full):
    """Compare current period vs. the equivalent prior period of the same length."""
    current_start = pp_current["Date"].min()
    current_end = pp_current["Date"].max()
    period_days = (current_end - current_start).days + 1

    prior_end = current_start - pd.Timedelta(days=1)
    prior_start = prior_end - pd.Timedelta(days=period_days - 1)

    pp_prior = pp_full[
        (pp_full["Date"] >= prior_start) & (pp_full["Date"] <= prior_end)
    ]
    if len(pp_prior) == 0:
        return {}, 0

    metrics = {
        "total_impressions": ("Impressions", "sum"),
        "total_engagements": ("Engagements", "sum"),
        "total_video_views": ("Video Views", "sum"),
        "total_posts": (None, "count"),
        "total_comments": ("Comments", "sum"),
        "total_shares": ("Shares", "sum"),
    }
    if "Reach" in pp_current.columns:
        metrics["total_reach"] = ("Reach", "sum")
    if "Saves" in pp_current.columns:
        metrics["total_saves"] = ("Saves", "sum")
    if "Post Link Clicks" in pp_current.columns:
        metrics["total_link_clicks"] = ("Post Link Clicks", "sum")

    deltas = {}
    for key, (col, agg) in metrics.items():
        if agg == "count":
            v_prior, v_current = len(pp_prior), len(pp_current)
        else:
            v_prior, v_current = pp_prior[col].sum(), pp_current[col].sum()
        if v_prior > 0:
            deltas[key] = ((v_current - v_prior) / v_prior) * 100
        else:
            deltas[key] = 0.0
    return deltas, period_days


if has_data:
    pp_full = st.session_state["post_performance"]
    pp = apply_filters(pp_full, filters)
    prof_raw = st.session_state.get("profile_performance")
    prof = apply_filters(prof_raw, filters) if prof_raw is not None else None
    aff_raw = st.session_state.get("affogata")
    inbox_raw = st.session_state.get("inbox")
    looker_raw = st.session_state.get("looker_sentiment")

    aff = (
        apply_filters(aff_raw, filters, date_col="Created At", network_col="Network Name")
        if aff_raw is not None
        else None
    )

    # Filter Looker sentiment by date range
    looker = looker_raw
    if looker_raw is not None and "date_range" in filters and filters["date_range"]:
        dr = filters["date_range"]
        if isinstance(dr, (list, tuple)) and len(dr) == 2:
            looker = looker_raw[
                (looker_raw["Date"].dt.date >= dr[0])
                & (looker_raw["Date"].dt.date <= dr[1])
            ]

    kpis = get_kpis_safe(pp, prof)
    deltas, period_days = _compute_period_deltas(pp, pp_full)

    date_min = pp["Date"].min().strftime("%b %d, %Y")
    date_max = pp["Date"].max().strftime("%b %d, %Y")

    # ── KPI Dashboard ──────────────────────────────────────────
    # Detect active campaign phase from saved datasets
    _title_key = st.session_state.get("active_title", "NHL")
    _active_phase_label = ""
    _all_saved = list_saved_datasets(_title_key)
    _current_phases = []
    for _ds in _all_saved:
        _dr = _ds.get("date_range")
        if _dr and _dr[0] == pp["Date"].min().strftime("%Y-%m-%d") and _dr[1] == pp["Date"].max().strftime("%Y-%m-%d"):
            _current_phases = _ds.get("campaign_phases", [])
            break
    if _current_phases:
        _cur_start = pp["Date"].min().date()
        _cur_end = pp["Date"].max().date()
        for _ph in _current_phases:
            _ph_start = pd.Timestamp(_ph["start"]).date()
            _ph_end = pd.Timestamp(_ph.get("end", _ph["start"])).date()
            if _ph_start >= _cur_start and _ph_end <= _cur_end:
                _day0 = (_ph_start - _cur_start).days
                _dayN = (_ph_end - _cur_start).days
                _active_phase_label = f" · *{_ph['name']} (Days {_day0}–{_dayN})*"
                break

    render_section_header(f"Reporting Period: {date_min} — {date_max}{_active_phase_label}")

    def _delta(key):
        return deltas.get(key)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("Total Impressions", format_number(kpis["total_impressions"]), _delta("total_impressions"),
                        help="Total number of times your content was displayed on screen, including repeat views by the same user.")
    with c2:
        render_kpi_card("Total Engagements", format_number(kpis["total_engagements"]), _delta("total_engagements"),
                        help="Sum of all interactions (likes, comments, shares, clicks, saves) across your posts.")
    with c3:
        render_kpi_card("Engagement Rate", f"{kpis['avg_engagement_rate']:.2f}%",
                        help="Average engagements per impression, expressed as a percentage. Higher = more compelling content.")
    with c4:
        render_kpi_card("Video Views", format_number(kpis.get("total_video_views", pp["Video Views"].sum())), _delta("total_video_views"),
                        help="Total number of times your videos were watched. View thresholds vary by platform (e.g. 3s on most).")
    with c5:
        growth = kpis.get("audience_growth", 0)
        render_kpi_card("Audience Growth", f"{'+' if growth > 0 else ''}{format_number(growth)}",
                        help="Net change in followers/subscribers during this period.")

    st.markdown("")
    c6, c7, c8, c9, c10 = st.columns(5)
    with c6:
        render_kpi_card("Total Posts", f"{int(kpis['total_posts']):,}", _delta("total_posts"),
                        help="Number of posts published across all platforms in the selected date range.")
    with c7:
        render_kpi_card("Total Reach", format_number(kpis.get("total_reach", 0)), _delta("total_reach"),
                        help="Number of unique users who saw your content at least once. Unlike impressions, each person is counted only once.")
    with c8:
        render_kpi_card("Comments", format_number(kpis.get("total_comments", 0)), _delta("total_comments"),
                        help="Total comments and replies left on your posts across all platforms.")
    with c9:
        render_kpi_card("Shares", format_number(kpis.get("total_shares", 0)), _delta("total_shares"),
                        help="Number of times users shared your content (retweets, reposts, shares, sends).")
    with c10:
        aud = kpis.get("total_audience", 0)
        render_kpi_card("Total Audience", format_number(aud) if aud > 0 else "N/A",
                        help="Current total follower/subscriber count across all connected platforms.")

    st.markdown("")
    c11, c12, c13, c14, c15 = st.columns(5)
    with c11:
        render_kpi_card("Saves", format_number(kpis.get("total_saves", 0)), _delta("total_saves"),
                        help="Number of times users bookmarked or saved your posts for later. A strong signal of high-value content.")
    with c12:
        render_kpi_card("Link Clicks", format_number(kpis.get("total_link_clicks", 0)), _delta("total_link_clicks"),
                        help="Number of clicks on links included in your posts (e.g. URLs, CTAs, link stickers).")
    with c13:
        vvr = kpis.get("video_view_rate", 0)
        render_kpi_card("Video View Rate", f"{vvr:.1f}%" if vvr > 0 else "N/A",
                        help="Percentage of impressions that resulted in a video view. Higher = stronger stop-scroll power.")
    with c14:
        st.empty()
    with c15:
        st.empty()

    if period_days > 0 and len(deltas) > 0:
        st.caption(f"*Trends vs. prior {period_days}-day period*")
    else:
        st.caption("*No prior period data available for trend comparison*")

    # ── Sentiment Numbers (inline with KPIs) ───────────────────
    if looker is not None and len(looker) > 0:
        avg_score = looker["Impact Score"].mean()
        max_row = looker.loc[looker["Impact Score"].idxmax()]
        min_row = looker.loc[looker["Impact Score"].idxmin()]

        st.markdown("")
        render_section_header("Sentiment Snapshot")
        s1, s2, s3 = st.columns(3)
        s1.metric("Avg Impact Score", f"{avg_score:.1f}")
        s2.metric("Highest", f"{max_row['Impact Score']:.1f}", help=max_row["Date"].strftime("%b %d"))
        s3.metric("Lowest", f"{min_row['Impact Score']:.1f}", help=min_row["Date"].strftime("%b %d"))

    st.markdown("")

    # ── Charts Section ─────────────────────────────────────────

    # Daily Impressions
    if prof is not None and len(prof) > 0:
        daily = get_daily_metrics(prof)
        fig = daily_bar(daily, "Impressions", "Daily Impressions")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

    # Sentiment Timeline
    if looker is not None and len(looker) > 0:
        fig = looker_sentiment_timeline(looker, "Daily Sentiment Score")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

    st.markdown("")

    # ── What the Community Is Talking About ────────────────────
    if aff is not None or inbox_raw is not None:
        ai_buckets = st.session_state.get("ai_topic_buckets")
        if ai_buckets is None:
            ai_buckets = load_saved_topic_buckets()
            if ai_buckets is not None:
                st.session_state["ai_topic_buckets"] = ai_buckets
        using_ai = ai_buckets is not None
        buckets_to_use = ai_buckets if using_ai else None

        combined_for_topics = combine_community_messages(aff, inbox_raw)
        has_msgs = len(combined_for_topics) > 10 if combined_for_topics is not None else False

        _h_left, _h_right = st.columns([4, 1])
        with _h_left:
            st.markdown("### What the Community Is Talking About")
        with _h_right:
            if has_msgs:
                refresh_topics = st.button(
                    "Refresh with AI" if not using_ai else "Re-discover",
                    type="secondary",
                    use_container_width=True,
                    key="home_btn_refresh_topics",
                )
            else:
                refresh_topics = False

        topics_df = get_top_conversation_topics(aff, inbox_raw, buckets=buckets_to_use)
        if topics_df is not None and len(topics_df) > 0:
            source_label = "AI-discovered topics" if using_ai else f"Default {cfg['name']} topic buckets"
            st.caption(f"% of messages matching each topic — {source_label}.")
            fig_topics = topic_percentage_bar(topics_df)
            st.plotly_chart(fig_topics, use_container_width=True, config=CHART_CONFIG)

            other_row = topics_df[topics_df["Topic"] == "Other / Uncategorized"]
            if not using_ai and len(other_row) > 0 and other_row.iloc[0]["Pct"] > 25:
                st.info(
                    f"{other_row.iloc[0]['Pct']:.0f}% of messages didn't match any predefined topic. "
                    "Click **Refresh with AI** to discover what else the community is talking about."
                )

        if refresh_topics:
            with st.spinner("Discovering topics from community messages..."):
                new_buckets = discover_topic_buckets(combined_for_topics)
                if new_buckets:
                    st.session_state["ai_topic_buckets"] = new_buckets
                    st.rerun()
                else:
                    st.error("Could not discover topics. Check your Google API key.")

        st.markdown("")

    # ── Posts by Impressions (paginated, grouped cross-platform) ───
    render_section_header("Top Posts by Impressions", "Posts shared across channels are grouped. Expand for per-channel metrics + community messages.")

    exclude_types = ["Story", "@Reply", "'@Reply"]
    pp_clean = pp[~pp["Post Type"].isin(exclude_types)].copy()
    pp_clean["_post_key"] = pp_clean["Post"].fillna("").str.strip().str[:120]
    pp_clean["_date_key"] = pp_clean["Date"].dt.normalize()

    grouped = (
        pp_clean.groupby(["_date_key", "_post_key"])
        .agg(
            Combined_Impressions=("Impressions", "sum"),
            Combined_Engagements=("Engagements", "sum"),
            Channels=("Network", lambda x: list(x)),
            _indices=("Impressions", lambda x: list(x.index)),
        )
        .reset_index()
        .sort_values("Combined_Impressions", ascending=False)
        .reset_index(drop=True)
    )

    POSTS_PER_PAGE = 5
    total_posts_count = len(grouped)
    total_pages = max(1, (total_posts_count + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)

    if "posts_page" not in st.session_state:
        st.session_state["posts_page"] = 1
    current_page = st.session_state["posts_page"]
    current_page = min(current_page, total_pages)

    start_idx = (current_page - 1) * POSTS_PER_PAGE
    end_idx = min(start_idx + POSTS_PER_PAGE, total_posts_count)
    page_slice = grouped.iloc[start_idx:end_idx]

    st.caption(f"Showing {start_idx + 1}–{end_idx} of {total_posts_count} posts")

    for rank_offset, (_, grp) in enumerate(page_slice.iterrows()):
        rank = start_idx + rank_offset + 1
        post_text = str(grp["_post_key"])[:200]
        date_str = grp["_date_key"].strftime("%b %d, %Y")
        channels = grp["Channels"]
        indices = grp["_indices"]
        total_imp = int(grp["Combined_Impressions"])
        total_eng = int(grp["Combined_Engagements"])
        n_channels = len(channels)
        channel_str = " + ".join(sorted(set(channels)))

        render_post_card(rank, channel_str, date_str, post_text, format_number(total_imp), format_number(total_eng))

        with st.expander(f"Expand #{rank} — {n_channels} channel{'s' if n_channels > 1 else ''} detail", expanded=False):
            post_rows = pp_clean.loc[indices]

            if n_channels > 1:
                st.markdown("**Combined Totals**")
                tc1, tc2, tc3, tc4 = st.columns(4)
                tc1.metric("Total Impressions", format_number(total_imp))
                tc2.metric("Total Engagements", format_number(total_eng))
                tc3.metric("Total Comments", format_number(int(post_rows["Comments"].sum())))
                tc4.metric("Total Shares", format_number(int(post_rows["Shares"].sum())))
                st.markdown("---")

            tabs = st.tabs([r["Network"] for _, r in post_rows.iterrows()])
            for tab, (_, row) in zip(tabs, post_rows.iterrows()):
                with tab:
                    m1, m2, m3, m4, m5, m6 = st.columns(6)
                    m1.metric("Impressions", format_number(int(row["Impressions"])))
                    m2.metric("Engagements", format_number(int(row["Engagements"])))
                    m3.metric("Reactions", format_number(int(row.get("Reactions", 0))))
                    m4.metric("Comments", format_number(int(row.get("Comments", 0))))
                    m5.metric("Shares", format_number(int(row.get("Shares", 0))))
                    m6.metric("Video Views", format_number(int(row.get("Video Views", 0))))

                    extra = st.columns(4)
                    extra[0].metric("Reach", format_number(int(row.get("Reach", 0))) if int(row.get("Reach", 0)) > 0 else "N/A")
                    extra[1].metric("Saves", format_number(int(row.get("Saves", 0))))
                    extra[2].metric("Link Clicks", format_number(int(row.get("Post Link Clicks", 0))))
                    er = row.get("Engagement Rate (per Impression)", 0)
                    extra[3].metric("Eng. Rate", f"{float(er):.2f}%" if er else "N/A")

                    link = str(row.get("Link", "")).strip()
                    if link and link not in ("", "nan"):
                        st.markdown(f"[View Post on {row['Network']} ↗]({link})")

            post_date = grp["_date_key"].date()
            messages = get_messages_around_beat(aff_raw, inbox_raw, post_date, days_window=0)
            if messages is not None and len(messages) > 0:
                messages = messages.sort_values("Engagements", ascending=False)
                total_msgs = len(messages)
                st.markdown(f"**Community messages — {post_date.strftime('%b %d')}** ({total_msgs:,} total)")
                for _, msg in messages.head(8).iterrows():
                    msg_link = str(msg.get("Link", "")).strip()
                    render_message_card(
                        network=msg.get("Network", ""),
                        source=msg.get("Source", ""),
                        text=str(msg["Text"])[:300],
                        sentiment=msg["Sentiment"],
                        engagements=int(msg.get("Engagements", 0)),
                        link=msg_link if msg_link not in ("", "nan") else "",
                        likes=int(msg.get("Likes", 0)),
                        shares=int(msg.get("Shares", 0)),
                        comments=int(msg.get("Comments", 0)),
                        views=int(msg.get("Views", 0)),
                    )
                if total_msgs > 8:
                    st.caption(f"... and {total_msgs - 8:,} more messages")

    # Pagination controls
    if total_pages > 1:
        st.markdown("")
        page_cols = st.columns([1, 1, 3, 1, 1])
        with page_cols[0]:
            if st.button("« First", disabled=current_page == 1, key="posts_first", use_container_width=True):
                st.session_state["posts_page"] = 1
                st.rerun()
        with page_cols[1]:
            if st.button("‹ Prev", disabled=current_page == 1, key="posts_prev", use_container_width=True):
                st.session_state["posts_page"] = current_page - 1
                st.rerun()
        with page_cols[2]:
            st.markdown(
                f'<div style="text-align:center; padding:6px 0; font-size:0.9rem;">'
                f'Page <strong>{current_page}</strong> of <strong>{total_pages}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with page_cols[3]:
            if st.button("Next ›", disabled=current_page == total_pages, key="posts_next", use_container_width=True):
                st.session_state["posts_page"] = current_page + 1
                st.rerun()
        with page_cols[4]:
            if st.button("Last »", disabled=current_page == total_pages, key="posts_last", use_container_width=True):
                st.session_state["posts_page"] = total_pages
                st.rerun()

else:
    render_empty_state(
        "",
        "Welcome to Community Insights",
        "Select a title from the sidebar, then upload your social data exports "
        "or load sample data to get started.",
    )

    render_steps([
        ("Select Title", "Choose your game title from the sidebar dropdown"),
        ("Upload Data", "Import Sprout Social, Affogata, and Looker CSVs"),
        ("Explore Insights", "KPIs, sentiment, topics, and AI analysis unlock automatically"),
    ])

    st.markdown("")
    render_section_header("Pages Available After Upload")
    render_feature_grid([
        ("", "Dashboard", "KPIs, sentiment, community topics, top posts"),
        ("", "Content Performance", "Post rankings, content type analysis"),
        ("", "Community Insights", "Sentiment, AI themes, conversation drivers"),
        ("", "Platform Breakdown", "Platform comparison, share of voice"),
        ("", "Compare Periods", "Side-by-side date range comparison"),
        ("", "Ask the Data", "Natural-language questions via Gemini"),
        ("", "Full Report", "AI-generated executive summary and narrative"),
        ("", "Multi-Title", "Compare NHL, UFC, and F1 side-by-side"),
    ])
