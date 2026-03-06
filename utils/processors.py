import pandas as pd
from datetime import timedelta


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
    total_reach = post_df["Reach"].sum()
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


def get_sentiment_distribution(affogata_df, inbox_df=None):
    counts = affogata_df["Sentiment"].value_counts()

    if inbox_df is not None and "Sentiment" in inbox_df.columns:
        inbox_counts = inbox_df["Sentiment"].value_counts()
        counts = counts.add(inbox_counts, fill_value=0)

    return counts


def get_sentiment_over_time(affogata_df, inbox_df=None):
    df = affogata_df.copy()
    df["Date"] = df["Created At"].dt.date
    daily = df.groupby(["Date", "Sentiment"]).size().unstack(fill_value=0).reset_index()
    daily["Date"] = pd.to_datetime(daily["Date"])
    return daily


def identify_key_beats(post_df, n=8):
    df = post_df.copy()
    exclude_types = ["Story", "@Reply", "'@Reply"]
    df = df[~df["Post Type"].isin(exclude_types)]
    df["DateOnly"] = df["Date"].dt.date

    daily_eng = df.groupby("DateOnly")["Engagements"].sum().nlargest(n)

    beats = []
    for date, total_eng in daily_eng.items():
        day_posts = df[df["DateOnly"] == date]
        top = day_posts.nlargest(1, "Engagements").iloc[0]
        post_text = str(top.get("Post", ""))[:80].replace("\n", " ")

        label = f"{date.strftime('%b %d')} — {post_text}..."
        beats.append(
            {
                "date": date,
                "total_engagements": total_eng,
                "top_post_text": post_text,
                "label": label,
                "network": top.get("Network", ""),
                "num_posts": len(day_posts),
            }
        )

    return beats


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
                }
            )
            frames.append(inb_out)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined = combined[combined["Text"].notna() & (combined["Text"].str.strip() != "")]
        return combined

    return pd.DataFrame(columns=["Timestamp", "Network", "Text", "Sentiment", "Engagements", "Source"])


def format_number(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,.0f}"
