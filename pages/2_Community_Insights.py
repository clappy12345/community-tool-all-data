import streamlit as st
import pandas as pd

st.set_page_config(page_title="Community Insights", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.processors import (
    apply_filters,
    get_messages_around_beat,
    combine_community_messages,
    format_number,
    get_top_conversation_topics,
    get_topic_deltas,
)
from utils.charts import (
    looker_sentiment_timeline,
    topic_percentage_bar,
    theme_bar,
    theme_sentiment_bar,
    CHART_CONFIG,
    SENTIMENT_COLORS,
)
from utils.ai_analysis import (
    discover_themes,
    classify_messages,
    get_theme_summary,
    generate_conversation_drivers,
    discover_topic_buckets,
    load_saved_topic_buckets,
)
from utils.theme import (
    render_kpi_card,
    render_message_card,
    render_section_header,
    render_trend_line,
    render_nav_header,
)

filters = render_sidebar()
apply_theme()
require_data()

from utils.titles import get_title_config

_cfg = get_title_config()
render_nav_header(
    "Community Insights",
    f"What {_cfg['community_noun']} are saying — AI-powered theme discovery and community voice",
)
st.markdown("")

pp = apply_filters(st.session_state["post_performance"], filters)
aff_raw = st.session_state.get("affogata")
inbox_raw = st.session_state.get("inbox")
looker_raw = st.session_state.get("looker_sentiment")

aff = (
    apply_filters(aff_raw, filters, date_col="Created At", network_col="Network Name")
    if aff_raw is not None
    else None
)

has_community_data = aff is not None or inbox_raw is not None or looker_raw is not None

if not has_community_data:
    st.warning("Upload Affogata, Inbox, or Looker Sentiment data to see community insights.")
    st.stop()

# ── Tabbed layout ──────────────────────────────────────────────
tab_sentiment, tab_topics, tab_ai, tab_messages = st.tabs(
    ["Sentiment", "Topics", "AI Analysis", "Messages"]
)

# ═══════════════════════════════════════════════════════════════
# TAB 1: Sentiment
# ═══════════════════════════════════════════════════════════════
with tab_sentiment:
    if looker_raw is not None:
        render_section_header("Daily Sentiment Score", "Hover to see top post by impressions. Click a point to see community messages that day.")

        looker_df = looker_raw.copy()
        if "date_range" in filters and filters["date_range"]:
            dr = filters["date_range"]
            if isinstance(dr, (list, tuple)) and len(dr) == 2:
                looker_df = looker_df[
                    (looker_df["Date"].dt.date >= dr[0])
                    & (looker_df["Date"].dt.date <= dr[1])
                ]

        if len(looker_df) > 0:
            avg_score = looker_df["Impact Score"].mean()
            max_row = looker_df.loc[looker_df["Impact Score"].idxmax()]
            min_row = looker_df.loc[looker_df["Impact Score"].idxmin()]

            k1, k2, k3 = st.columns(3)
            with k1:
                render_kpi_card("Avg Impact Score", f"{avg_score:.1f}")
            with k2:
                render_kpi_card("Highest", f"{max_row['Impact Score']:.1f}")
            with k3:
                render_kpi_card("Lowest", f"{min_row['Impact Score']:.1f}")

            exclude_types = ["Story", "@Reply", "'@Reply"]
            pp_clean = pp[~pp["Post Type"].isin(exclude_types)].copy()
            top_per_day = []
            for date in looker_df["Date"]:
                day_posts = pp_clean[pp_clean["Date"].dt.normalize() == date.normalize()]
                if len(day_posts) > 0:
                    best = day_posts.nlargest(1, "Impressions").iloc[0]
                    top_per_day.append({
                        "Date": date,
                        "Top Network": best.get("Network", ""),
                        "Top Post": str(best.get("Post", ""))[:100].replace("\n", " "),
                    })
                else:
                    top_per_day.append({"Date": date, "Top Network": "", "Top Post": "No posts"})
            top_df = pd.DataFrame(top_per_day)
            looker_chart = looker_df.merge(top_df, on="Date", how="left")
            looker_chart["Top Post"] = looker_chart["Top Post"].fillna("No posts")
            looker_chart["Top Network"] = looker_chart["Top Network"].fillna("")

            fig = looker_sentiment_timeline(looker_chart)
            event = st.plotly_chart(
                fig,
                use_container_width=True,
                on_select="rerun",
                selection_mode=("points", "box", "lasso"),
                key="sentiment_timeline",
            )

            selected_date = None
            if event and event.selection and event.selection.points:
                selected_date = pd.Timestamp(event.selection.points[0]["x"]).date()

            if selected_date is not None:
                score_row = looker_df[looker_df["Date"].dt.date == selected_date]
                score_str = f" · Impact Score: {score_row['Impact Score'].values[0]:.1f}" if len(score_row) > 0 else ""

                messages = get_messages_around_beat(aff_raw, inbox_raw, selected_date, days_window=0)

                if len(messages) > 0:
                    messages = messages.sort_values("Engagements", ascending=False)
                    total = len(messages)
                    sent_counts = messages["Sentiment"].value_counts()
                    pos_pct = sent_counts.get("positive", 0) / total * 100
                    neg_pct = sent_counts.get("negative", 0) / total * 100

                    label = (
                        f"{selected_date.strftime('%A, %b %d, %Y')}{score_str} — "
                        f"{total} community messages"
                    )
                    with st.expander(label, expanded=True):
                        mcol1, mcol2, mcol3 = st.columns(3)
                        with mcol1:
                            render_kpi_card("Messages", f"{total:,}")
                        with mcol2:
                            render_kpi_card("Positive", f"{pos_pct:.0f}%")
                        with mcol3:
                            render_kpi_card("Negative", f"{neg_pct:.0f}%")

                        st.markdown(f"**Top community conversations** (sorted by engagement)")
                        for _, msg in messages.head(15).iterrows():
                            ts = msg["Timestamp"].strftime("%I:%M %p") if pd.notna(msg["Timestamp"]) else ""
                            link = str(msg.get("Link", "")).strip()
                            render_message_card(
                                network=msg.get("Network", "Unknown"),
                                source=msg.get("Source", ""),
                                text=str(msg["Text"])[:300],
                                sentiment=msg["Sentiment"],
                                engagements=int(msg.get("Engagements", 0)),
                                link=link if link not in ("", "nan") else "",
                                timestamp=ts,
                                likes=int(msg.get("Likes", 0)),
                                shares=int(msg.get("Shares", 0)),
                                comments=int(msg.get("Comments", 0)),
                                views=int(msg.get("Views", 0)),
                            )

                        if total > 15:
                            st.caption(f"... and {total - 15:,} more messages")
                else:
                    st.info(f"No community messages found on {selected_date.strftime('%b %d, %Y')}.")
    else:
        st.info("Upload Looker Sentiment data to view sentiment trends.")

    if aff is not None:
        st.markdown("")
        render_section_header("Conversation Volume by Platform")
        vol = aff.groupby("Network Name").size().reset_index(name="Messages").sort_values("Messages", ascending=False)
        cols = st.columns(min(len(vol), 6))
        for i, (_, row) in enumerate(vol.iterrows()):
            if i < len(cols):
                with cols[i]:
                    render_kpi_card(row["Network Name"], format_number(row["Messages"]))

        eng_cols = ["Likes", "Shares", "Comments", "Views", "Reach"]
        available_eng = [c for c in eng_cols if c in aff.columns and aff[c].sum() > 0]
        if available_eng:
            st.markdown("")
            render_section_header("Engagement Breakdown", "Aggregate engagement metrics from community listening data")
            ec = st.columns(len(available_eng))
            for i, col_name in enumerate(available_eng):
                with ec[i]:
                    render_kpi_card(f"Total {col_name}", format_number(int(aff[col_name].sum())))

# ═══════════════════════════════════════════════════════════════
# TAB 2: Topics
# ═══════════════════════════════════════════════════════════════
with tab_topics:
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
            render_section_header("What the Community Is Talking About")
        with _h_right:
            if has_msgs:
                refresh_topics = st.button(
                    "Refresh with AI" if not using_ai else "Re-discover",
                    type="secondary",
                    use_container_width=True,
                    key="btn_refresh_topics",
                )
            else:
                refresh_topics = False

        topics_df = get_top_conversation_topics(aff, inbox_raw, buckets=buckets_to_use)

        if topics_df is not None and len(topics_df) > 0:
            source_label = "AI-discovered topics" if using_ai else f"Default {_cfg['name']} topic buckets"
            st.caption(f"% of messages matching each topic — {source_label}.")
            fig_topics = topic_percentage_bar(topics_df)
            st.plotly_chart(fig_topics, use_container_width=True, config=CHART_CONFIG)

            deltas_df = get_topic_deltas(aff, inbox_raw, buckets=buckets_to_use)
            if deltas_df is not None and len(deltas_df) > 0:
                trending_up = deltas_df[deltas_df["Delta"] > 0.5].head(3)
                trending_down = deltas_df[deltas_df["Delta"] < -0.5].head(3)
                trend_parts = []
                for _, tr in trending_up.iterrows():
                    trend_parts.append(f"<span style='color:var(--positive);'>▲ {tr['Topic']} +{tr['Delta']}pp</span>")
                for _, tr in trending_down.iterrows():
                    trend_parts.append(f"<span style='color:var(--negative);'>▼ {tr['Topic']} {tr['Delta']}pp</span>")
                render_trend_line(trend_parts)

            other_row = topics_df[topics_df["Topic"] == "Other / Uncategorized"]
            if not using_ai and len(other_row) > 0 and other_row.iloc[0]["Pct"] > 25:
                st.info(
                    f"{other_row.iloc[0]['Pct']:.0f}% of messages didn't match any predefined topic. "
                    "Click **Refresh with AI** to discover what else the community is talking about."
                )
        else:
            st.info("Not enough community messages to analyze topics.")

        if refresh_topics:
            with st.spinner("Discovering topics from community messages..."):
                new_buckets = discover_topic_buckets(combined_for_topics)
                if new_buckets:
                    st.session_state["ai_topic_buckets"] = new_buckets
                    st.rerun()
                else:
                    st.error("Could not discover topics. Check your Google API key.")
    else:
        st.info("Upload Affogata or Inbox data to see topic analysis.")

# ═══════════════════════════════════════════════════════════════
# TAB 3: AI Analysis
# ═══════════════════════════════════════════════════════════════
with tab_ai:
    if aff is not None or inbox_raw is not None:
        # Conversation Drivers
        render_section_header("Conversation Drivers — AI Deep Dive",
                              "AI-powered analysis with estimated volume, key takeaways, and expanded summaries.")

        drivers_ready = "conversation_drivers" in st.session_state and st.session_state["conversation_drivers"] is not None

        drv_btn_col, drv_status_col = st.columns([1, 3])
        with drv_btn_col:
            run_drivers = st.button(
                "Generate Drivers" if not drivers_ready else "Re-generate Drivers",
                type="primary" if not drivers_ready else "secondary",
                use_container_width=True,
                key="btn_drivers",
            )
        with drv_status_col:
            if drivers_ready:
                st.success("Conversation drivers ready")
            else:
                st.caption("Requires Google API key — takes 20-40 seconds")

        if run_drivers:
            combined_for_drivers = combine_community_messages(aff_raw, inbox_raw)
            if len(combined_for_drivers) > 0:
                with st.spinner("Analyzing conversation drivers with AI..."):
                    drivers_md = generate_conversation_drivers(combined_for_drivers)
                    if drivers_md:
                        st.session_state["conversation_drivers"] = drivers_md
                        st.rerun()
            else:
                st.warning("No community messages available to analyze.")

        if drivers_ready:
            st.markdown(st.session_state["conversation_drivers"], unsafe_allow_html=False)
            st.download_button(
                "Download Conversation Drivers (.md)",
                st.session_state["conversation_drivers"],
                file_name="conversation_drivers.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_drivers",
            )

        st.markdown("")

        # Theme Discovery
        render_section_header("AI Theme Discovery",
                              "Automatically discover what topics the community is discussing.")

        combined_messages = combine_community_messages(aff, inbox_raw)
        if len(combined_messages) == 0:
            combined_messages = None

        themes_ready = "themes" in st.session_state and st.session_state["themes"] is not None

        col_btn, col_status = st.columns([1, 3])
        with col_btn:
            run_ai = st.button(
                "Discover Themes" if not themes_ready else "Re-run Analysis",
                type="primary" if not themes_ready else "secondary",
                use_container_width=True,
            )
        with col_status:
            if themes_ready:
                n_themes = len(st.session_state["themes"])
                st.success(f"Analysis complete — {n_themes} themes discovered")
            else:
                st.caption("Requires Google API key in .env file")

        if run_ai and combined_messages is not None:
            with st.spinner("Analyzing community conversations with AI..."):
                themes = discover_themes(combined_messages, n_sample=600)
                if themes:
                    st.session_state["themes"] = themes
                    classified = classify_messages(combined_messages, themes)
                    st.session_state["classified_messages"] = classified
                    st.rerun()

        if themes_ready and "classified_messages" in st.session_state:
            classified = st.session_state["classified_messages"]
            theme_summary = get_theme_summary(classified)

            if theme_summary is not None:
                col1, col2 = st.columns(2)
                with col1:
                    fig = theme_bar(theme_summary, "Most Discussed Topics")
                    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
                with col2:
                    fig = theme_sentiment_bar(theme_summary, "Sentiment by Topic")
                    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

                render_section_header("Theme Details")
                themes_list = st.session_state["themes"]
                for theme in themes_list:
                    name = theme["name"]
                    count = theme_summary[theme_summary["Theme"] == name]["Count"].values
                    count_str = f" ({format_number(count[0])} messages)" if len(count) > 0 else ""
                    lean = theme.get("sentiment_lean", "mixed")
                    lean_label = {"positive": "[+]", "negative": "[-]", "mixed": "[~]"}.get(lean, "")

                    with st.expander(f"{lean_label} **{name}**{count_str}"):
                        st.markdown(f"*{theme['description']}*")
                        st.caption(f"Sentiment lean: {lean} · Keywords: {', '.join(theme['keywords'][:8])}")

                        theme_msgs = classified[classified["Theme"] == name]
                        if len(theme_msgs) > 0:
                            sample = theme_msgs.sample(min(5, len(theme_msgs)), random_state=42)
                            for _, msg in sample.iterrows():
                                render_message_card(
                                    network="",
                                    source="",
                                    text=str(msg["Text"])[:200],
                                    sentiment=msg["Sentiment"],
                                )
    else:
        st.info("Upload Affogata or Inbox data to use AI analysis.")

# ═══════════════════════════════════════════════════════════════
# TAB 4: Messages
# ═══════════════════════════════════════════════════════════════
with tab_messages:
    render_section_header("Community Messages", "Browse and filter all community messages.")

    all_messages = combine_community_messages(aff, inbox_raw)

    if len(all_messages) > 0 and "date_range" in filters and filters["date_range"]:
        dr = filters["date_range"]
        if isinstance(dr, (list, tuple)) and len(dr) == 2:
            all_messages = all_messages[
                all_messages["Timestamp"].dt.date.between(dr[0], dr[1])
            ]

    if len(all_messages) == 0:
        all_messages = None

    if all_messages is not None and len(all_messages) > 0:
        search_term = st.text_input("Search messages", placeholder="Type a keyword...", key="msg_search")

        filter_cols = st.columns(4)
        with filter_cols[0]:
            sent_options = sorted(all_messages["Sentiment"].dropna().unique().tolist())
            sent_filter = st.multiselect("Sentiment", sent_options, default=sent_options, key="cm_sentiment")
        with filter_cols[1]:
            source_options = sorted(all_messages["Source"].dropna().unique().tolist())
            source_filter = st.multiselect("Source", source_options, default=source_options, key="cm_source")
        with filter_cols[2]:
            net_options = sorted(all_messages["Network"].dropna().unique().tolist())
            network_filter = st.multiselect("Network", net_options, default=net_options, key="cm_network")
        with filter_cols[3]:
            sort_by = st.selectbox("Sort by", ["Most Engaged", "Most Recent", "Oldest"], key="cm_sort")

        filtered = all_messages[
            all_messages["Sentiment"].isin(sent_filter)
            & all_messages["Source"].isin(source_filter)
            & all_messages["Network"].isin(network_filter)
        ]

        if search_term:
            filtered = filtered[filtered["Text"].str.contains(search_term, case=False, na=False)]

        if sort_by == "Most Recent":
            filtered = filtered.sort_values("Timestamp", ascending=False)
        elif sort_by == "Most Engaged":
            filtered = filtered.sort_values("Engagements", ascending=False)
        else:
            filtered = filtered.sort_values("Timestamp", ascending=True)

        page_size = 25
        total_msgs = len(filtered)
        st.caption(f"Showing {min(page_size, total_msgs)} of {total_msgs:,} messages")

        for _, msg in filtered.head(page_size).iterrows():
            ts = msg["Timestamp"].strftime("%b %d, %I:%M %p") if pd.notna(msg["Timestamp"]) else ""
            link = str(msg.get("Link", "")).strip()
            render_message_card(
                network=msg.get("Network", "Unknown"),
                source=msg.get("Source", ""),
                text=str(msg["Text"])[:300],
                sentiment=msg["Sentiment"],
                engagements=int(msg.get("Engagements", 0)),
                link=link if link not in ("", "nan") else "",
                timestamp=ts,
                likes=int(msg.get("Likes", 0)),
                shares=int(msg.get("Shares", 0)),
                comments=int(msg.get("Comments", 0)),
                views=int(msg.get("Views", 0)),
            )

        if total_msgs > page_size:
            st.caption(f"... and {total_msgs - page_size:,} more messages")

        csv = filtered.to_csv(index=False)
        st.download_button(
            "Download Messages (CSV)",
            csv,
            "community_messages.csv",
            "text/csv",
            use_container_width=True,
        )
    else:
        st.info("No community messages available. Upload Affogata or Inbox data to see messages.")
