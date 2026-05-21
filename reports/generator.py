import os
from datetime import datetime
from config import REPORTS_DIR


def _recommendation_badge(rec: str) -> str:
    colors = {"COMPRAR": "#26a69a", "AGUARDAR": "#ffa726", "VENDER": "#ef5350"}
    bg = colors.get(rec, "#666")
    return f'<span style="background:{bg};color:white;padding:4px 12px;border-radius:12px;font-weight:bold;font-size:0.9em;">{rec}</span>'


def _score_bar(score: float) -> str:
    pct = min(max(score, 0), 100)
    if pct >= 65:
        color = "#26a69a"
    elif pct >= 40:
        color = "#ffa726"
    else:
        color = "#ef5350"
    return (
        f'<div style="background:#333;border-radius:6px;height:10px;width:100%;">'
        f'<div style="background:{color};width:{pct}%;height:100%;border-radius:6px;"></div></div>'
        f'<small style="color:{color};font-weight:bold;">{pct:.1f}/100</small>'
    )


def generate_html_report(scores: dict, fundamentals: dict, chart_paths: dict, stock_names: dict = None) -> str:
    stock_names = stock_names or {}
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    cards_html = ""
    for ticker, data in ranked:
        name = stock_names.get(ticker, ticker.replace(".SA", ""))
        fund = fundamentals.get(ticker, {})
        rec = data["recommendation"]
        score = data["score"]
        comps = data["components"]
        notes = data.get("justifications", [])

        pe = fund.get("pe_ratio")
        pb = fund.get("pb_ratio")
        dy = fund.get("dividend_yield")
        roe = fund.get("roe")

        pe_str = f"{pe:.1f}" if pe else "N/D"
        pb_str = f"{pb:.2f}" if pb else "N/D"
        dy_str = f"{dy*100:.1f}%" if dy else "N/D"
        roe_str = f"{roe*100:.1f}%" if roe else "N/D"

        notes_html = "".join(f"<li>{n}</li>" for n in notes)

        comp_rows = "".join(
            f"<tr><td>{k}</td><td style='text-align:right;color:#aaa;'>{v:.0f}/100</td></tr>"
            for k, v in comps.items()
        )

        chart_link = chart_paths.get(ticker, "")
        chart_btn = (
            f'<a href="{chart_link}" target="_blank" style="display:inline-block;margin-top:10px;'
            f'padding:6px 14px;background:#1e88e5;color:white;border-radius:8px;text-decoration:none;font-size:0.85em;">'
            f'Ver Gráfico Técnico</a>'
        ) if chart_link else ""

        cards_html += f"""
        <div style="background:#1e1e2e;border-radius:12px;padding:24px;margin-bottom:24px;border:1px solid #333;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
            <div>
              <h2 style="margin:0;color:#e0e0e0;">{name}</h2>
              <span style="color:#888;font-size:0.9em;">{ticker}</span>
            </div>
            <div style="text-align:right;">
              {_recommendation_badge(rec)}
              <div style="margin-top:8px;min-width:160px;">
                {_score_bar(score)}
              </div>
            </div>
          </div>

          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-top:20px;">
            <div style="background:#252535;border-radius:8px;padding:16px;">
              <p style="color:#888;margin:0 0 6px;font-size:0.8em;text-transform:uppercase;">Fundamentos</p>
              <table style="width:100%;color:#ccc;font-size:0.9em;">
                <tr><td>P/L</td><td style="text-align:right;">{pe_str}</td></tr>
                <tr><td>P/VP</td><td style="text-align:right;">{pb_str}</td></tr>
                <tr><td>Div. Yield</td><td style="text-align:right;">{dy_str}</td></tr>
                <tr><td>ROE</td><td style="text-align:right;">{roe_str}</td></tr>
              </table>
            </div>
            <div style="background:#252535;border-radius:8px;padding:16px;">
              <p style="color:#888;margin:0 0 6px;font-size:0.8em;text-transform:uppercase;">Componentes do Score</p>
              <table style="width:100%;color:#ccc;font-size:0.9em;">
                {comp_rows}
              </table>
            </div>
            <div style="background:#252535;border-radius:8px;padding:16px;">
              <p style="color:#888;margin:0 0 6px;font-size:0.8em;text-transform:uppercase;">Justificativas</p>
              <ul style="color:#ccc;font-size:0.85em;margin:0;padding-left:18px;">
                {notes_html}
              </ul>
              {chart_btn}
            </div>
          </div>
        </div>
        """

    compare_html = ""
    for key, label in [
        ("normalized_returns", "Retorno Comparativo"),
        ("correlation", "Correlação"),
        ("radar", "Radar de Scores"),
    ]:
        path = chart_paths.get(key, "")
        if path:
            compare_html += (
                f'<a href="{path}" target="_blank" style="display:inline-block;margin:8px;'
                f'padding:10px 20px;background:#37474f;color:white;border-radius:8px;text-decoration:none;">'
                f'{label}</a>'
            )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Análise de Ações B3 — 2026</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 24px; background: #12121f; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }}
    h1 {{ color: #fff; border-bottom: 2px solid #26a69a; padding-bottom: 10px; }}
  </style>
</head>
<body>
  <h1>Análise de Ações B3 — 2026</h1>
  <p style="color:#888;">Gerado em: {now} &nbsp;|&nbsp; Ranking por score total</p>

  <div style="margin-bottom:24px;">
    <strong style="color:#aaa;">Gráficos Comparativos:</strong><br>
    {compare_html}
  </div>

  {cards_html}

  <footer style="margin-top:40px;color:#555;font-size:0.8em;text-align:center;">
    Este relatório é apenas informativo e não constitui recomendação de investimento.
  </footer>
</body>
</html>"""

    path = os.path.join(REPORTS_DIR, "relatorio_acoes_2026.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
