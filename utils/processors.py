import re
from collections import Counter
from datetime import timedelta

import pandas as pd


def apply_filters(df, filters, date_col="Date", network_col="Network"):
    filtered = df.copy()

    if "date_range" in filters and filters["date_range"]:
        dr = filters["date_range"]
        if isinstance(dr, (list, tuple)) and len(dr) == 2:
            start, end = dr
            if date_col in filtered.columns:
                filtered = filtered[
                    (filtered[date_col].dt.date >= start)
                    & (filtered[date_col].dt.date <= end)
                ]

    if "networks" in filters and filters["networks"] and network_col in filtered.columns:
        filtered = filtered[filtered[network_col].isin(filters["networks"])]

    return filtered


def get_kpis(post_df, profile_df):
    total_impressions = post_df["Impressions"].sum()
    total_engagements = post_df["Engagements"].sum()
    total_reach = post_df["Reach"].sum() if "Reach" in post_df.columns else 0
    total_video_views = post_df["Video Views"].sum()

    avg_engagement_rate = (
        (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
    )

    audience_growth = profile_df["Net Audience Growth"].sum()

    latest_date = profile_df["Date"].max()
    latest_audience = (
        profile_df[profile_df["Date"] == latest_date]
        .groupby("Network")["Audience"]
        .max()
        .sum()
    )

    total_posts = len(post_df)
    total_comments = post_df["Comments"].sum()
    total_shares = post_df["Shares"].sum()

    return {
        "total_impressions": total_impressions,
        "total_engagements": total_engagements,
        "total_reach": total_reach,
        "total_video_views": total_video_views,
        "avg_engagement_rate": avg_engagement_rate,
        "audience_growth": audience_growth,
        "total_audience": latest_audience,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_shares": total_shares,
    }


def get_kpis_safe(post_df, profile_df=None):
    """Compute KPIs from post data, optionally enriched with profile data."""
    if profile_df is not None and len(profile_df) > 0:
        return get_kpis(post_df, profile_df)

    total_imp = post_df["Impressions"].sum()
    total_eng = post_df["Engagements"].sum()
    return {
        "total_impressions": total_imp,
        "total_engagements": total_eng,
        "total_reach": post_df["Reach"].sum() if "Reach" in post_df.columns else 0,
        "total_video_views": post_df["Video Views"].sum(),
        "avg_engagement_rate": (total_eng / total_imp * 100) if total_imp > 0 else 0,
        "audience_growth": 0,
        "total_audience": 0,
        "total_posts": len(post_df),
        "total_comments": post_df["Comments"].sum(),
        "total_shares": post_df["Shares"].sum(),
    }


def get_daily_metrics(profile_df):
    daily = (
        profile_df.groupby("Date")
        .agg(
            {
                "Impressions": "sum",
                "Engagements": "sum",
                "Video Views": "sum",
                "Net Audience Growth": "sum",
            }
        )
        .reset_index()
    )
    daily["Cumulative Audience Growth"] = daily["Net Audience Growth"].cumsum()
    return daily


def get_platform_summary(profile_df):
    platform = (
        profile_df.groupby("Network")
        .agg(
            {
                "Impressions": "sum",
                "Engagements": "sum",
                "Video Views": "sum",
                "Net Audience Growth": "sum",
            }
        )
        .reset_index()
    )

    latest_date = profile_df["Date"].max()
    latest_audience = (
        profile_df[profile_df["Date"] == latest_date]
        .groupby("Network")["Audience"]
        .max()
        .reset_index()
    )
    platform = platform.merge(latest_audience, on="Network", how="left")

    platform["Engagement Rate"] = (
        platform["Engagements"] / platform["Impressions"] * 100
    ).fillna(0)

    return platform


def get_top_posts(post_df, n=10, sort_by="Engagements"):
    exclude_types = ["Story", "@Reply", "'@Reply"]
    filtered = post_df[~post_df["Post Type"].isin(exclude_types)]
    return filtered.nlargest(n, sort_by)


def get_daily_post_engagement(post_df):
    exclude_types = ["Story", "@Reply", "'@Reply"]
    df = post_df[~post_df["Post Type"].isin(exclude_types)].copy()

    daily_agg = (
        df.groupby(df["Date"].dt.normalize())
        .agg(
            Total_Engagements=("Engagements", "sum"),
            Impressions=("Impressions", "sum"),
            Posts=("Engagements", "count"),
        )
        .reset_index()
    )

    top_posts = []
    for date in daily_agg["Date"]:
        day_posts = df[df["Date"].dt.normalize() == date]
        top = day_posts.nlargest(1, "Engagements").iloc[0]
        top_posts.append(
            {
                "Date": date,
                "Top Post": str(top.get("Post", ""))[:120].replace("\n", " "),
                "Top Network": top.get("Network", ""),
                "Top Post Engagements": top["Engagements"],
                "Top Post Link": top.get("Link", ""),
            }
        )

    top_df = pd.DataFrame(top_posts)
    daily = daily_agg.merge(top_df, on="Date", how="left")
    return daily.sort_values("Date")


def get_posts_for_date(post_df, date):
    exclude_types = ["Story", "@Reply", "'@Reply"]
    df = post_df[~post_df["Post Type"].isin(exclude_types)].copy()
    day_posts = df[df["Date"].dt.normalize() == pd.Timestamp(date).normalize()]
    return day_posts.sort_values("Engagements", ascending=False)


def get_content_type_performance(post_df):
    exclude_types = ["Story", "@Reply", "'@Reply"]
    filtered = post_df[~post_df["Post Type"].isin(exclude_types)]
    result = (
        filtered.groupby("Content Type")
        .agg(
            Posts=("Engagements", "count"),
            Impressions=("Impressions", "sum"),
            Engagements=("Engagements", "sum"),
            Reactions=("Reactions", "sum"),
            Comments=("Comments", "sum"),
            Shares=("Shares", "sum"),
        )
        .reset_index()
    )
    result["Avg Engagements"] = (result["Engagements"] / result["Posts"]).round(0)
    result["Engagement Rate"] = (
        result["Engagements"] / result["Impressions"] * 100
    ).fillna(0)
    return result.sort_values("Engagements", ascending=False)


def get_network_content_performance(post_df):
    exclude_types = ["Story", "@Reply", "'@Reply"]
    filtered = post_df[~post_df["Post Type"].isin(exclude_types)]
    return (
        filtered.groupby("Network")
        .agg(
            Posts=("Engagements", "count"),
            Impressions=("Impressions", "sum"),
            Engagements=("Engagements", "sum"),
            Reactions=("Reactions", "sum"),
            Comments=("Comments", "sum"),
            Shares=("Shares", "sum"),
            Video_Views=("Video Views", "sum"),
        )
        .reset_index()
        .sort_values("Engagements", ascending=False)
    )


def combine_community_messages(aff_df=None, inbox_df=None):
    """Merge Affogata and Inbox messages into a single DataFrame with Link/Source."""
    frames = []
    if aff_df is not None and len(aff_df) > 0:
        a = aff_df[["Created At", "Network Name", "Text", "Sentiment"]].copy()
        a["Engagements"] = aff_df["Total Engagements"] if "Total Engagements" in aff_df.columns else 0
        a["Link"] = aff_df["URL"] if "URL" in aff_df.columns else ""
        a["Source"] = "Community"
        a.columns = ["Timestamp", "Network", "Text", "Sentiment", "Engagements", "Link", "Source"]
        frames.append(a)
    if inbox_df is not None and len(inbox_df) > 0 and "Message" in inbox_df.columns:
        cols_needed = ["Timestamp", "Network", "Message", "Sentiment"]
        if all(c in inbox_df.columns for c in cols_needed):
            b = inbox_df[cols_needed].copy()
            b["Engagements"] = 0
            b["Link"] = inbox_df["Permalink"] if "Permalink" in inbox_df.columns else ""
            b["Source"] = "Direct"
            b.columns = ["Timestamp", "Network", "Text", "Sentiment", "Engagements", "Link", "Source"]
            frames.append(b)
    if not frames:
        return pd.DataFrame(columns=["Timestamp", "Network", "Text", "Sentiment", "Engagements", "Link", "Source"])
    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["Text"].notna() & (combined["Text"].str.strip() != "")]
    return combined


