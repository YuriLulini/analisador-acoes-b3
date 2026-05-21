import sys
import os
import webbrowser
import time

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich.text import Text
from rich import box

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import IBOVESPA_PRESET, BATCH_SIZE
from data.b3_stocks import fetch_b3_stock_list, search_stocks, get_categories, get_stock_dict, FEATURED
from data.fetcher import fetch_all_stocks, fetch_fundamentals
from analysis.scorer import compute_score, rank_stocks
from charts.price_charts import plot_candlestick
from charts.comparison import plot_normalized_returns, plot_correlation_heatmap, plot_score_radar
from reports.generator import generate_html_report

console = Console()

ALL_STOCKS = []


def load_stock_registry(force: bool = False):
    global ALL_STOCKS
    ALL_STOCKS = fetch_b3_stock_list(force_refresh=force)


def print_banner():
    total = len(ALL_STOCKS)
    console.print(Panel.fit(
        f"[bold cyan]Analisador de Ações B3 — 2026[/bold cyan]\n"
        f"[dim]{total} ativos cadastrados · yfinance + BRAPI[/dim]",
        border_style="cyan",
        padding=(1, 4),
    ))


def menu_browse_by_category() -> list:
    categories = get_categories(ALL_STOCKS)
    console.print("\n[bold]Categorias disponíveis:[/bold]")
    for i, cat in enumerate(categories, 1):
        count = sum(1 for s in ALL_STOCKS if s["category"] == cat)
        console.print(f"  [{i}] {cat:<12} ({count} ativos)")

    choice = Prompt.ask("\nCategoria (número ou Enter para todas)", default="")
    if choice.isdigit() and 1 <= int(choice) <= len(categories):
        selected_cat = categories[int(choice) - 1]
        filtered = [s for s in ALL_STOCKS if s["category"] == selected_cat]
    else:
        filtered = ALL_STOCKS

    console.print(f"\n[dim]{len(filtered)} ativos na categoria. Digite parte do ticker para filtrar.[/dim]")
    query = Prompt.ask("Filtro (Enter para listar todos)", default="")
    if query.strip():
        filtered = search_stocks(query, filtered)

    return _pick_from_list(filtered)


def menu_search() -> list:
    query = Prompt.ask("\nDigite ticker ou nome da empresa (ex: PETR, Petrobras, VALE)")
    results = search_stocks(query, ALL_STOCKS)
    if not results:
        console.print("[yellow]Nenhum ativo encontrado.[/yellow]")
        return []
    return _pick_from_list(results)


def _pick_from_list(stocks_list: list) -> list:
    if not stocks_list:
        return []

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Ticker", width=10)
    table.add_column("Nome", width=28)
    table.add_column("Tipo", width=8)
    table.add_column("Setor", width=20)

    display = stocks_list[:60]
    for i, s in enumerate(display, 1):
        table.add_row(str(i), s["ticker"], s["name"], s["category"], s["sector"])

    console.print(table)
    if len(stocks_list) > 60:
        console.print(f"[dim]... e mais {len(stocks_list) - 60} ativos. Refine a busca para ver todos.[/dim]")

    choice = Prompt.ask(
        "\nSelecione números separados por vírgula (ex: 1,3,5) ou 'todos' para selecionar até 10",
        default="1"
    )

    if choice.strip().lower() == "todos":
        return [s["ticker_sa"] for s in display[:BATCH_SIZE]]

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(display):
                selected.append(display[idx]["ticker_sa"])
    return selected


