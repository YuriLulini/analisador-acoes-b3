import pandas as pd
import numpy as np


def add_sma(df: pd.DataFrame, window: int) -> pd.Series:
    return df["Close"].rolling(window=window).mean()


def add_ema(df: pd.DataFrame, window: int) -> pd.Series:
    return df["Close"].ewm(span=window, adjust=False).mean()


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0):
    sma = df["Close"].rolling(window=window).mean()
    std = df["Close"].rolling(window=window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    return upper, sma, lower


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["SMA20"] = add_sma(df, 20)
    result["SMA50"] = add_sma(df, 50)
    result["EMA9"] = add_ema(df, 9)
    result["RSI"] = add_rsi(df)
    macd, signal, hist = add_macd(df)
    result["MACD"] = macd
    result["MACD_Signal"] = signal
    result["MACD_Hist"] = hist
    bb_upper, bb_mid, bb_lower = add_bollinger_bands(df)
    result["BB_Upper"] = bb_upper
    result["BB_Mid"] = bb_mid
    result["BB_Lower"] = bb_lower
    result["Return_1d"] = df["Close"].pct_change()
    result["Return_5d"] = df["Close"].pct_change(5)
    result["Return_21d"] = df["Close"].pct_change(21)
    result["Vol_Avg20"] = df["Volume"].rolling(20).mean()
    return result


def get_trend_score(df: pd.DataFrame) -> float:
    """Returns 0–100 trend score based on price vs moving averages."""
    if df.empty or len(df) < 50:
        return 50.0

    latest = df.iloc[-1]
    score = 50.0

    if latest["Close"] > latest.get("SMA20", latest["Close"]):
        score += 10
    else:
        score -= 10

    if latest["Close"] > latest.get("SMA50", latest["Close"]):
        score += 15
    else:
        score -= 15

    if latest.get("SMA20", 0) > latest.get("SMA50", 0):
        score += 10
    else:
        score -= 10

    ret_21d = latest.get("Return_21d", 0) or 0
    score += min(max(ret_21d * 100, -15), 15)

    return float(min(max(score, 0), 100))


def get_rsi_score(df: pd.DataFrame) -> float:
    """Returns 0–100 RSI score. High score = good entry point (oversold)."""
    if df.empty or "RSI" not in df.columns:
        return 50.0
    rsi = df["RSI"].dropna()
    if rsi.empty:
        return 50.0
    last_rsi = rsi.iloc[-1]
    if last_rsi <= 30:
        return 90.0
    elif last_rsi <= 40:
        return 70.0
    elif last_rsi <= 55:
        return 55.0
    elif last_rsi <= 70:
        return 40.0
    else:
        return 20.0
