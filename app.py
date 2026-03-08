import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Community Insights",
    page_icon="📊",
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
from utils.theme import (
    inject_global_css,
    render_kpi_card,
    render_post_card,
    render_message_card,
    render_section_header,
)

filters = render_sidebar()
apply_theme()
cfg = get_title_config()

st.title(f"{cfg['icon']} {cfg['full_name']} Dashboard")
st.markdown("*Social performance + community snapshot — all in one view*")
st.divider()

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
    render_section_header(f"Reporting Period: {date_min} — {date_max}")

    def _delta(key):
        return deltas.get(key)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("Total Impressions", format_number(kpis["total_impressions"]), _delta("total_impressions"))
    with c2:
        render_kpi_card("Total Engagements", format_number(kpis["total_engagements"]), _delta("total_engagements"))
    with c3:
        render_kpi_card("Engagement Rate", f"{kpis['avg_engagement_rate']:.2f}%")
    with c4:
        render_kpi_card("Video Views", format_number(kpis.get("total_video_views", pp["Video Views"].sum())), _delta("total_video_views"))
    with c5:
        growth = kpis.get("audience_growth", 0)
        render_kpi_card("Audience Growth", f"{'+' if growth > 0 else ''}{format_number(growth)}")

    st.markdown("")
    c6, c7, c8, c9, c10 = st.columns(5)
    with c6:
        render_kpi_card("Total Posts", f"{int(kpis['total_posts']):,}", _delta("total_posts"))
    with c7:
        render_kpi_card("Total Reach", format_number(kpis.get("total_reach", 0)), _delta("total_reach"))
    with c8:
        render_kpi_card("Comments", format_number(kpis.get("total_comments", 0)), _delta("total_comments"))
    with c9:
        render_kpi_card("Shares", format_number(kpis.get("total_shares", 0)), _delta("total_shares"))
    with c10:
        aud = kpis.get("total_audience", 0)
        render_kpi_card("Total Audience", format_number(aud) if aud > 0 else "N/A")

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

    st.divider()

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

    st.divider()

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

        st.divider()

    # ── Top 5 Posts by Impressions (grouped cross-platform) ───
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
        .head(5)
    )

    for rank, (_, grp) in enumerate(grouped.iterrows(), 1):
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

            # Community messages for that day
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
                    )
                if total_msgs > 8:
                    st.caption(f"... and {total_msgs - 8:,} more messages")

else:
    st.markdown("### Getting Started")
    st.markdown(
        f"""
Select a title from the dropdown at the top of the sidebar, then upload your social data exports
or click **Load Sample Data** to explore with demo data. This tool accepts:

1. **Post Performance** (Sprout Social CSV) — individual post metrics
2. **Profile Performance** (Sprout Social CSV) — daily profile-level metrics
3. **Affogata Export** (CSV) — community conversations
4. **Inbox Export** (Sprout Social CSV or ZIP) — {cfg['community_noun']} messages and comments
5. **Looker Sentiment Score** (CSV) — daily sentiment impact scores

All files should cover the same date range for the most accurate analysis.
"""
    )

    st.markdown("---")
    st.markdown(
        """
#### Pages Available After Upload
| Page | What It Shows |
|------|--------------|
| **Dashboard** (this page) | KPIs, sentiment, community topics, impressions, top posts |
| **Content Performance** | Post rankings, content type analysis |
| **Community Insights** | Sentiment timeline, AI conversation drivers, theme discovery, community messages |
| **Platform Breakdown** | Platform comparison, audience growth, share of voice |
| **Compare Periods** | Side-by-side comparison with a second date range |
| **Ask the Data** | Chatbot (Gemini) — ask natural-language questions about your data |
| **Full Report** | AI-generated report — exec summary, performance narrative, coverage themes, conversation drivers |
"""
    )
