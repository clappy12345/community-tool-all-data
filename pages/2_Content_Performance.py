import streamlit as st
import pandas as pd

st.set_page_config(page_title="Content Performance", page_icon="📝", layout="wide")

from utils.sidebar import render_sidebar, require_data
from utils.processors import (
    apply_filters,
    get_content_type_performance,
    get_network_content_performance,
    format_number,
)
from utils.charts import content_type_bar, platform_bar, CHART_CONFIG

filters = render_sidebar()
require_data()

st.title("📝 Content Performance")
st.markdown("*How different content types and themes performed*")
st.divider()

pp = apply_filters(st.session_state["post_performance"], filters)

# --- Content Type Performance ---
st.markdown("### Performance by Content Type")
ct_perf = get_content_type_performance(pp)

col1, col2 = st.columns(2)
with col1:
    fig = content_type_bar(ct_perf, "Total Engagements by Content Type")
    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

with col2:
    st.dataframe(
        ct_perf[
            ["Content Type", "Posts", "Impressions", "Engagements", "Avg Engagements", "Engagement Rate"]
        ].style.format(
            {
                "Impressions": "{:,.0f}",
                "Engagements": "{:,.0f}",
                "Avg Engagements": "{:,.0f}",
                "Engagement Rate": "{:.2f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# --- Network Performance ---
st.markdown("### Performance by Platform")
net_perf = get_network_content_performance(pp)

fig = platform_bar(net_perf, "Engagements", "Total Engagements by Platform")
st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)

st.dataframe(
    net_perf.style.format(
        {
            "Impressions": "{:,.0f}",
            "Engagements": "{:,.0f}",
            "Reactions": "{:,.0f}",
            "Comments": "{:,.0f}",
            "Shares": "{:,.0f}",
            "Video_Views": "{:,.0f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# --- Tag/Theme Analysis ---
st.markdown("### Performance by Content Theme")

if "Tags" in pp.columns:
    tagged = pp[pp["Tags"].notna() & (pp["Tags"].str.strip() != "")].copy()
    if len(tagged) > 0:
        tag_perf = (
            tagged.groupby("Tags")
            .agg(
                Posts=("Engagements", "count"),
                Impressions=("Impressions", "sum"),
                Engagements=("Engagements", "sum"),
                Reactions=("Reactions", "sum"),
                Comments=("Comments", "sum"),
                Shares=("Shares", "sum"),
            )
            .reset_index()
            .sort_values("Engagements", ascending=False)
        )
        tag_perf["Avg Engagements"] = (tag_perf["Engagements"] / tag_perf["Posts"]).round(0)

        st.dataframe(
            tag_perf.style.format(
                {
                    "Impressions": "{:,.0f}",
                    "Engagements": "{:,.0f}",
                    "Avg Engagements": "{:,.0f}",
                    "Reactions": "{:,.0f}",
                    "Comments": "{:,.0f}",
                    "Shares": "{:,.0f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No tagged posts found in filtered data.")
else:
    st.caption("No Tags column in post data.")

st.divider()

# --- Best Post Per Platform ---
st.markdown("### Best Post Per Platform")

exclude_types = ["Story", "@Reply", "'@Reply"]
filtered = pp[~pp["Post Type"].isin(exclude_types)]

for network in sorted(filtered["Network"].unique()):
    net_posts = filtered[filtered["Network"] == network]
    if len(net_posts) > 0:
        best = net_posts.nlargest(1, "Engagements").iloc[0]
        with st.expander(f"**{network}** — {format_number(best['Engagements'])} engagements"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Impressions", format_number(best["Impressions"]))
            c2.metric("Engagements", format_number(best["Engagements"]))
            c3.metric("Comments", format_number(best["Comments"]))
            c4.metric("Shares", format_number(best["Shares"]))

            post_text = str(best.get("Post", ""))[:300]
            st.markdown(f"*{post_text}*")
            if best.get("Link"):
                st.markdown(f"[View Post]({best['Link']})")

st.divider()

# --- Full Post Table ---
st.markdown("### All Posts")
display_cols = [
    "Date",
    "Network",
    "Content Type",
    "Post",
    "Impressions",
    "Engagements",
    "Reactions",
    "Comments",
    "Shares",
    "Video Views",
]
available = [c for c in display_cols if c in pp.columns]
display_df = pp[available].copy()
display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
if "Post" in display_df.columns:
    display_df["Post"] = display_df["Post"].str[:100]

st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

csv = pp.to_csv(index=False)
st.download_button(
    "Download Post Data (CSV)", csv, "content_performance.csv", "text/csv", use_container_width=True
)
