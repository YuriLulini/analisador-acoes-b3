import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from config import REPORTS_DIR


def plot_candlestick(df: pd.DataFrame, ticker: str, name: str) -> str:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.55, 0.25, 0.20],
        subplot_titles=[f"{name} ({ticker}) - Preço", "Volume", "RSI"],
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Preço",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    for col, color, dash in [
        ("SMA20", "#ffa726", "solid"),
        ("SMA50", "#42a5f5", "solid"),
        ("EMA9", "#ab47bc", "dash"),
    ]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df[col], name=col, line=dict(color=color, width=1.2, dash=dash)),
                row=1, col=1,
            )

    if "BB_Upper" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["BB_Upper"],
                name="BB Superior", line=dict(color="rgba(150,150,150,0.5)", width=1, dash="dot"),
                showlegend=False,
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["BB_Lower"],
                name="BB Inferior", line=dict(color="rgba(150,150,150,0.5)", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(150,150,150,0.05)",
                showlegend=False,
            ),
            row=1, col=1,
        )

    colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors, opacity=0.7),
        row=2, col=1,
    )

    if "RSI" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#ff7043", width=1.5)),
            row=3, col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=1, row=3, col=1)

    fig.update_layout(
        title=f"Análise Técnica — {name}",
        template="plotly_dark",
        height=750,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0),
        margin=dict(l=40, r=40, t=80, b=40),
    )

    path = os.path.join(REPORTS_DIR, f"{ticker.replace('.SA','')}_candlestick.html")
    fig.write_html(path)
    return path
