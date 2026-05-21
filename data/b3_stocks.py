import os
import json
import re
import requests
from datetime import datetime, timedelta
from rich.console import Console

from config import DATA_DIR

console = Console()
CACHE_FILE = os.path.join(DATA_DIR, "b3_stocks.json")
CACHE_TTL_DAYS = 7

CATEGORY_RULES = [
    ("BDR", re.compile(r"\d{2}$")),
    ("FII", re.compile(r"11$")),
    ("ETF", re.compile(r"1[12]$")),
    ("ON", re.compile(r"3$")),
    ("PN", re.compile(r"4$")),
    ("PNB", re.compile(r"5$")),
    ("PNC", re.compile(r"6$")),
    ("UNT", re.compile(r"11$")),
]

BDR_PATTERN = re.compile(r"[A-Z]{4}3[2-5]$")
FII_PATTERN = re.compile(r"[A-Z]{4}11$")

FEATURED = {
    "PETR4.SA": "Petrobras PN",
    "PETR3.SA": "Petrobras ON",
    "ITUB4.SA": "Itaú Unibanco PN",
    "ITUB3.SA": "Itaú Unibanco ON",
    "VALE3.SA": "Vale ON",
    "BBDC4.SA": "Bradesco PN",
    "BBAS3.SA": "Banco do Brasil ON",
    "WEGE3.SA": "WEG ON",
    "ABEV3.SA": "Ambev ON",
    "MGLU3.SA": "Magazine Luiza ON",
    "LREN3.SA": "Lojas Renner ON",
    "RENT3.SA": "Localiza ON",
    "PRIO3.SA": "PetroRio ON",
    "RDOR3.SA": "Rede D'Or ON",
    "HAPV3.SA": "Hapvida ON",
    "TOTS3.SA": "Totvs ON",
    "BPAC11.SA": "BTG Pactual UNT",
    "CSAN3.SA": "Cosan ON",
    "GGBR4.SA": "Gerdau PN",
    "CSNA3.SA": "CSN ON",
    "CMIN3.SA": "CSN Mineração ON",
    "USIM5.SA": "Usiminas PNA",
    "BBSE3.SA": "BB Seguridade ON",
    "ITSA4.SA": "Itaúsa PN",
    "RAIL3.SA": "Rumo ON",
    "B3SA3.SA": "B3 ON",
    "SBSP3.SA": "Sabesp ON",
    "CMIG4.SA": "Cemig PN",
    "ELET3.SA": "Eletrobras ON",
    "ELET6.SA": "Eletrobras PNB",
    "SUZB3.SA": "Suzano ON",
    "KLBN11.SA": "Klabin UNT",
    "EQTL3.SA": "Equatorial ON",
    "EMBR3.SA": "Embraer ON",
    "AZUL4.SA": "Azul PN",
    "GOLL4.SA": "Gol PN",
    "CPLE3.SA": "Copel ON",
    "SANB11.SA": "Santander UNT",
    "MRVE3.SA": "MRV ON",
    "CYRE3.SA": "Cyrela ON",
    "VIVT3.SA": "Vivo ON",
    "TIMS3.SA": "TIM ON",
}

SECTOR_MAP = {
    "PETR": "Petróleo e Gás",
    "ITUB": "Bancos",
    "ITSA": "Bancos",
    "BBDC": "Bancos",
    "BBAS": "Bancos",
    "SANB": "Bancos",
    "BPAC": "Bancos",
    "VALE": "Mineração",
    "CSNA": "Siderurgia",
    "CMIN": "Mineração",
    "GGBR": "Siderurgia",
    "USIM": "Siderurgia",
    "ABEV": "Bebidas",
    "WEGE": "Máquinas",
    "EMBR": "Aviação",
    "AZUL": "Aviação",
    "GOLL": "Aviação",
    "MGLU": "Varejo",
    "LREN": "Varejo",
    "RENT": "Locação",
    "VAMO": "Locação",
    "RAIL": "Logística",
    "ELET": "Energia",
    "CMIG": "Energia",
    "EQTL": "Energia",
    "CPLE": "Energia",
    "SBSP": "Saneamento",
    "CSAN": "Energia",
    "SUZB": "Papel e Celulose",
    "KLBN": "Papel e Celulose",
    "TOTS": "Tecnologia",
    "B3SA": "Bolsa de Valores",
    "PRIO": "Petróleo e Gás",
    "BRAV": "Petróleo e Gás",
    "RDOR": "Saúde",
    "HAPV": "Saúde",
    "BBSE": "Seguros",
    "VIVT": "Telecom",
    "TIMS": "Telecom",
    "MRVE": "Construção Civil",
    "CYRE": "Construção Civil",
}


def _categorize(ticker: str) -> str:
    if BDR_PATTERN.match(ticker):
        return "BDR"
    if FII_PATTERN.match(ticker):
        return "FII"
    if ticker.endswith("11"):
        return "UNT/ETF"
    if ticker.endswith("3"):
        return "ON"
    if ticker.endswith("4"):
        return "PN"
    if ticker.endswith("5"):
        return "PNA"
    if ticker.endswith("6"):
        return "PNB"
    return "Outro"


def _get_sector(ticker: str) -> str:
    prefix = ticker[:4]
    return SECTOR_MAP.get(prefix, "")


def _cache_fresh() -> bool:
    if not os.path.exists(CACHE_FILE):
        return False
    mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
    return datetime.now() - mtime < timedelta(days=CACHE_TTL_DAYS)


def _load_cache() -> list:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_cache(stocks: list):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)


def fetch_b3_stock_list(force_refresh: bool = False) -> list:
    """Returns list of dicts: {ticker, ticker_sa, name, category, sector}"""
    if not force_refresh and _cache_fresh():
        return _load_cache()

    console.print("[cyan]Baixando lista completa da B3 via BRAPI...[/cyan]")
    try:
        r = requests.get(
            "https://brapi.dev/api/available",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        raw_tickers = r.json().get("stocks", [])
    except Exception as e:
        console.print(f"[yellow]Aviso: falha ao buscar lista ({e}). Usando cache ou lista base.[/yellow]")
        if os.path.exists(CACHE_FILE):
            return _load_cache()
        raw_tickers = list(t.replace(".SA", "") for t in FEATURED.keys())

    stocks = []
    for t in raw_tickers:
        ticker_sa = f"{t}.SA"
        category = _categorize(t)
        name = FEATURED.get(ticker_sa, t)
        sector = _get_sector(t)
        stocks.append({
            "ticker": t,
            "ticker_sa": ticker_sa,
            "name": name,
            "category": category,
            "sector": sector,
        })

    stocks.sort(key=lambda x: x["ticker"])
    _save_cache(stocks)
    console.print(f"[green]Lista atualizada: {len(stocks)} ativos cadastrados.[/green]")
    return stocks


def search_stocks(query: str, stocks: list, category_filter: str = None) -> list:
    """Search stocks by ticker or name, optionally filtered by category."""
    q = query.upper().strip()
    results = []
    for s in stocks:
        if category_filter and s["category"] != category_filter:
            continue
        if q in s["ticker"] or q in s["name"].upper():
            results.append(s)
    return results


def get_categories(stocks: list) -> list:
    return sorted(set(s["category"] for s in stocks))


def get_stock_dict(tickers_sa: list, stocks: list) -> dict:
    """Returns {ticker_sa: name} for a list of tickers."""
    lookup = {s["ticker_sa"]: s["name"] for s in stocks}
    return {t: lookup.get(t, t.replace(".SA", "")) for t in tickers_sa}
