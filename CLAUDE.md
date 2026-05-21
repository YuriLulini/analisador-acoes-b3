# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
cd stock_analyzer
python3 main.py
```

Install dependencies (Python 3.9+):

```bash
pip3 install -r requirements.txt
```

Quick programmatic test without the interactive menu:

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from data.fetcher import fetch_price_history, fetch_fundamentals
from analysis.scorer import compute_score

df = fetch_price_history('PETR4.SA', period='3mo')
fund = fetch_fundamentals('PETR4.SA')
result = compute_score(df, fund)
print(result['score'], result['recommendation'])
"
```

## Architecture

The pipeline runs in this fixed order:

```
data/b3_stocks.py   →   data/fetcher.py   →   analysis/   →   charts/   →   reports/
(registry)              (price + fund)         (scoring)       (plotly)      (HTML)
```

**`data/b3_stocks.py`** — Fetches the full B3 asset list (~1,500 tickers) from `https://brapi.dev/api/available` and caches it to `data/cache/b3_stocks.json` (TTL 7 days). Categorizes assets into ON, PN, FII, BDR, UNT/ETF. `FEATURED` dict maps ticker_sa → display name for ~40 known companies; all others fall back to the raw ticker string. The `search_stocks()` function does case-insensitive substring matching on both ticker and name.

**`data/fetcher.py`** — Two-layer cache: SQLite (`data/cache/stocks.db`) stores OHLCV price rows per ticker/date; `meta_cache` table records last fetch timestamp. Cache is considered fresh for 6 hours. `fetch_fundamentals()` is not cached — it calls yfinance on every run. **Important:** yfinance's `dividendYield` field is already a percentage (e.g. `8.69` = 8.69%), so the code uses `trailingAnnualDividendYield` (decimal) instead.

**`analysis/technical.py`** — All indicators (RSI-14, MACD 12/26/9, SMA20, SMA50, EMA9, Bollinger 20/2σ) are computed manually with pandas/numpy — `pandas-ta` is listed in requirements but not used. `compute_indicators()` returns an enriched DataFrame. `get_trend_score()` and `get_rsi_score()` each return 0–100.

**`analysis/fundamental.py`** — `get_fundamentals_score()` and `get_dividend_score()` each return 0–100 based on thresholds defined inline. `format_fundamentals()` is a display helper only; it is not used in the scoring pipeline.

**`analysis/scorer.py`** — Combines the four sub-scores using weights from `config.SCORE_WEIGHTS` (default: trend 30%, RSI 20%, fundamentals 30%, dividend 20%). Thresholds in `config.RECOMMENDATION_THRESHOLDS` determine COMPRAR (≥65) / AGUARDAR (≥40) / VENDER (<40). The returned dict includes the enriched DataFrame under key `"df"` — downstream chart functions read it from there.

**`charts/`** — `price_charts.plot_candlestick()` writes one HTML file per ticker. `comparison.py` writes three shared HTML files (`comparativo_retorno.html`, `correlacao.html`, `radar_scores.html`). All chart functions accept a `stock_names: dict` parameter (`{ticker_sa: display_name}`) — pass the output of `data.b3_stocks.get_stock_dict()`.

**`reports/generator.py`** — Generates a single dark-theme HTML dashboard linking to all chart files via relative paths. Accepts `stock_names` as an optional parameter.

**`main.py`** — Interactive CLI entry point. Loads the stock registry once at startup into the module-level `ALL_STOCKS` list. `BATCH_SIZE = 10` in config limits tickers per run to avoid yfinance rate limiting.

## Key configuration (config.py)

| Constant | Purpose |
|---|---|
| `SCORE_WEIGHTS` | Relative weight of each scoring component |
| `RECOMMENDATION_THRESHOLDS` | Score cutoffs for COMPRAR / AGUARDAR / VENDER |
| `IBOVESPA_PRESET` | 20-ticker preset shown in menu option [1] |
| `BATCH_SIZE` | Hard cap on tickers per analysis run |

## Cache locations

| Path | Contents | TTL |
|---|---|---|
| `data/cache/stocks.db` | SQLite — OHLCV price history per ticker | 6 hours |
| `data/cache/b3_stocks.json` | Full B3 asset list from BRAPI | 7 days |
| `reports/output/` | Generated HTML charts and report | no TTL |

To force a fresh download, pass `force_refresh=True` to `fetch_price_history()` / `fetch_all_stocks()`, or `force_refresh=True` to `fetch_b3_stock_list()`.

## GitHub repository

**URL:** https://github.com/YuriLulini/analisador-acoes-b3

**Auto-push hook:** every time Claude Code edits or writes a file, the hook `.claude/auto_push.sh` runs automatically and pushes the changes to `main`. This is configured in `.claude/settings.json` via `PostToolUse` on `Edit|Write` events.

The `gh` CLI binary lives at `~/.local/bin/gh` (installed without sudo). If it stops working, reinstall:

```bash
curl -fsSL "https://github.com/cli/cli/releases/download/v2.92.0/gh_2.92.0_macOS_arm64.zip" -o /tmp/gh.zip
cd /tmp && unzip -q gh.zip
cp /tmp/gh_2.92.0_macOS_arm64/bin/gh ~/.local/bin/gh
chmod +x ~/.local/bin/gh
~/.local/bin/gh auth login --web
```

**Manual push** (if needed):

```bash
cd stock_analyzer
git add -A && git commit -m "mensagem" && git push origin main
```

**Check push history:**

```bash
cd stock_analyzer && git log --oneline -10
```

`.claude/auto_push.sh` silently skips the push if there are no staged changes, so it is safe to run at any time.
