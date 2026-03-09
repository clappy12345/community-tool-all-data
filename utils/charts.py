import pandas as pd
import streamlit as st
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

_FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


def _is_light_mode() -> bool:
    return st.session_state.get("light_mode", False)


def apply_dark_theme(fig, height=400):
    light = _is_light_mode()
    text_color = "#1a1a2e" if light else "#FAFAFA"
    secondary_color = "#5a6577" if light else "#8899A6"
    grid_color = "rgba(0,0,0,0.05)" if light else "rgba(255,255,255,0.04)"
    tooltip_bg = "rgba(255,255,255,0.96)" if light else "rgba(26,29,35,0.95)"
    tooltip_border = "rgba(0,0,0,0.10)" if light else "rgba(0,180,216,0.25)"
    tooltip_text = "#1a1a2e" if light else "#FAFAFA"

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color, size=12, family=_FONT_FAMILY),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=secondary_color),
            borderwidth=0,
        ),
        margin=dict(l=40, r=20, t=60, b=40),
        height=height,
        hoverlabel=dict(
            bgcolor=tooltip_bg,
            bordercolor=tooltip_border,
            font_size=12,
            font_color=tooltip_text,
            font_family=_FONT_FAMILY,
        ),
        title=dict(
            font=dict(size=15, color=text_color, family=_FONT_FAMILY),
            x=0,
            xanchor="left",
            y=0.97,
        ),
    )
    fig.update_xaxes(
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(size=11, color=secondary_color),
    )
    fig.update_yaxes(
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(size=11, color=secondary_color),
    )
    return fig


def daily_bar(daily_df, y_col, title, color="#00B4D8"):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=daily_df["Date"],
            y=daily_df[y_col],
            marker_color=color,
            marker_line_width=0,
            marker_cornerradius=6,
            text=daily_df[y_col].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
            textfont=dict(size=10, color="#8899A6" if not _is_light_mode() else "#5a6577"),
        )
    )
    fig.update_layout(
        title=title, xaxis_title="", yaxis_title="", bargap=0.2,
        xaxis=dict(showgrid=False),
    )
    return apply_dark_theme(fig)


def daily_timeline(daily_df, y_col, title, color="#00B4D8"):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily_df["Date"],
            y=daily_df[y_col],
            mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline"),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
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
            marker_line_width=0,
            marker_cornerradius=6,
            text=platform_df[y_col].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    fig.update_layout(
        title=title, xaxis_title="", yaxis_title="",
        xaxis=dict(showgrid=False),
    )
    return apply_dark_theme(fig)