def get_messages_around_beat(affogata_df, inbox_df, beat_date, days_window=1):
    start = pd.Timestamp(beat_date) - timedelta(days=days_window)
    end = pd.Timestamp(beat_date) + timedelta(days=days_window + 1)

    frames = []

    if affogata_df is not None and len(affogata_df) > 0:
        mask = (affogata_df["Created At"] >= start) & (affogata_df["Created At"] < end)
        aff = affogata_df[mask].copy()
        if len(aff) > 0:
            aff_out = pd.DataFrame(
                {
                    "Timestamp": aff["Created At"],
                    "Network": aff["Network Name"],
                    "Text": aff["Text"],
                    "Sentiment": aff["Sentiment"],
                    "Engagements": aff["Total Engagements"],
                    "Source": "Community",
                    "Link": aff["URL"] if "URL" in aff.columns else "",
                }
            )
            frames.append(aff_out)

    if inbox_df is not None and len(inbox_df) > 0 and "Timestamp" in inbox_df.columns:
        mask = (inbox_df["Timestamp"] >= start) & (inbox_df["Timestamp"] < end)
        inb = inbox_df[mask].copy()
        if len(inb) > 0:
            inb_out = pd.DataFrame(
                {
                    "Timestamp": inb["Timestamp"],
                    "Network": inb["Network"],
                    "Text": inb["Message"],
                    "Sentiment": inb["Sentiment"],
                    "Engagements": 0,
                    "Source": "Direct",
                    "Link": inb["Permalink"] if "Permalink" in inb.columns else "",
                }
            )
            frames.append(inb_out)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined = combined[combined["Text"].notna() & (combined["Text"].str.strip() != "")]
        return combined

    return pd.DataFrame(columns=["Timestamp", "Network", "Text", "Sentiment", "Engagements", "Source", "Link"])


