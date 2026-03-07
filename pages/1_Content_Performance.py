import streamlit as st
import pandas as pd

st.set_page_config(page_title="Content Performance", page_icon="📝", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.processors import (
    apply_filters,
    get_daily_post_engagement,
    get_posts_for_date,
    get_network_content_performance,
    format_number,
)
from utils.charts import daily_engagement_timeline_with_hover, platform_bar, CHART_CONFIG

filters = render_sidebar()
apply_theme()
require_data()

st.title("📝 Content Performance")
st.markdown("*How different content types and themes performed*")
st.divider()

pp = apply_filters(st.session_state["post_performance"], filters)

# --- Total Engagement Metrics ---
exclude_types = ["Story", "@Reply", "'@Reply"]
pp_filtered = pp[~pp["Post Type"].isin(exclude_types)]
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Impressions", format_number(pp_filtered["Impressions"].sum()))
k2.metric("Total Engagements", format_number(pp_filtered["Engagements"].sum()))
k3.metric("Video Views", format_number(pp_filtered["Video Views"].sum()))
k4.metric("Reactions", format_number(pp_filtered["Reactions"].sum()))
k5.metric("Reach", format_number(pp_filtered["Reach"].sum()))

k6, k7, k8, k9, k10 = st.columns(5)
k6.metric("Comments", format_number(pp_filtered["Comments"].sum()))
k7.metric("Shares", format_number(pp_filtered["Shares"].sum()))
k8.metric("Link Clicks", format_number(pp_filtered["Post Link Clicks"].sum()))
k9.metric("Total Posts", format_number(len(pp_filtered)))
avg_eng = pp_filtered["Engagements"].mean() if len(pp_filtered) > 0 else 0
k10.metric("Avg Eng / Post", format_number(int(avg_eng)))

st.divider()

# --- Daily Impressions Timeline ---
st.markdown("### Daily Impressions Timeline")
st.caption("Click a point to see what was posted that day.")
daily = get_daily_post_engagement(pp)
fig = daily_engagement_timeline_with_hover(daily)
event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode=("points", "box", "lasso"),
    key="daily_timeline",
)

selected_date = None
if event and event.selection and event.selection.points:
    selected_date = pd.Timestamp(event.selection.points[0]["x"]).date()

if selected_date is not None:
    day_posts = get_posts_for_date(pp, selected_date)
    label = (
        f"{selected_date.strftime('%A, %b %d, %Y')} — "
        f"{len(day_posts)} post{'s' if len(day_posts) != 1 else ''}, "
        f"{day_posts['Engagements'].sum():,.0f} total engagements"
    )
    with st.expander(label, expanded=True):
        if len(day_posts) > 0:
            for _, post in day_posts.iterrows():
                eng = format_number(post["Engagements"])
                network = post.get("Network", "")
                text = str(post.get("Post", ""))[:200].replace("\n", " ")
                link = post.get("Link", "")

                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                    with c1:
                        st.markdown(f"**{network}** — *{text}*")
                        if link:
                            st.markdown(f"[View Post]({link})")
                    with c2:
                        st.metric("Engagements", eng)
                    with c3:
                        st.metric("Comments", format_number(post.get("Comments", 0)))
                    with c4:
                        st.metric("Shares", format_number(post.get("Shares", 0)))
        else:
            st.caption("No posts on this day.")

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

# --- Top Posts (Grouped Cross-Channel) ---
st.markdown("### Top Posts (Cross-Channel)")
st.caption("Identical posts across channels are grouped. Expand for per-channel metrics.")

exclude_types = ["Story", "@Reply", "'@Reply"]
pp_clean = pp[~pp["Post Type"].isin(exclude_types)].copy()
pp_clean["_post_key"] = pp_clean["Post"].fillna("").str.strip().str[:120]
pp_clean["_date_key"] = pp_clean["Date"].dt.normalize()

sort_metric = st.selectbox("Sort by", ["Impressions", "Engagements"], index=0, key="cp_sort")

grouped = (
    pp_clean.groupby(["_date_key", "_post_key"])
    .agg(
        Combined_Impressions=("Impressions", "sum"),
        Combined_Engagements=("Engagements", "sum"),
        Channels=("Network", lambda x: list(x)),
        _indices=("Impressions", lambda x: list(x.index)),
    )
    .reset_index()
    .sort_values(f"Combined_{sort_metric}", ascending=False)
    .head(10)
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

    st.markdown(
        f"<div style='padding:14px 18px; margin:6px 0; background:#1A1D23; border-radius:10px; "
        f"border-left: 4px solid #00B4D8;'>"
        f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>"
        f"<span style='font-size:0.8rem; color:#90A4AE; font-weight:600;'>#{rank} · {channel_str} · {date_str}</span>"
        f"<span style='font-size:0.8rem; color:#00B4D8; font-weight:600;'>"
        f"{format_number(total_imp)} imp · {format_number(total_eng)} eng</span>"
        f"</div>"
        f"<div style='font-size:0.92rem;'>{post_text}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

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
