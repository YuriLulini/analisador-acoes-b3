from config import SCORE_WEIGHTS, RECOMMENDATION_THRESHOLDS
from analysis.technical import get_trend_score, get_rsi_score, compute_indicators
from analysis.fundamental import get_fundamentals_score, get_dividend_score


def compute_score(df_raw, fundamentals: dict) -> dict:
    """Computes weighted score and returns recommendation details."""
    df = compute_indicators(df_raw)

    trend_score = get_trend_score(df)
    rsi_score = get_rsi_score(df)
    fund_score = get_fundamentals_score(fundamentals)
    div_score = get_dividend_score(fundamentals)

    total = (
        trend_score * SCORE_WEIGHTS["trend"]
        + rsi_score * SCORE_WEIGHTS["rsi"]
        + fund_score * SCORE_WEIGHTS["fundamentals"]
        + div_score * SCORE_WEIGHTS["dividend_yield"]
    )

    if total >= RECOMMENDATION_THRESHOLDS["buy"]:
        recommendation = "COMPRAR"
        color = "green"
    elif total >= RECOMMENDATION_THRESHOLDS["wait"]:
        recommendation = "AGUARDAR"
        color = "yellow"
    else:
        recommendation = "VENDER"
        color = "red"

    latest = df.iloc[-1] if not df.empty else {}
    rsi_val = latest.get("RSI") if hasattr(latest, "get") else None

    justifications = _build_justification(
        trend_score, rsi_score, fund_score, div_score,
        fundamentals, rsi_val
    )

    return {
        "score": round(total, 1),
        "recommendation": recommendation,
        "color": color,
        "components": {
            "Tendência": round(trend_score, 1),
            "RSI": round(rsi_score, 1),
            "Fundamentos": round(fund_score, 1),
            "Dividendos": round(div_score, 1),
        },
        "justifications": justifications,
        "df": df,
    }


def _build_justification(trend, rsi, fund, div, info, rsi_val) -> list:
    notes = []

    if trend >= 70:
        notes.append("Tendencia de alta forte (preco acima das medias moveis)")
    elif trend >= 50:
        notes.append("Tendencia levemente positiva")
    else:
        notes.append("Tendencia de baixa (preco abaixo das medias moveis)")

    if rsi_val is not None:
        if rsi_val <= 30:
            notes.append(f"RSI sobrevendido ({rsi_val:.0f}) - possivel ponto de entrada")
        elif rsi_val >= 70:
            notes.append(f"RSI sobrecomprado ({rsi_val:.0f}) - cautela")
        else:
            notes.append(f"RSI neutro ({rsi_val:.0f})")

    pe = info.get("pe_ratio")
    if pe is not None and pe > 0:
        if pe < 10:
            notes.append(f"P/L baixo ({pe:.1f}) - acao potencialmente subavaliada")
        elif pe > 30:
            notes.append(f"P/L elevado ({pe:.1f}) - precificacao exigente")

    dy = info.get("dividend_yield")
    if dy is not None:
        dy_pct = dy * 100
        if dy_pct >= 6:
            notes.append(f"Dividend yield atrativo ({dy_pct:.1f}%)")
        elif dy_pct < 1:
            notes.append("Baixo pagamento de dividendos")

    roe = info.get("roe")
    if roe is not None and roe > 0.20:
        notes.append(f"ROE elevado ({roe*100:.1f}%) - empresa lucrativa")

    return notes


def rank_stocks(scores: dict) -> list:
    """Returns list of tickers sorted by score descending."""
    return sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
