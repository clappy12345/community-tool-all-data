import plotly.express as px
import plotly.graph_objects as go

PLATFORM_COLORS = {
    "X": "#1DA1F2",
    "Facebook": "#1877F2",
    "Instagram": "#E4405F",
    "TikTok": "#69C9D0",
    "YouTube": "#FF0000",
    "Threads": "#808080",
    "Reddit": "#FF4500",
}

SENTIMENT_COLORS = {
    "positive": "#06D6A0",
    "negative": "#EF476F",
    "neutral": "#FFD166",
}

CHART_CONFIG = {
    "toImageButtonOptions": {"format": "png", "height": 600, "width": 1200},
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def apply_dark_theme(fig, height=400):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA", size=12),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", zeroline=False)
    return fig


def daily_bar(daily_df, y_col, title, color="#00B4D8"):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=daily_df["Date"],
            y=daily_df[y_col],
            marker_color=color,
            marker_line_width=0,
            text=daily_df[y_col].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
            textfont=dict(size=9, color="#90A4AE"),
        )
    )
    fig.update_layout(title=title, xaxis_title="", yaxis_title="", bargap=0.15)
    return apply_dark_theme(fig)


def daily_timeline(daily_df, y_col, title, color="#00B4D8"):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily_df["Date"],
            y=daily_df[y_col],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)",
            name=y_col,
        )
    )
    fig.update_layout(title=title, xaxis_title="", yaxis_title=y_col)
    return apply_dark_theme(fig)


def platform_bar(platform_df, y_col, title):
    colors = [PLATFORM_COLORS.get(n, "#00B4D8") for n in platform_df["Network"]]
    fig = go.Figure(
        go.Bar(
            x=platform_df["Network"],
            y=platform_df[y_col],
            marker_color=colors,
            text=platform_df[y_col].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
        )
    )
    fig.update_layout(title=title, xaxis_title="", yaxis_title="")
    return apply_dark_theme(fig)


def daily_engagement_timeline_with_hover(daily_df, title="Daily Impressions Timeline"):
    color = "#00B4D8"
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_df["Date"],
            y=daily_df["Impressions"],
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor="rgba(0,180,216,0.08)",
            hoverinfo="skip",
            showlegend=False,
            name="_line",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily_df["Date"],
            y=daily_df["Impressions"],
            mode="markers",
            marker=dict(size=10, color=color, line=dict(width=1, color="#FAFAFA")),
            hovertemplate="%{x|%b %d, %Y}<extra></extra>",
            showlegend=False,
            name="Engagements",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title="",
        xaxis=dict(tickformat="%b %d"),
        showlegend=False,
    )
    return apply_dark_theme(fig, height=420)


def looker_sentiment_timeline(df, title="Daily Sentiment Score"):
    color = "#06D6A0"
    fig = go.Figure()

    has_hover = "Top Post" in df.columns and "Top Network" in df.columns

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Impact Score"],
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor="rgba(6,214,160,0.08)",
            hoverinfo="skip",
            showlegend=False,
            name="_line",
        )
    )

    if has_hover:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Impact Score"],
                mode="markers",
                marker=dict(size=10, color=color, line=dict(width=1, color="#FAFAFA")),
                customdata=df[["Top Network", "Top Post"]].values,
                hovertemplate=(
                    "<b>%{x|%b %d, %Y}</b><br>"
                    "Impact Score: %{y:.1f}<br>"
                    "<br>Top Post (%{customdata[0]}):<br>"
                    "%{customdata[1]}"
                    "<extra></extra>"
                ),
                showlegend=False,
                name="Impact Score",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Impact Score"],
                mode="markers",
                marker=dict(size=10, color=color, line=dict(width=1, color="#FAFAFA")),
                hovertemplate="%{x|%b %d, %Y}<br>Impact Score: %{y:.1f}<extra></extra>",
                showlegend=False,
                name="Impact Score",
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title="Impact Score",
        xaxis=dict(tickformat="%b %d"),
        showlegend=False,
    )
    return apply_dark_theme(fig, height=420)


def content_type_bar(ct_df, title="Performance by Content Type"):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=ct_df["Content Type"],
            y=ct_df["Engagements"],
            name="Total Engagements",
            marker_color="#00B4D8",
            text=ct_df["Engagements"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
        )
    )
    fig.update_layout(title=title, xaxis_title="", yaxis_title="")
    return apply_dark_theme(fig)


def platform_share_pie(platform_df, value_col, title):
    colors = [PLATFORM_COLORS.get(n, "#00B4D8") for n in platform_df["Network"]]
    fig = go.Figure(
        go.Pie(
            labels=platform_df["Network"],
            values=platform_df[value_col],
            marker=dict(colors=colors),
            textinfo="percent+label",
            textfont=dict(size=12),
        )
    )
    fig.update_layout(title=title, showlegend=False)
    return apply_dark_theme(fig, height=380)


