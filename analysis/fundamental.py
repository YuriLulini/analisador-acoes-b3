def get_fundamentals_score(info: dict) -> float:
    """Returns 0–100 score based on fundamental indicators."""
    if not info:
        return 50.0

    score = 50.0

    pe = info.get("pe_ratio")
    if pe is not None:
        if pe < 0:
            score -= 15
        elif pe < 8:
            score += 20
        elif pe < 15:
            score += 15
        elif pe < 25:
            score += 5
        elif pe < 40:
            score -= 5
        else:
            score -= 15

    pb = info.get("pb_ratio")
    if pb is not None:
        if pb < 0:
            score -= 10
        elif pb < 1.0:
            score += 15
        elif pb < 2.0:
            score += 8
        elif pb < 4.0:
            score += 0
        else:
            score -= 10

    roe = info.get("roe")
    if roe is not None:
        if roe > 0.25:
            score += 15
        elif roe > 0.15:
            score += 10
        elif roe > 0.08:
            score += 3
        elif roe > 0:
            score -= 5
        else:
            score -= 15

    margin = info.get("net_margin")
    if margin is not None:
        if margin > 0.20:
            score += 10
        elif margin > 0.10:
            score += 5
        elif margin < 0:
            score -= 10

    dte = info.get("debt_to_equity")
    if dte is not None:
        if dte < 50:
            score += 5
        elif dte > 200:
            score -= 10

    return float(min(max(score, 0), 100))


def get_dividend_score(info: dict) -> float:
    """Returns 0–100 score based on dividend yield."""
    if not info:
        return 50.0

    dy = info.get("dividend_yield")
    if dy is None:
        return 40.0

    dy_pct = dy * 100
    if dy_pct >= 10:
        return 95.0
    elif dy_pct >= 7:
        return 85.0
    elif dy_pct >= 5:
        return 75.0
    elif dy_pct >= 3:
        return 60.0
    elif dy_pct >= 1:
        return 45.0
    else:
        return 30.0


def format_fundamentals(info: dict, name: str) -> dict:
    """Formats fundamental data for display."""
    def pct(v):
        return f"{v * 100:.1f}%" if v is not None else "N/D"

    def fmt(v, decimals=2):
        return f"{v:.{decimals}f}" if v is not None else "N/D"

    def currency(v):
        if v is None:
            return "N/D"
        if v >= 1e12:
            return f"R$ {v/1e12:.2f}T"
        elif v >= 1e9:
            return f"R$ {v/1e9:.2f}B"
        elif v >= 1e6:
            return f"R$ {v/1e6:.2f}M"
        return f"R$ {v:.2f}"

    return {
        "Empresa": name,
        "P/L": fmt(info.get("pe_ratio")),
        "P/VP": fmt(info.get("pb_ratio")),
        "Div. Yield": pct(info.get("dividend_yield")),
        "ROE": pct(info.get("roe")),
        "Margem Líq.": pct(info.get("net_margin")),
        "Market Cap": currency(info.get("market_cap")),
        "Dívida/PL": fmt(info.get("debt_to_equity")),
        "Setor": info.get("sector", "N/D"),
    }