def format_number(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,.0f}"


# ─────────────────────────────────────────────────────────────
# Data-driven conversation driver helpers (no AI required)
# ─────────────────────────────────────────────────────────────


def get_sentiment_by_platform(aff_df):
    """Sentiment distribution per platform from Affogata data."""
    if aff_df is None or len(aff_df) == 0 or "Sentiment" not in aff_df.columns:
        return None
    grouped = (
        aff_df.groupby(["Network Name", "Sentiment"])
        .size()
        .reset_index(name="Count")
    )
    return grouped


def get_interaction_type_breakdown(aff_df):
    """Interaction type distribution from Affogata data."""
    if aff_df is None or len(aff_df) == 0 or "Interaction Type" not in aff_df.columns:
        return None
    counts = (
        aff_df["Interaction Type"]
        .str.strip()
        .str.lower()
        .value_counts()
        .reset_index()
    )
    counts.columns = ["Interaction Type", "Count"]
    return counts


def get_message_intent_breakdown(inbox_df):
    """Message intent distribution from Inbox data (Sprout classification)."""
    if inbox_df is None or len(inbox_df) == 0 or "Message Intent" not in inbox_df.columns:
        return None
    counts = (
        inbox_df["Message Intent"]
        .str.strip()
        .str.lower()
        .value_counts()
        .reset_index()
    )
    counts.columns = ["Message Intent", "Count"]
    counts = counts[counts["Message Intent"] != "unclassified"]
    if len(counts) == 0:
        return None
    return counts


def get_message_type_breakdown(inbox_df):
    """Message type breakdown (Comment, DM, Mention, Reply) from Inbox data."""
    if inbox_df is None or len(inbox_df) == 0 or "Message Type" not in inbox_df.columns:
        return None
    counts = (
        inbox_df["Message Type"]
        .str.strip()
        .value_counts()
        .reset_index()
    )
    counts.columns = ["Message Type", "Count"]
    return counts


def get_top_engaged_messages(aff_df, n=5):
    """Top N community messages by total engagements."""
    if aff_df is None or len(aff_df) == 0 or "Total Engagements" not in aff_df.columns:
        return None
    valid = aff_df[aff_df["Text"].notna() & (aff_df["Text"].str.strip() != "")]
    if len(valid) == 0:
        return None
    top = valid.nlargest(n, "Total Engagements")
    return top[["Created At", "Network Name", "Text", "Sentiment",
                 "Total Engagements", "URL"]].copy()


def get_sentiment_trend_community(aff_df):
    """Daily positive/negative/neutral message counts from Affogata."""
    if aff_df is None or len(aff_df) == 0 or "Sentiment" not in aff_df.columns:
        return None
    df = aff_df.copy()
    df["Date"] = df["Created At"].dt.normalize()
    daily = (
        df.groupby(["Date", "Sentiment"])
        .size()
        .reset_index(name="Count")
    )
    return daily


def get_peak_conversation_days(aff_df, inbox_df=None, n=5):
    """Days with the highest total community message volume."""
    frames = []
    if aff_df is not None and len(aff_df) > 0:
        a = aff_df[["Created At"]].copy()
        a["Date"] = a["Created At"].dt.normalize()
        frames.append(a[["Date"]])
    if inbox_df is not None and len(inbox_df) > 0 and "Timestamp" in inbox_df.columns:
        b = inbox_df[["Timestamp"]].copy()
        b["Date"] = b["Timestamp"].dt.normalize()
        frames.append(b[["Date"]])
    if not frames:
        return None
    all_dates = pd.concat(frames, ignore_index=True)
    daily = all_dates.groupby("Date").size().reset_index(name="Messages")
    return daily.nlargest(n, "Messages").sort_values("Date")


