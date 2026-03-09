import streamlit as st
import pandas as pd

st.set_page_config(page_title="Content Performance", layout="wide")

from utils.sidebar import render_sidebar, require_data, apply_theme
from utils.processors import (
    apply_filters,
    get_daily_post_engagement,
    get_posts_for_date,
    get_network_content_performance,
    get_kpis_safe,
    format_number,
)
from utils.charts import daily_engagement_timeline_with_hover, platform_bar, CHART_CONFIG
from utils.theme import render_kpi_card, render_post_card, render_section_header, render_nav_header

filters = render_sidebar()
apply_theme()
require_data()

render_nav_header("Content Performance", "How different content types and themes performed")
st.markdown("")

pp_full = st.session_state["post_performance"]
pp = apply_filters(pp_full, filters)
prof_raw = st.session_state.get("profile_performance")
prof = apply_filters(prof_raw, filters) if prof_raw is not None else None

kpis = get_kpis_safe(pp, prof)


def _compute_period_deltas(pp_current, pp_full_df):
    current_start = pp_current["Date"].min()
    current_end = pp_current["Date"].max()
    period_days = (current_end - current_start).days + 1
    prior_end = current_start - pd.Timedelta(days=1)
    prior_start = prior_end - pd.Timedelta(days=period_days - 1)
    pp_prior = pp_full_df[
        (pp_full_df["Date"] >= prior_start) & (pp_full_df["Date"] <= prior_end)
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


deltas, period_days = _compute_period_deltas(pp, pp_full)

date_min = pp["Date"].min().strftime("%b %d, %Y")
date_max = pp["Date"].max().strftime("%b %d, %Y")
render_section_header(f"Reporting Period: {date_min} — {date_max}")


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

st.markdown("")

# --- Daily Impressions Timeline ---
render_section_header("Daily Impressions Timeline", "Click a point to see what was posted that day.")
daily = get_daily_post_engagement(pp)
fig = daily_engagement_timeline_with_hover(daily, title="")
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

st.markdown("")

# --- Top Posts (Grouped Cross-Channel) ---
render_section_header("Top Posts (Cross-Channel)", "Identical posts across channels are grouped. Expand for per-channel metrics.")

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

if "cp_posts_page" not in st.session_state:
    st.session_state["cp_posts_page"] = 1
current_page = st.session_state["cp_posts_page"]
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

if total_pages > 1:
    st.markdown("")
    page_cols = st.columns([1, 1, 3, 1, 1])
    with page_cols[0]:
        if st.button("« First", disabled=current_page == 1, key="cp_posts_first", use_container_width=True):
            st.session_state["cp_posts_page"] = 1
            st.rerun()
    with page_cols[1]:
        if st.button("‹ Prev", disabled=current_page == 1, key="cp_posts_prev", use_container_width=True):
            st.session_state["cp_posts_page"] = current_page - 1
            st.rerun()
    with page_cols[2]:
        st.markdown(
            f'<div style="text-align:center; padding:6px 0; font-size:0.9rem;">'
            f'Page <strong>{current_page}</strong> of <strong>{total_pages}</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with page_cols[3]:
        if st.button("Next ›", disabled=current_page == total_pages, key="cp_posts_next", use_container_width=True):
            st.session_state["cp_posts_page"] = current_page + 1
            st.rerun()
    with page_cols[4]:
        if st.button("Last »", disabled=current_page == total_pages, key="cp_posts_last", use_container_width=True):
            st.session_state["cp_posts_page"] = total_pages
            st.rerun()

st.markdown("")

# --- Network Performance ---
render_section_header("Performance by Platform")
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

st.markdown("")

# --- Full Post Table ---
render_section_header("All Posts")
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
