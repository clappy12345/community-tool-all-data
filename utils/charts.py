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


def sentiment_donut(sentiment_counts, title="Community Sentiment"):
    labels = []
    values = []
    colors = []

    for sentiment in ["positive", "neutral", "negative"]:
        if sentiment in sentiment_counts.index:
            labels.append(sentiment.title())
            values.append(sentiment_counts[sentiment])
            colors.append(SENTIMENT_COLORS.get(sentiment, "#808080"))

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors),
            textinfo="percent+label",
            textfont=dict(size=13),
        )
    )
    fig.update_layout(title=title, showlegend=False)
    return apply_dark_theme(fig, height=350)


def sentiment_timeline(daily_sentiment_df, title="Sentiment Over Time"):
    fig = go.Figure()
    for sentiment in ["positive", "neutral", "negative"]:
        if sentiment in daily_sentiment_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=daily_sentiment_df["Date"],
                    y=daily_sentiment_df[sentiment],
                    mode="lines",
                    name=sentiment.title(),
                    line=dict(
                        color=SENTIMENT_COLORS.get(sentiment, "#808080"), width=2
                    ),
                    stackgroup="one",
                )
            )
    fig.update_layout(title=title, xaxis_title="", yaxis_title="Messages")
    return apply_dark_theme(fig)


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