def menu_ibovespa_preset() -> list:
    console.print(f"\n[bold]Preset Ibovespa ({len(IBOVESPA_PRESET)} principais ações):[/bold]")
    table = Table(box=box.SIMPLE)
    table.add_column("#", style="dim", width=3)
    table.add_column("Ticker")
    table.add_column("Nome")
    lookup = {s["ticker_sa"]: s["name"] for s in ALL_STOCKS}
    for i, t in enumerate(IBOVESPA_PRESET, 1):
        table.add_row(str(i), t.replace(".SA", ""), lookup.get(t, t))
    console.print(table)

    choice = Prompt.ask(
        f"\nSelecione (números, 'todos' para todos os {len(IBOVESPA_PRESET)}, ou Enter para primeiros 10)",
        default="todos"
    )

    if choice.strip().lower() == "todos":
        return IBOVESPA_PRESET
    if not choice.strip():
        return IBOVESPA_PRESET[:BATCH_SIZE]

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(IBOVESPA_PRESET):
                selected.append(IBOVESPA_PRESET[idx])
    return selected or IBOVESPA_PRESET[:BATCH_SIZE]


def menu_custom_input() -> list:
    console.print("\n[dim]Digite tickers separados por vírgula (sem .SA). Ex: PETR4,ITUB4,VALE3[/dim]")
    raw = Prompt.ask("Tickers")
    tickers = []
    for t in raw.upper().split(","):
        t = t.strip()
        if t:
            tickers.append(f"{t}.SA")
    return tickers


def select_period() -> str:
    console.print("\n[bold]Período de análise:[/bold]")
    options = {"1": "3mo", "2": "6mo", "3": "1y", "4": "2y"}
    labels = {"1": "3 meses", "2": "6 meses", "3": "1 ano", "4": "2 anos"}
    for k, v in labels.items():
        console.print(f"  [{k}] {v}")
    return options.get(Prompt.ask("Escolha", default="3"), "1y")


def run_analysis(tickers: list, period: str, force_refresh: bool = False):
    if not tickers:
        console.print("[red]Nenhum ativo selecionado.[/red]")
        return

    if len(tickers) > BATCH_SIZE:
        console.print(f"[yellow]Limitando a {BATCH_SIZE} ativos por rodada para evitar rate limiting.[/yellow]")
        tickers = tickers[:BATCH_SIZE]

    stock_names = get_stock_dict(tickers, ALL_STOCKS)

    console.print(f"\n[bold cyan]Coletando dados de {len(tickers)} ativo(s)...[/bold cyan]")
    all_data = fetch_all_stocks(tickers, period=period, force_refresh=force_refresh)

    if not all_data:
        console.print("[red]Nenhum dado retornado. Verifique os tickers e sua conexão.[/red]")
        return

    console.print("\n[bold cyan]Calculando scores e recomendações...[/bold cyan]")
    scores = {}
    fundamentals = {}

    for ticker in tickers:
        if ticker not in all_data:
            console.print(f"  [yellow]Sem dados: {ticker}[/yellow]")
            continue
        fund = fetch_fundamentals(ticker)
        fundamentals[ticker] = fund
        scores[ticker] = compute_score(all_data[ticker], fund)

    if not scores:
        console.print("[red]Não foi possível calcular scores.[/red]")
        return

    _print_summary_table(scores, fundamentals, stock_names)

    console.print("\n[bold cyan]Gerando gráficos...[/bold cyan]")
    chart_paths = {}
    for ticker, data in scores.items():
        name = stock_names.get(ticker, ticker)
        path = plot_candlestick(data["df"], ticker, name)
        chart_paths[ticker] = path
        console.print(f"  [green]✓[/green] {ticker.replace('.SA','')}")

    if len(all_data) > 1:
        chart_paths["normalized_returns"] = plot_normalized_returns(all_data, stock_names)
        chart_paths["correlation"] = plot_correlation_heatmap(all_data, stock_names)
        chart_paths["radar"] = plot_score_radar(scores, stock_names)
        console.print("  [green]✓[/green] Gráficos comparativos")

    console.print("\n[bold cyan]Gerando relatório HTML...[/bold cyan]")
    report_path = generate_html_report(scores, fundamentals, chart_paths, stock_names)
    console.print(f"[bold green]Relatório:[/bold green] {report_path}")

    if Confirm.ask("\nAbrir relatório no navegador?", default=True):
        webbrowser.open(f"file://{report_path}")

    _print_recommendations(scores, stock_names)


