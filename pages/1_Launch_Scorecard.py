import streamlit as st

st.set_page_config(page_title="Launch Scorecard", page_icon="📊", layout="wide")

from utils.sidebar import render_sidebar, require_data
from utils.processors import (
    apply_filters,
    get_kpis,
    get_daily_metrics,
    get_top_posts,
    get_sentiment_distribution,
    format_number,
)
from utils.charts import (
    daily_timeline,
    sentiment_donut,
    CHART_CONFIG,
)

filters = render_sidebar()
require_data()

st.title("📊 Launch Scorecard")
st.markdown("*High-level performance overview for the reporting period*")
st.divider()

pp = apply_filters(st.session_state["post_performance"], filters)
prof_raw = st.session_state.get("profile_performance")
aff_raw = st.session_state.get("affogata")
inbox_raw = st.session_state.get("inbox")

prof = apply_filters(prof_raw, filters) if prof_raw is not None else None
aff = (
    apply_filters(aff_raw, filters, date_col="Created At", network_col="Network Name")
    if aff_raw is not None
    else None
)

# --- KPIs ---
if prof is not None:
    kpis = get_kpis(pp, prof)
else:
    kpis = {
        "total_impressions": pp["Impressions"].sum(),
        "total_engagements": pp["Engagements"].sum(),
        "avg_engagement_rate": 0,
        "audience_growth": 0,
        "total_posts": len(pp),
        "total_comments": pp["Comments"].sum(),
        "total_shares": pp["Shares"].sum(),
        "total_video_views": pp["Video Views"].sum(),
    }

c1, c2, c3, c4, c5 = st.columns(5)
metrics = [
    ("Impressions", kpis["total_impressions"]),
    ("Engagements", kpis["total_engagements"]),
    ("Eng. Rate", f"{kpis['avg_engagement_rate']:.2f}%"),
    ("Audience Growth", f"+{format_number(kpis.get('audience_growth', 0))}"),
    ("Posts", kpis.get("total_posts", len(pp))),
]
for col, (label, value) in zip([c1, c2, c3, c4, c5], metrics):
    with col:
        display = format_number(value) if isinstance(value, (int, float)) else value
        st.metric(label, display)

st.divider()

# --- Timeline + Sentiment ---
col_left, col_right = st.columns([2, 1])

with col_left:
    if prof is not None:
        daily = get_daily_metrics(prof)
        fig = daily_timeline(daily, "Engagements", "Daily Engagements")
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

        fig2 = daily_timeline(daily, "Impressions", "Daily Impressions", color="#90E0EF")
        st.plotly_chart(fig2, use_container_width=True, config=CHART_CONFIG)
    else:
        st.info("Upload Profile Performance data to see daily trends.")

with col_right:
    if aff is not None:
        sentiment = get_sentiment_distribution(aff, inbox_raw)
        fig = sentiment_donut(sentiment)
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

        total = sentiment.sum()
        if total > 0:
            pos_pct = sentiment.get("positive", 0) / total * 100
            neg_pct = sentiment.get("negative", 0) / total * 100
            st.markdown(
                f"**{pos_pct:.1f}%** positive · **{neg_pct:.1f}%** negative · "
                f"**{format_number(total)}** total conversations"
            )
    else:
        st.info("Upload Affogata data to see sentiment.")

st.divider()

# --- Top Posts ---
st.markdown("### Top Performing Posts")

sort_option = st.selectbox(
    "Sort by", ["Engagements", "Impressions", "Comments", "Shares", "Reactions"], index=0
)
top = get_top_posts(pp, n=10, sort_by=sort_option)

for _, row in top.iterrows():
    with st.container():
        cols = st.columns([1, 3, 1, 1, 1, 1])
        with cols[0]:
            st.caption(row["Network"])
            st.caption(row["Date"].strftime("%b %d"))
        with cols[1]:
            post_text = str(row.get("Post", ""))[:150].replace("\n", " ")
            st.markdown(f"**{post_text}**")
            if row.get("Link"):
                st.caption(f"[View Post]({row['Link']})")
        with cols[2]:
            st.metric("Impressions", format_number(row["Impressions"]))
        with cols[3]:
            st.metric("Engagements", format_number(row["Engagements"]))
        with cols[4]:
            st.metric("Comments", format_number(row["Comments"]))
        with cols[5]:
            st.metric("Shares", format_number(row["Shares"]))
        st.divider()

# --- Export ---
st.markdown("### Export")
csv = pp.to_csv(index=False)
st.download_button(
    "Download Filtered Post Data (CSV)",
    csv,
    "filtered_posts.csv",
    "text/csv",
    use_container_width=True,
)