def daily_platform_lines(profile_df, y_col, title):
    fig = go.Figure()
    for network in sorted(profile_df["Network"].unique()):
        ndf = profile_df[profile_df["Network"] == network]
        daily = ndf.groupby("Date")[y_col].sum().reset_index()
        fig.add_trace(
            go.Scatter(
                x=daily["Date"],
                y=daily[y_col],
                mode="lines+markers",
                name=network,
                line=dict(color=PLATFORM_COLORS.get(network, "#00B4D8"), width=2),
                marker=dict(size=4),
            )
        )
    fig.update_layout(title=title, xaxis_title="", yaxis_title=y_col)
    return apply_dark_theme(fig)


def theme_bar(theme_df, title="Top Community Themes"):
    top = theme_df.head(15)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=top["Theme"],
            x=top["Count"],
            orientation="h",
            marker_color="#00B4D8",
            text=top["Count"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
        )
    )
    fig.update_layout(title=title, yaxis=dict(autorange="reversed"), xaxis_title="Messages")
    return apply_dark_theme(fig, height=max(350, len(top) * 35))


def theme_sentiment_bar(theme_df, title="Sentiment by Theme"):
    top = theme_df[theme_df["Theme"] != "Uncategorized"].head(12)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=top["Theme"],
            x=top["Pct Positive"],
            name="Positive",
            orientation="h",
            marker_color=SENTIMENT_COLORS["positive"],
        )
    )
    fig.add_trace(
        go.Bar(
            y=top["Theme"],
            x=top["Pct Negative"],
            name="Negative",
            orientation="h",
            marker_color=SENTIMENT_COLORS["negative"],
        )
    )
    fig.update_layout(
        title=title,
        barmode="group",
        yaxis=dict(autorange="reversed"),
        xaxis_title="% of Messages",
    )
    return apply_dark_theme(fig, height=max(350, len(top) * 40))


def sentiment_by_platform_bar(grouped_df, title="Sentiment by Platform"):
    """Stacked horizontal bar of sentiment distribution per platform."""
    import pandas as pd
    pivoted = grouped_df.pivot_table(
        index="Network Name", columns="Sentiment", values="Count", fill_value=0
    ).reset_index()

    platforms = pivoted["Network Name"].tolist()
    fig = go.Figure()
    for sent in ["positive", "neutral", "negative"]:
        if sent in pivoted.columns:
            fig.add_trace(
                go.Bar(
                    y=platforms,
                    x=pivoted[sent],
                    name=sent.title(),
                    orientation="h",
                    marker_color=SENTIMENT_COLORS.get(sent, "#808080"),
                )
            )
    fig.update_layout(
        title=title,
        barmode="stack",
        xaxis_title="Messages",
        yaxis=dict(autorange="reversed"),
    )
    return apply_dark_theme(fig, height=max(300, len(platforms) * 50))


def horizontal_breakdown_bar(df, label_col, count_col, title, color="#00B4D8"):
    """Simple horizontal bar for categorical breakdowns."""
    top = df.head(10)
    fig = go.Figure(
        go.Bar(
            y=top[label_col],
            x=top[count_col],
            orientation="h",
            marker_color=color,
            text=top[count_col].apply(lambda v: f"{v:,}"),
            textposition="outside",
        )
    )
    fig.update_layout(title=title, yaxis=dict(autorange="reversed"), xaxis_title="Count")
    return apply_dark_theme(fig, height=max(280, len(top) * 40))


def topic_percentage_bar(topic_df, title="What the Community Is Talking About"):
    """Horizontal bar showing conversation topic buckets by % of messages."""
    top = topic_df.head(15)
    labels = top["Topic"].tolist()
    colors = [
        "#555555" if t == "Other / Uncategorized" else "#00B4D8"
        for t in labels
    ]
    fig = go.Figure(
        go.Bar(
            y=labels,
            x=top["Pct"],
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=top["Pct"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(size=12, color="#FAFAFA"),
        )
    )
    fig.update_layout(
        title=title,
        yaxis=dict(autorange="reversed"),
        xaxis_title="% of Messages",
        xaxis=dict(range=[0, top["Pct"].max() * 1.35]),
    )
    return apply_dark_theme(fig, height=max(340, len(top) * 38))


def comparison_bar(label_a, label_b, metrics_a, metrics_b, metric_names):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=[metrics_a.get(m, 0) for m in metric_names],
            name=label_a,
            marker_color="#00B4D8",
        )
    )
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=[metrics_b.get(m, 0) for m in metric_names],
            name=label_b,
            marker_color="#90E0EF",
        )
    )
    fig.update_layout(title="Period Comparison", barmode="group")
    return apply_dark_theme(fig)
