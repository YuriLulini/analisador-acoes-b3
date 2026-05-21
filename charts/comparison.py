import os
import plotly.graph_objects as go
import pandas as pd

from config import REPORTS_DIR

_COLORS = ["#26a69a", "#ffa726", "#42a5f5", "#ab47bc", "#ef5350", "#66bb6a",
           "#ff7043", "#29b6f6", "#d4e157", "#ec407a", "#78909c", "#26c6da"]
_PALETTE = [
    ("#26a69a", "rgba(38,166,154,0.15)"),
    ("#ffa726", "rgba(255,167,38,0.15)"),
    ("#42a5f5", "rgba(66,165,245,0.15)"),
    ("#ab47bc", "rgba(171,71,188,0.15)"),
    ("#ef5350", "rgba(239,83,80,0.15)"),
    ("#66bb6a", "rgba(102,187,106,0.15)"),
    ("#ff7043", "rgba(255,112,67,0.15)"),
    ("#29b6f6", "rgba(41,182,246,0.15)"),
    ("#d4e157", "rgba(212,225,87,0.15)"),
    ("#ec407a", "rgba(236,64,122,0.15)"),
]


def _short_name(ticker: str, stock_names: dict) -> str:
    return stock_names.get(ticker, ticker.replace(".SA", "")).split()[0]


def plot_normalized_returns(all_data: dict, stock_names: dict = None) -> str:
    stock_names = stock_names or {}
    fig = go.Figure()

    for i, (ticker, df) in enumerate(all_data.items()):
        if df.empty:
            continue
        name = _short_name(ticker, stock_names)
        normalized = (df["Close"] / df["Close"].iloc[0] - 1) * 100
        color = _COLORS[i % len(_COLORS)]
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=normalized,
                name=f"{name} ({ticker.replace('.SA','')})",
                line=dict(color=color, width=2),
                hovertemplate="%{y:.2f}%<extra></extra>",
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    fig.update_layout(
        title="Retorno Acumulado Comparativo (%)",
        template="plotly_dark",
        height=500,
        xaxis_title="Data",
        yaxis_title="Retorno (%)",
        legend=dict(orientation="h", y=-0.15),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=80, b=80),
    )

    path = os.path.join(REPORTS_DIR, "comparativo_retorno.html")
    fig.write_html(path)
    return path


def plot_correlation_heatmap(all_data: dict, stock_names: dict = None) -> str:
    stock_names = stock_names or {}
    closes = {}
    for ticker, df in all_data.items():
        if not df.empty:
            label = f"{_short_name(ticker, stock_names)}\n({ticker.replace('.SA','')})"
            closes[label] = df["Close"]

    combined = pd.DataFrame(closes).dropna()
    if combined.shape[1] < 2:
        return ""

    corr = combined.pct_change().corr()
    font_size = max(8, 14 - len(corr))

    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdYlGn",
            zmin=-1,
            zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in corr.values],
            texttemplate="%{text}",
            textfont={"size": font_size},
        )
    )

    height = max(450, len(corr) * 40 + 100)
    fig.update_layout(
        title="Correlação entre Retornos Diários",
        template="plotly_dark",
        height=height,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    path = os.path.join(REPORTS_DIR, "correlacao.html")
    fig.write_html(path)
    return path


def plot_score_radar(scores: dict, stock_names: dict = None) -> str:
    stock_names = stock_names or {}
    categories = ["Tendência", "RSI", "Fundamentos", "Dividendos"]
    fig = go.Figure()

    for i, (ticker, data) in enumerate(scores.items()):
        name = _short_name(ticker, stock_names)
        values = [data["components"].get(c, 50) for c in categories]
        values_closed = values + [values[0]]
        cats_closed = categories + [categories[0]]
        line_color, fill_color = _PALETTE[i % len(_PALETTE)]

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=cats_closed,
                fill="toself",
                name=f"{name} ({ticker.replace('.SA','')})",
                line_color=line_color,
                fillcolor=fill_color,
                opacity=0.85,
            )
        )

    fig.update_layout(
        title="Radar de Score por Critério",
        template="plotly_dark",
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=500,
        legend=dict(orientation="h", y=-0.1),
        margin=dict(l=40, r=40, t=80, b=80),
    )

    path = os.path.join(REPORTS_DIR, "radar_scores.html")
    fig.write_html(path)
    return path
