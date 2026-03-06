import streamlit as st
import pandas as pd

st.set_page_config(page_title="Community Insights", page_icon="💬", layout="wide")

from utils.sidebar import render_sidebar, require_data
from utils.processors import (
    apply_filters,
    get_sentiment_distribution,
    get_sentiment_over_time,
    identify_key_beats,
    get_messages_around_beat,
    format_number,
)
from utils.charts import (
    sentiment_donut,
    sentiment_timeline,
    theme_bar,
    theme_sentiment_bar,
    CHART_CONFIG,
    SENTIMENT_COLORS,
)
from utils.ai_analysis import discover_themes, classify_messages, get_theme_summary

filters = render_sidebar()
require_data()

st.title("💬 Community Insights")
st.markdown("*What players are saying — AI-powered theme discovery and player voice*")
st.divider()

pp = apply_filters(st.session_state["post_performance"], filters)
aff_raw = st.session_state.get("affogata")
inbox_raw = st.session_state.get("inbox")

aff = (
    apply_filters(aff_raw, filters, date_col="Created At", network_col="Network Name")
    if aff_raw is not None
    else None
)

has_community_data = aff is not None or inbox_raw is not None

if not has_community_data:
    st.warning("Upload Affogata or Inbox Export data to see community insights.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# SECTION 1: Sentiment Overview
# ─────────────────────────────────────────────────────────────
st.markdown("### Sentiment Overview")

col1, col2 = st.columns([1, 2])

with col1:
    sentiment = get_sentiment_distribution(aff, inbox_raw) if aff is not None else pd.Series()
    if len(sentiment) > 0:
        fig = sentiment_donut(sentiment, "Overall Sentiment")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

        total = sentiment.sum()
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        st.markdown(
            f"**{format_number(total)}** total messages analyzed  \n"
            f"🟢 {pos / total * 100:.1f}% positive · "
            f"🔴 {neg / total * 100:.1f}% negative"
        )

with col2:
    if aff is not None:
        daily_sent = get_sentiment_over_time(aff)
        fig = sentiment_timeline(daily_sent, "Sentiment Trend Over Time")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.divider()

# ─────────────────────────────────────────────────────────────
# SECTION 2: Conversation Volume by Platform
# ─────────────────────────────────────────────────────────────
if aff is not None:
    st.markdown("### Conversation Volume by Platform")
    vol = aff.groupby("Network Name").size().reset_index(name="Messages").sort_values("Messages", ascending=False)
    cols = st.columns(min(len(vol), 6))
    for i, (_, row) in enumerate(vol.iterrows()):
        if i < len(cols):
            cols[i].metric(row["Network Name"], format_number(row["Messages"]))
    st.divider()

# ─────────────────────────────────────────────────────────────
# SECTION 3: AI Theme Discovery
# ─────────────────────────────────────────────────────────────
st.markdown("### AI Theme Discovery")
st.markdown(
    "Use AI to automatically discover what topics the community is discussing. "
    "This analyzes a sample of messages and identifies recurring themes."
)

# Combine Affogata + Inbox for AI analysis
combined_messages = None
if aff is not None:
    aff_for_ai = aff[["Created At", "Network Name", "Text", "Sentiment", "Total Engagements"]].copy()
    aff_for_ai.columns = ["Timestamp", "Network", "Text", "Sentiment", "Engagements"]
    combined_messages = aff_for_ai

if inbox_raw is not None and "Message" in inbox_raw.columns:
    inbox_for_ai = inbox_raw[["Timestamp", "Network", "Message", "Sentiment"]].copy()
    inbox_for_ai["Engagements"] = 0
    inbox_for_ai.columns = ["Timestamp", "Network", "Text", "Sentiment", "Engagements"]
    if combined_messages is not None:
        combined_messages = pd.concat([combined_messages, inbox_for_ai], ignore_index=True)
    else:
        combined_messages = inbox_for_ai

if combined_messages is not None:
    combined_messages = combined_messages[
        combined_messages["Text"].notna() & (combined_messages["Text"].str.strip() != "")
    ]

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
        st.caption("Requires OpenAI API key in .env file")

if run_ai and combined_messages is not None:
    with st.spinner("Analyzing community conversations with AI..."):
        themes = discover_themes(combined_messages, n_sample=600)
        if themes:
            st.session_state["themes"] = themes
            classified = classify_messages(combined_messages, themes)
            st.session_state["classified_messages"] = classified
            st.rerun()

# Show theme results
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

        # Theme details
        st.markdown("#### Theme Details")
        themes_list = st.session_state["themes"]
        for theme in themes_list:
            name = theme["name"]
            count = theme_summary[theme_summary["Theme"] == name]["Count"].values
            count_str = f" ({format_number(count[0])} messages)" if len(count) > 0 else ""
            lean = theme.get("sentiment_lean", "mixed")
            lean_emoji = {"positive": "🟢", "negative": "🔴", "mixed": "🟡"}.get(lean, "⚪")

            with st.expander(f"{lean_emoji} **{name}**{count_str}"):
                st.markdown(f"*{theme['description']}*")
                st.caption(f"Sentiment lean: {lean} · Keywords: {', '.join(theme['keywords'][:8])}")

                theme_msgs = classified[classified["Theme"] == name]
                if len(theme_msgs) > 0:
                    sample = theme_msgs.sample(min(5, len(theme_msgs)), random_state=42)
                    for _, msg in sample.iterrows():
                        sent_color = SENTIMENT_COLORS.get(msg["Sentiment"], "#808080")
                        text = str(msg["Text"])[:200]
                        st.markdown(
                            f"<div style='padding:8px 12px; margin:4px 0; "
                            f"background:#1A1D23; border-radius:8px; "
                            f"border-left: 3px solid {sent_color};'>"
                            f"<span style='font-size:0.85rem;'>{text}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

st.divider()

# ─────────────────────────────────────────────────────────────
# SECTION 4: Player Voice — What Players Are Saying Around Key Beats
# ─────────────────────────────────────────────────────────────
st.markdown("### Player Voice — Key Beats")
st.markdown(
    "See what players were saying around your biggest content moments. "
    "Select a key beat to explore community reaction."
)

beats = identify_key_beats(pp, n=10)

if not beats:
    st.info("No key beats detected in the current date range.")
else:
    beat_labels = [b["label"] for b in beats]
    selected_label = st.selectbox("Select a key beat", beat_labels)

    selected_beat = next(b for b in beats if b["label"] == selected_label)
    beat_date = selected_beat["date"]

    st.markdown(
        f"**{selected_beat['date'].strftime('%B %d, %Y')}** · "
        f"{selected_beat['num_posts']} posts · "
        f"{format_number(selected_beat['total_engagements'])} total engagements"
    )

    window = st.slider("Days around beat to include", 0, 3, 1)

    messages = get_messages_around_beat(aff_raw, inbox_raw, beat_date, days_window=window)

    if len(messages) > 0:
        # Sentiment breakdown for this beat
        beat_sentiment = messages["Sentiment"].value_counts()
        total = beat_sentiment.sum()

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Total Messages", format_number(total))
        mcol2.metric(
            "Positive",
            f"{beat_sentiment.get('positive', 0) / total * 100:.1f}%",
        )
        mcol3.metric(
            "Negative",
            f"{beat_sentiment.get('negative', 0) / total * 100:.1f}%",
        )
        mcol4.metric(
            "Neutral",
            f"{beat_sentiment.get('neutral', 0) / total * 100:.1f}%",
        )

        # Filter controls
        st.markdown("#### Community Messages")
        filter_cols = st.columns(3)
        with filter_cols[0]:
            sent_filter = st.multiselect(
                "Sentiment",
                ["positive", "negative", "neutral"],
                default=["positive", "negative", "neutral"],
                key="beat_sentiment",
            )
        with filter_cols[1]:
            source_filter = st.multiselect(
                "Source",
                messages["Source"].unique().tolist(),
                default=messages["Source"].unique().tolist(),
                key="beat_source",
            )
        with filter_cols[2]:
            network_filter = st.multiselect(
                "Network",
                sorted(messages["Network"].dropna().unique().tolist()),
                default=sorted(messages["Network"].dropna().unique().tolist()),
                key="beat_network",
            )

        filtered_msgs = messages[
            messages["Sentiment"].isin(sent_filter)
            & messages["Source"].isin(source_filter)
            & messages["Network"].isin(network_filter)
        ]

        # Sort options
        sort_col = st.columns([1, 3])
        with sort_col[0]:
            sort_by = st.selectbox("Sort by", ["Most Recent", "Most Engaged", "Oldest"])

        if sort_by == "Most Recent":
            filtered_msgs = filtered_msgs.sort_values("Timestamp", ascending=False)
        elif sort_by == "Most Engaged":
            filtered_msgs = filtered_msgs.sort_values("Engagements", ascending=False)
        else:
            filtered_msgs = filtered_msgs.sort_values("Timestamp", ascending=True)

        # Display messages
        page_size = 25
        total_msgs = len(filtered_msgs)
        st.caption(f"Showing {min(page_size, total_msgs)} of {total_msgs:,} messages")

        for _, msg in filtered_msgs.head(page_size).iterrows():
            sent_color = SENTIMENT_COLORS.get(str(msg["Sentiment"]).lower(), "#808080")
            text = str(msg["Text"])[:300]
            network = msg.get("Network", "Unknown")
            source = msg.get("Source", "")
            ts = msg["Timestamp"].strftime("%b %d, %I:%M %p") if pd.notna(msg["Timestamp"]) else ""

            st.markdown(
                f"<div style='padding:10px 14px; margin:6px 0; "
                f"background:#1A1D23; border-radius:8px; "
                f"border-left: 3px solid {sent_color};'>"
                f"<div style='display:flex; justify-content:space-between; margin-bottom:4px;'>"
                f"<span style='font-size:0.75rem; color:#90A4AE;'>"
                f"{network} · {source}</span>"
                f"<span style='font-size:0.75rem; color:#90A4AE;'>{ts}</span>"
                f"</div>"
                f"<span style='font-size:0.9rem;'>{text}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        if total_msgs > page_size:
            st.caption(f"... and {total_msgs - page_size:,} more messages")

        # Export beat messages
        csv = filtered_msgs.to_csv(index=False)
        st.download_button(
            f"Download Messages for {selected_beat['date'].strftime('%b %d')} (CSV)",
            csv,
            f"player_voice_{beat_date}.csv",
            "text/csv",
            use_container_width=True,
        )
    else:
        st.info("No community messages found around this beat. Try increasing the day window.")

st.divider()

# ─────────────────────────────────────────────────────────────
# SECTION 5: Raw Message Explorer
# ─────────────────────────────────────────────────────────────
st.markdown("### Message Explorer")
st.markdown("Search and filter all community messages.")

search_term = st.text_input("Search messages", placeholder="Type a keyword...")

explore_df = combined_messages if combined_messages is not None else pd.DataFrame()

if search_term and len(explore_df) > 0:
    mask = explore_df["Text"].str.contains(search_term, case=False, na=False)
    results = explore_df[mask]
    st.caption(f"{len(results):,} messages matching '{search_term}'")

    if len(results) > 0:
        sent_breakdown = results["Sentiment"].value_counts()
        scol1, scol2, scol3 = st.columns(3)
        scol1.metric("Positive", f"{sent_breakdown.get('positive', 0):,}")
        scol2.metric("Negative", f"{sent_breakdown.get('negative', 0):,}")
        scol3.metric("Neutral", f"{sent_breakdown.get('neutral', 0):,}")

        for _, msg in results.head(20).iterrows():
            sent_color = SENTIMENT_COLORS.get(str(msg["Sentiment"]).lower(), "#808080")
            text = str(msg["Text"])[:300]
            st.markdown(
                f"<div style='padding:8px 12px; margin:4px 0; "
                f"background:#1A1D23; border-radius:8px; "
                f"border-left: 3px solid {sent_color};'>"
                f"<span style='font-size:0.85rem;'>{text}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
elif not search_term:
    st.caption("Enter a search term to explore messages across all sources.")
