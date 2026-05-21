import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "cache")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "output")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

STOCKS = {}  # populated dynamically from b3_stocks module

IBOVESPA_PRESET = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA",
    "WEGE3.SA", "ABEV3.SA", "B3SA3.SA", "GGBR4.SA", "RENT3.SA",
    "SUZB3.SA", "EQTL3.SA", "RAIL3.SA", "ITSA4.SA", "LREN3.SA",
    "CSAN3.SA", "PRIO3.SA", "TOTS3.SA", "BPAC11.SA", "EMBR3.SA",
]

BATCH_SIZE = 10  # max tickers per analysis run to avoid yfinance rate limiting

DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"

SCORE_WEIGHTS = {
    "trend": 0.30,
    "rsi": 0.20,
    "fundamentals": 0.30,
    "dividend_yield": 0.20,
}

RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

RECOMMENDATION_THRESHOLDS = {
    "buy": 65,
    "wait": 40,
}
