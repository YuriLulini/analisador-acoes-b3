import os
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from rich.console import Console

from config import DATA_DIR, DEFAULT_PERIOD, DEFAULT_INTERVAL

console = Console()
DB_PATH = os.path.join(DATA_DIR, "stocks.db")


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_cache (
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta_cache (
            ticker TEXT PRIMARY KEY,
            fetched_at TEXT,
            info TEXT
        )
    """)
    conn.commit()
    return conn


def _is_cache_fresh(ticker: str, max_age_hours: int = 6) -> bool:
    conn = _get_connection()
    row = conn.execute(
        "SELECT fetched_at FROM meta_cache WHERE ticker = ?", (ticker,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    fetched_at = datetime.fromisoformat(row[0])
    return datetime.now() - fetched_at < timedelta(hours=max_age_hours)


def _save_prices(ticker: str, df: pd.DataFrame):
    conn = _get_connection()
    for date, row in df.iterrows():
        conn.execute(
            "INSERT OR REPLACE INTO price_cache VALUES (?,?,?,?,?,?,?)",
            (
                ticker,
                str(date.date()),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"]),
            ),
        )
    conn.execute(
        "INSERT OR REPLACE INTO meta_cache (ticker, fetched_at) VALUES (?, ?)",
        (ticker, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def _load_prices_from_cache(ticker: str) -> pd.DataFrame:
    conn = _get_connection()
    df = pd.read_sql(
        "SELECT * FROM price_cache WHERE ticker = ? ORDER BY date",
        conn,
        params=(ticker,),
    )
    conn.close()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.drop(columns=["ticker"], errors="ignore")
    df.columns = ["Open", "High", "Low", "Close", "Volume"]
    return df


def fetch_price_history(
    ticker: str,
    period: str = DEFAULT_PERIOD,
    interval: str = DEFAULT_INTERVAL,
    force_refresh: bool = False,
) -> pd.DataFrame:
    if not force_refresh and _is_cache_fresh(ticker):
        console.print(f"  [dim]Cache hit: {ticker}[/dim]")
        return _load_prices_from_cache(ticker)

    console.print(f"  [cyan]Baixando dados: {ticker}...[/cyan]")
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            console.print(f"  [red]Sem dados para {ticker}[/red]")
            return pd.DataFrame()
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.index = df.index.tz_localize(None)
        _save_prices(ticker, df)
        return df
    except Exception as e:
        console.print(f"  [red]Erro ao buscar {ticker}: {e}[/red]")
        cached = _load_prices_from_cache(ticker)
        return cached


def fetch_fundamentals(ticker: str) -> dict:
    console.print(f"  [cyan]Buscando fundamentos: {ticker}...[/cyan]")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("trailingAnnualDividendYield") or (info.get("dividendYield", 0) / 100 if info.get("dividendYield") else None),
            "roe": info.get("returnOnEquity"),
            "net_margin": info.get("profitMargins"),
            "market_cap": info.get("marketCap"),
            "ebitda": info.get("ebitda"),
            "revenue": info.get("totalRevenue"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "sector": info.get("sector", "N/A"),
        }
    except Exception as e:
        console.print(f"  [red]Erro ao buscar fundamentos de {ticker}: {e}[/red]")
        return {}


def fetch_all_stocks(
    tickers: list,
    period: str = DEFAULT_PERIOD,
    force_refresh: bool = False,
) -> dict:
    result = {}
    for ticker in tickers:
        df = fetch_price_history(ticker, period=period, force_refresh=force_refresh)
        if not df.empty:
            result[ticker] = df
    return result