# ─────────────────────────────────────────────────────────────
# Keyword-bucket topic detection (no AI)
# ─────────────────────────────────────────────────────────────


def _collect_texts(aff_df=None, inbox_df=None):
    """Gather all message text from Affogata and Inbox into a list."""
    texts = []
    if aff_df is not None and len(aff_df) > 0 and "Text" in aff_df.columns:
        texts.extend(aff_df["Text"].dropna().tolist())
    if inbox_df is not None and len(inbox_df) > 0 and "Message" in inbox_df.columns:
        texts.extend(inbox_df["Message"].dropna().tolist())
    return texts


def _collect_texts_with_dates(aff_df=None, inbox_df=None):
    """Return list of (text, date) tuples for temporal analysis."""
    items = []
    if aff_df is not None and len(aff_df) > 0:
        if "Text" in aff_df.columns and "Created At" in aff_df.columns:
            for _, r in aff_df.dropna(subset=["Text"]).iterrows():
                items.append((r["Text"], pd.Timestamp(r["Created At"])))
    if inbox_df is not None and len(inbox_df) > 0:
        date_col = "Date" if "Date" in inbox_df.columns else "Timestamp (PT)"
        if "Message" in inbox_df.columns and date_col in inbox_df.columns:
            for _, r in inbox_df.dropna(subset=["Message"]).iterrows():
                items.append((r["Message"], pd.Timestamp(r[date_col])))
    return items


def get_topic_deltas(aff_df=None, inbox_df=None, buckets=None):
    """Compare topic % between the first and second halves of the data period.

    Returns a DataFrame with columns ["Topic", "Pct", "Pct_prev", "Delta"]
    sorted by Delta descending, or None if insufficient data.
    """
    items = _collect_texts_with_dates(aff_df, inbox_df)
    if len(items) < 10:
        return None

    if buckets is None:
        from utils.titles import get_title_config
        cfg = get_title_config()
        buckets = cfg.get("topic_buckets", {})
    if not buckets:
        return None

    dates = [d for _, d in items]
    mid = sorted(dates)[len(dates) // 2]

    first_half = [t for t, d in items if d < mid]
    second_half = [t for t, d in items if d >= mid]
    if len(first_half) < 5 or len(second_half) < 5:
        return None

    def _pct(texts_list):
        total = len(texts_list)
        counts = {}
        for raw in texts_list:
            text_lower = str(raw).lower()
            for name, keywords in buckets.items():
                if any(kw in text_lower for kw in keywords):
                    counts[name] = counts.get(name, 0) + 1
        return {name: round(c / total * 100, 1) for name, c in counts.items()}

    prev = _pct(first_half)
    curr = _pct(second_half)
    all_topics = set(prev) | set(curr)

    rows = []
    for topic in all_topics:
        p = prev.get(topic, 0.0)
        c = curr.get(topic, 0.0)
        rows.append({"Topic": topic, "Pct": c, "Pct_prev": p, "Delta": round(c - p, 1)})

    rows.sort(key=lambda r: abs(r["Delta"]), reverse=True)
    return pd.DataFrame(rows) if rows else None


def get_top_conversation_topics(aff_df=None, inbox_df=None, buckets=None):
    """Count what % of community messages match each keyword bucket.

    Parameters
    ----------
    buckets : dict[str, list[str]] | None
        Topic name -> list of lowercase keywords/phrases.
        If None, loads defaults from the active title config.

    Returns a DataFrame with columns ["Topic", "Messages", "Pct"] or None.
    """
    texts = _collect_texts(aff_df, inbox_df)
    if len(texts) < 5:
        return None

    if buckets is None:
        from utils.titles import get_title_config
        cfg = get_title_config()
        buckets = cfg.get("topic_buckets", {})

    if not buckets:
        return None

    total = len(texts)
    counts = {name: 0 for name in buckets}
    other_count = 0

    for raw in texts:
        text_lower = str(raw).lower()
        matched = False
        for name, keywords in buckets.items():
            if any(kw in text_lower for kw in keywords):
                counts[name] += 1
                matched = True
        if not matched:
            other_count += 1

    rows = [
        {"Topic": name, "Messages": c, "Pct": round(c / total * 100, 1)}
        for name, c in counts.items()
        if c > 0
    ]
    rows.sort(key=lambda r: r["Messages"], reverse=True)

    if other_count > 0:
        rows.append({
            "Topic": "Other / Uncategorized",
            "Messages": other_count,
            "Pct": round(other_count / total * 100, 1),
        })

    if not rows:
        return None
    return pd.DataFrame(rows)