def daily_engagement_timeline_with_hover(daily_df, title="Daily Impressions Timeline"):
    color = "#00B4D8"
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_df["Date"],
            y=daily_df["Impressions"],
            mode="lines",
            line=dict(color=color, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(0,180,216,0.06)",
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
            marker=dict(
                size=9, color=color,
                line=dict(width=2, color="rgba(255,255,255,0.8)" if not _is_light_mode() else "rgba(255,255,255,1)"),
            ),
            hovertemplate="%{x|%b %d, %Y}<extra></extra>",
            showlegend=False,
            name="Engagements",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title="",
        xaxis=dict(tickformat="%b %d", showgrid=False),
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
            line=dict(color=color, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(6,214,160,0.06)",
            hoverinfo="skip",
            showlegend=False,
            name="_line",
        )
    )

    marker_border = "rgba(255,255,255,0.8)" if not _is_light_mode() else "rgba(255,255,255,1)"
    if has_hover:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Impact Score"],
                mode="markers",
                marker=dict(size=9, color=color, line=dict(width=2, color=marker_border)),
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
                marker=dict(size=9, color=color, line=dict(width=2, color=marker_border)),
                hovertemplate="%{x|%b %d, %Y}<br>Impact Score: %{y:.1f}<extra></extra>",
                showlegend=False,
                name="Impact Score",
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title="Impact Score",
        xaxis=dict(tickformat="%b %d", showgrid=False),
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
            marker_line_width=0,
            marker_cornerradius=6,
            text=ct_df["Engagements"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    fig.update_layout(
        title=title, xaxis_title="", yaxis_title="",
        xaxis=dict(showgrid=False),
    )
    return apply_dark_theme(fig)


def platform_share_pie(platform_df, value_col, title):
    colors = [PLATFORM_COLORS.get(n, "#00B4D8") for n in platform_df["Network"]]
    fig = go.Figure(
        go.Pie(
            labels=platform_df["Network"],
            values=platform_df[value_col],
            marker=dict(colors=colors, line=dict(width=2, color="rgba(14,17,23,0.8)" if not _is_light_mode() else "#FFFFFF")),
            textinfo="percent",
            textfont=dict(size=12),
            hole=0.45,
        )
    )
    fig.update_layout(
        title=title,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    return apply_dark_theme(fig, height=400)


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
                line=dict(color=PLATFORM_COLORS.get(network, "#00B4D8"), width=2.5, shape="spline"),
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
            marker_line_width=0,
            marker_cornerradius=5,
            text=top["Count"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    fig.update_layout(
        title=title,
        yaxis=dict(autorange="reversed"),
        xaxis_title="Messages",
        xaxis=dict(showgrid=False),
    )
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
            marker_line_width=0,
            marker_cornerradius=4,
        )
    )
    fig.add_trace(
        go.Bar(
            y=top["Theme"],
            x=top["Pct Negative"],
            name="Negative",
            orientation="h",
            marker_color=SENTIMENT_COLORS["negative"],
            marker_line_width=0,
            marker_cornerradius=4,
        )
    )
    fig.update_layout(
        title=title,
        barmode="group",
        yaxis=dict(autorange="reversed"),
        xaxis_title="% of Messages",
        xaxis=dict(showgrid=False),
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
                    marker_line_width=0,
                    marker_cornerradius=4,
                )
            )
    fig.update_layout(
        title=title,
        barmode="stack",
        xaxis_title="Messages",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(showgrid=False),
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
            marker_line_width=0,
            marker_cornerradius=5,
            text=top[count_col].apply(lambda v: f"{v:,}"),
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    fig.update_layout(
        title=title,
        yaxis=dict(autorange="reversed"),
        xaxis_title="Count",
        xaxis=dict(showgrid=False),
    )
    return apply_dark_theme(fig, height=max(280, len(top) * 40))


def topic_percentage_bar(topic_df, title="What the Community Is Talking About"):
    """Horizontal bar showing conversation topic buckets by % of messages."""
    top = topic_df.head(15)
    labels = top["Topic"].tolist()
    colors = [
        "#3a3f4a" if t == "Other / Uncategorized" else "#00B4D8"
        for t in labels
    ]
    text_color = "#5a6577" if _is_light_mode() else "#FAFAFA"
    fig = go.Figure(
        go.Bar(
            y=labels,
            x=top["Pct"],
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            marker_cornerradius=5,
            text=top["Pct"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(size=11, color=text_color),
        )
    )
    fig.update_layout(
        title=title,
        yaxis=dict(autorange="reversed"),
        xaxis_title="% of Messages",
        xaxis=dict(range=[0, top["Pct"].max() * 1.35], showgrid=False),
    )
    return apply_dark_theme(fig, height=max(340, len(top) * 38))


def campaign_day_overlay(daily_a, daily_b, y_col, label_a, label_b, title=""):
    """Overlay two daily-metric series aligned by relative campaign day."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily_a["Campaign Day"],
            y=daily_a[y_col],
            mode="lines+markers",
            name=label_a,
            line=dict(color="#00B4D8", width=2.5, shape="spline"),
            marker=dict(size=5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily_b["Campaign Day"],
            y=daily_b[y_col],
            mode="lines+markers",
            name=label_b,
            line=dict(color="#90E0EF", width=2.5, shape="spline"),
            marker=dict(size=5),
        )
    )
    fig.update_layout(
        title=title or f"{y_col} by Campaign Day",
        xaxis_title="Campaign Day",
        yaxis_title=y_col,
    )
    return apply_dark_theme(fig)


def comparison_bar(label_a, label_b, metrics_a, metrics_b, metric_names):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=[metrics_a.get(m, 0) for m in metric_names],
            name=label_a,
            marker_color="#00B4D8",
            marker_line_width=0,
            marker_cornerradius=6,
        )
    )
    fig.add_trace(
        go.Bar(
            x=metric_names,
            y=[metrics_b.get(m, 0) for m in metric_names],
            name=label_b,
            marker_color="#90E0EF",
            marker_line_width=0,
            marker_cornerradius=6,
        )
    )
    fig.update_layout(
        title="Period Comparison", barmode="group",
        xaxis=dict(showgrid=False),
    )
    return apply_dark_theme(fig)


def add_event_markers(fig, events, x_mode="date", anchor_date=None):
    """Add vertical dashed lines with labels for campaign events.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure to annotate.
    events : list[dict]
        Each dict has ``name``, ``date`` (str or date), and optional ``color``.
    x_mode : str
        ``"date"`` places lines at calendar dates on the x-axis.
        ``"campaign_day"`` converts dates to relative days from *anchor_date*.
    anchor_date : date-like, optional
        Required when *x_mode* is ``"campaign_day"``.
    """
    if not events:
        return fig

    _DEFAULT_COLORS = [
        "#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3",
        "#F38181", "#AA96DA", "#FCBAD3", "#A8D8EA",
    ]
    light = _is_light_mode()

    for i, ev in enumerate(events):
        name = ev.get("name", "")
        raw_date = ev.get("date")
        if not raw_date:
            continue

        evt_date = pd.Timestamp(raw_date).date()
        color = ev.get("color") or _DEFAULT_COLORS[i % len(_DEFAULT_COLORS)]

        if x_mode == "campaign_day":
            if anchor_date is None:
                continue
            anchor = pd.Timestamp(anchor_date).date()
            x_val = (evt_date - anchor).days
        else:
            x_val = evt_date

        label_color = "#333" if light else "#eee"

        fig.add_vline(
            x=x_val,
            line_dash="dot",
            line_color=color,
            line_width=1.5,
            opacity=0.7,
        )
        fig.add_annotation(
            x=x_val,
            y=1.02,
            yref="paper",
            text=f"<b>{name}</b>",
            showarrow=False,
            font=dict(size=9, color=label_color, family=_FONT_FAMILY),
            bgcolor=color,
            borderpad=3,
            opacity=0.85,
            textangle=-35,
        )

    return fig