def _print_summary_table(scores: dict, fundamentals: dict, stock_names: dict):
    ranked = rank_stocks(scores)
    rec_colors = {"COMPRAR": "green", "AGUARDAR": "yellow", "VENDER": "red"}

    table = Table(
        title="\nRanking de Recomendações",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Ação", style="bold")
    table.add_column("Score", justify="center", width=8)
    table.add_column("Recomendação", justify="center", width=14)
    table.add_column("P/L", justify="right", width=7)
    table.add_column("P/VP", justify="right", width=7)
    table.add_column("DY", justify="right", width=8)
    table.add_column("RSI", justify="right", width=6)

    for i, (ticker, data) in enumerate(ranked, 1):
        name = stock_names.get(ticker, ticker).split()[0]
        rec = data["recommendation"]
        color = rec_colors.get(rec, "white")
        fund = fundamentals.get(ticker, {})
        pe = fund.get("pe_ratio")
        pb = fund.get("pb_ratio")
        dy = fund.get("dividend_yield")

        rsi_raw = None
        df = data.get("df")
        if df is not None and "RSI" in df.columns and not df["RSI"].dropna().empty:
            rsi_raw = df["RSI"].dropna().iloc[-1]

        table.add_row(
            str(i),
            f"{name}\n[dim]{ticker.replace('.SA','')}[/dim]",
            f"[bold {color}]{data['score']:.1f}[/bold {color}]",
            f"[bold {color}]{rec}[/bold {color}]",
            f"{pe:.1f}" if pe else "N/D",
            f"{pb:.2f}" if pb else "N/D",
            f"{dy*100:.1f}%" if dy else "N/D",
            f"{rsi_raw:.0f}" if rsi_raw else "N/D",
        )

    console.print(table)


def _print_recommendations(scores: dict, stock_names: dict):
    ranked = rank_stocks(scores)
    console.print("\n[bold]Justificativas:[/bold]")
    for ticker, data in ranked:
        name = stock_names.get(ticker, ticker)
        rec = data["recommendation"]
        color = {"COMPRAR": "green", "AGUARDAR": "yellow", "VENDER": "red"}.get(rec, "white")
        console.print(f"\n  [bold {color}]{name} ({ticker.replace('.SA','')}) — {rec}[/bold {color}]")
        for note in data.get("justifications", []):
            console.print(f"    [dim]•[/dim] {note}")


def main_menu():
    load_stock_registry()
    print_banner()

    while True:
        console.print("\n[bold]Menu Principal:[/bold]")
        console.print("  [1] Preset Ibovespa (top 20 ações)")
        console.print("  [2] Buscar por ticker ou nome")
        console.print("  [3] Navegar por categoria (ON, PN, FII, BDR...)")
        console.print("  [4] Digitar tickers manualmente")
        console.print("  [5] Atualizar lista de ativos da B3")
        console.print("  [6] Sair")

        choice = Prompt.ask("\nEscolha", default="1")

        if choice == "1":
            tickers = menu_ibovespa_preset()
        elif choice == "2":
            tickers = menu_search()
        elif choice == "3":
            tickers = menu_browse_by_category()
        elif choice == "4":
            tickers = menu_custom_input()
        elif choice == "5":
            load_stock_registry(force=True)
            console.print(f"[green]Lista atualizada: {len(ALL_STOCKS)} ativos.[/green]")
            continue
        elif choice == "6":
            console.print("[dim]Encerrando...[/dim]")
            break
        else:
            console.print("[red]Opção inválida.[/red]")
            continue

        if not tickers:
            continue

        period = select_period()
        force = Confirm.ask("Forçar atualização dos dados (ignorar cache)?", default=False)
        run_analysis(tickers, period, force_refresh=force)


if __name__ == "__main__":
    main_menu()
