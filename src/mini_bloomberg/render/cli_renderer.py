"""
All terminal formatting lives here. No other layer prints anything.
Uses Rich for panels/tables and plotext for ASCII price charts.
"""

import io
import sys
from datetime import datetime
from typing import Optional

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

# Wrap stdout in UTF-8 so Rich can output full Unicode on Windows (GBK system locale).
# errors='replace' means truly unencodable chars become '?' rather than crashing.
_stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
) if hasattr(sys.stdout, "buffer") else sys.stdout

console = Console(file=_stdout, legacy_windows=False)

# ── Bloomberg colour palette ───────────────────────────────────────────────────
ORANGE   = "bright_yellow"
GREEN    = "bright_green"
RED      = "bright_red"
DIM      = "dim white"
HEADER   = "bold bright_white"
SUBHEAD  = "bold yellow"


_CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "HKD": "HK$", "CNY": "¥"}

def _fmt_large(n: Optional[int | float], currency: str = "") -> str:
    """Format large numbers as $3.87T, $391.0B, $97.0M, etc."""
    if n is None:
        return "N/A"
    prefix = _CURRENCY_SYMBOLS.get(currency, f"{currency} " if currency else "")
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    if abs_n >= 1e12:
        return f"{sign}{prefix}{abs_n / 1e12:.2f}T"
    if abs_n >= 1e9:
        return f"{sign}{prefix}{abs_n / 1e9:.1f}B"
    if abs_n >= 1e6:
        return f"{sign}{prefix}{abs_n / 1e6:.1f}M"
    return f"{sign}{prefix}{abs_n:,.0f}"


def _fmt_pct(n: Optional[float]) -> str:
    if n is None:
        return "N/A"
    return f"{n:.2f}%"


def _kv(label: str, value: str, label_width: int = 22) -> Text:
    t = Text()
    t.append(f"{label:<{label_width}}", style=DIM)
    t.append(value, style=GREEN)
    return t


# ─── DES ──────────────────────────────────────────────────────────────────────

def render_des(result: dict) -> None:
    if result["status"] == "error":
        console.print(f"[{RED}]DES ERROR:[/{RED}] {result['message']}")
        return

    d = result["data"]
    currency = d.get("currency") or "USD"
    mktcap = _fmt_large(d.get("market_cap"), currency)
    div_yield = _fmt_pct(d.get("dividend_yield"))

    # ── Left column ──────────────────────────────────────────────────────────
    left = Table.grid(padding=(0, 1))
    left.add_column(style=DIM, width=22)
    left.add_column(style=GREEN)
    rows_left = [
        ("Name",         d.get("name") or "N/A"),
        ("Exchange",     d.get("exchange") or "N/A"),
        ("Currency",     currency),
        ("Sector",       d.get("sector") or "N/A"),
        ("Industry",     d.get("industry") or "N/A"),
        ("Country",      d.get("country") or "N/A"),
        ("Employees",    f"{d.get('employees'):,}" if d.get("employees") else "N/A"),
    ]
    for label, value in rows_left:
        left.add_row(label, value)

    # ── Right column ─────────────────────────────────────────────────────────
    right = Table.grid(padding=(0, 1))
    right.add_column(style=DIM, width=22)
    right.add_column(style=GREEN)
    rows_right = [
        ("Market Cap",   mktcap),
        ("Shares Out",   _fmt_large(d.get("shares_outstanding"))),
        ("Float",        _fmt_large(d.get("shares_float"))),
        ("Dividend Yld", div_yield),
        ("Beta",         f"{d.get('beta'):.3f}" if d.get("beta") is not None else "N/A"),
        ("Website",      (d.get("website") or "N/A")[:30]),
        ("Phone",        d.get("phone") or "N/A"),
    ]
    for label, value in rows_right:
        right.add_row(label, value)

    # ── Description blurb ────────────────────────────────────────────────────
    desc = (d.get("long_description") or "No description available.")[:300]
    if len(d.get("long_description") or "") > 300:
        desc += "…"

    title = f"[{ORANGE}]DES[/{ORANGE}]  [{HEADER}]{d.get('name', d.get('symbol', ''))}[/{HEADER}]  [{DIM}]{d.get('symbol', '')}[/{DIM}]"

    panel_content = Table.grid(padding=(0, 2))
    panel_content.add_column()
    panel_content.add_column()
    panel_content.add_row(left, right)

    console.print()
    console.print(Panel(panel_content, title=title, border_style="yellow", padding=(1, 2)))
    console.print(Panel(Text(desc, style=DIM), title="Description", border_style="dim", padding=(0, 2)))
    console.print()


# ─── FA ───────────────────────────────────────────────────────────────────────

def render_fa(result: dict) -> None:
    if result["status"] == "error":
        console.print(f"[{RED}]FA ERROR:[/{RED}] {result['message']}")
        return

    d = result["data"]
    currency = d.get("currency") or "USD"
    income = d.get("income_statements", [])
    balance = d.get("balance_sheets", [])
    cashflow = d.get("cash_flows", [])

    if not income:
        console.print(f"[{RED}]FA:[/{RED}] No financial data available.")
        return

    years = [s.get("fiscal_year") or s.get("date", "")[:4] for s in income]
    title = f"[{ORANGE}]FA[/{ORANGE}]  [{HEADER}]{d.get('symbol', '')} — Financial Analysis ({currency})[/{HEADER}]"

    def make_table(section_title: str) -> Table:
        t = Table(title=f"[{SUBHEAD}]{section_title}[/{SUBHEAD}]", border_style="dim",
                  header_style=HEADER, show_lines=False)
        t.add_column("Metric", style=DIM, width=28)
        for y in years:
            t.add_column(str(y), justify="right", style=GREEN)
        return t

    def row(table: Table, label: str, values: list, formatter=None):
        fmt = formatter or (lambda v: _fmt_large(v, currency))
        table.add_row(label, *[fmt(v) if v is not None else "[dim]N/A[/dim]" for v in values])

    # Income statement
    inc_t = make_table("Income Statement")
    row(inc_t, "Revenue",          [s.get("revenue") for s in income])
    row(inc_t, "Gross Profit",     [s.get("gross_profit") for s in income])
    row(inc_t, "Operating Income", [s.get("operating_income") for s in income])
    row(inc_t, "EBITDA",           [s.get("ebitda") for s in income])
    row(inc_t, "Net Income",       [s.get("net_income") for s in income])
    eps_sym = _CURRENCY_SYMBOLS.get(currency, f"{currency} " if currency else "$")
    row(inc_t, "EPS (Diluted)",    [s.get("eps_diluted") for s in income],
        formatter=lambda v: f"{eps_sym}{v:.2f}" if v is not None else "N/A")
    row(inc_t, "R&D",              [s.get("rd_expenses") for s in income])

    # Balance sheet
    if balance:
        bal_t = make_table("Balance Sheet")
        row(bal_t, "Cash & Equivalents", [s.get("cash_and_equivalents") for s in balance])
        row(bal_t, "Total Assets",        [s.get("total_assets") for s in balance])
        row(bal_t, "Total Debt",          [s.get("total_debt") for s in balance])
        row(bal_t, "Net Debt",            [s.get("net_debt") for s in balance])
        row(bal_t, "Total Equity",        [s.get("total_equity") for s in balance])

    # Cash flow
    if cashflow:
        cf_t = make_table("Cash Flow")
        row(cf_t, "Operating Cash Flow", [s.get("operating_cash_flow") for s in cashflow])
        row(cf_t, "CapEx",               [s.get("capital_expenditure") for s in cashflow])
        row(cf_t, "Free Cash Flow",      [s.get("free_cash_flow") for s in cashflow])
        row(cf_t, "Dividends Paid",      [s.get("dividends_paid") for s in cashflow])
        row(cf_t, "Buybacks",            [s.get("common_stock_repurchased") for s in cashflow])

    console.print()
    console.print(Panel(inc_t, title=title, border_style="yellow", padding=(1, 2)))
    if balance:
        console.print(Panel(bal_t, border_style="dim", padding=(1, 2)))
    if cashflow:
        console.print(Panel(cf_t, border_style="dim", padding=(1, 2)))
    console.print()


# ─── GP ───────────────────────────────────────────────────────────────────────

def render_gp(result: dict) -> None:
    if result["status"] == "error":
        console.print(f"[{RED}]GP ERROR:[/{RED}] {result['message']}")
        return

    import sys
    import plotext as plt

    # Force UTF-8 on Windows to handle plotext's Unicode drawing characters
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    d = result["data"]
    bars = d.get("bars", [])
    symbol = d.get("symbol", "")
    lookback = result.get("lookback", len(bars))

    if not bars:
        console.print(f"[{RED}]GP:[/{RED}] No price data available.")
        return

    bars = bars[-lookback:]
    dates = [b["date"] for b in bars]
    closes = [b["close"] for b in bars if b.get("close") is not None]

    if not closes:
        console.print(f"[{RED}]GP:[/{RED}] No close prices in data.")
        return

    pct_chg = ((closes[-1] - closes[0]) / closes[0] * 100) if len(closes) > 1 else 0
    chg_color = GREEN if pct_chg >= 0 else RED

    plt.clf()
    plt.plot_size(100, 20)
    plt.theme("dark")
    plt.plot(closes, color="green")
    plt.title(f"{symbol} — {lookback}d Price (close)")
    plt.xlabel("Days")
    plt.ylabel("Price")
    plt.show()

    console.print(
        f"  [{DIM}]Last:[/{DIM}] [{GREEN}]{closes[-1]:.2f}[/{GREEN}]   "
        f"[{DIM}]Change:[/{DIM}] [{chg_color}]{pct_chg:+.2f}%[/{chg_color}]   "
        f"[{DIM}]Period:[/{DIM}] {dates[0]} → {dates[-1]}"
    )
    console.print()


# ─── ANR ──────────────────────────────────────────────────────────────────────

def render_anr(result: dict) -> None:
    if result["status"] == "error":
        console.print(f"[{RED}]ANR ERROR:[/{RED}] {result['message']}")
        return

    d = result["data"]
    symbol = d.get("symbol", "")
    pt = d.get("price_target") or {}
    title = f"[{ORANGE}]ANR[/{ORANGE}]  [{HEADER}]{symbol} — Analyst Recommendations[/{HEADER}]"

    t = Table(border_style="dim", header_style=HEADER, show_lines=False)
    t.add_column("Metric", style=DIM, width=24)
    t.add_column("Value", style=GREEN)

    if pt:
        t.add_row("Consensus Target",  f"${pt.get('target_consensus'):.2f}" if pt.get("target_consensus") else "N/A")
        t.add_row("Target High",       f"${pt.get('target_high'):.2f}" if pt.get("target_high") else "N/A")
        t.add_row("Target Low",        f"${pt.get('target_low'):.2f}" if pt.get("target_low") else "N/A")
        t.add_row("Target Median",     f"${pt.get('target_median'):.2f}" if pt.get("target_median") else "N/A")

    if d.get("consensus_rating"):
        t.add_row("Consensus Rating",  str(d.get("consensus_rating")))
    if d.get("num_analysts"):
        t.add_row("# Analysts",        str(d.get("num_analysts")))

    # Buy/hold/sell bar
    buy_ct   = (d.get("strong_buy") or 0) + (d.get("buy") or 0)
    hold_ct  = d.get("hold") or 0
    sell_ct  = (d.get("sell") or 0) + (d.get("strong_sell") or 0)
    if buy_ct or hold_ct or sell_ct:
        t.add_row("", "")
        t.add_row("Strong Buy / Buy",  f"[{GREEN}]{buy_ct}[/{GREEN}]")
        t.add_row("Hold",              f"[yellow]{hold_ct}[/yellow]")
        t.add_row("Sell / Strong Sell",f"[{RED}]{sell_ct}[/{RED}]")

    console.print()
    console.print(Panel(t, title=title, border_style="yellow", padding=(1, 2)))
    console.print()


# ─── COMP ─────────────────────────────────────────────────────────────────────

def render_comp(result: dict) -> None:
    if result["status"] == "error":
        console.print(f"[{RED}]COMP ERROR:[/{RED}] {result['message']}")
        return

    d = result["data"]
    symbol = d.get("symbol", "")
    peers = d.get("peers", [])
    title = f"[{ORANGE}]COMP[/{ORANGE}]  [{HEADER}]{symbol} — Comparables[/{HEADER}]"

    if not peers:
        console.print(f"[{RED}]COMP:[/{RED}] No comparable companies found.")
        return

    t = Table(border_style="dim", header_style=HEADER, show_lines=True, expand=True)
    t.add_column("Ticker",    style=ORANGE, min_width=6,  max_width=8,  no_wrap=True)
    t.add_column("Name",      style=HEADER, min_width=20, max_width=26, no_wrap=True)
    t.add_column("Mkt Cap",   justify="right", style=GREEN, min_width=9)
    t.add_column("Revenue",   justify="right", style=GREEN, min_width=9)
    t.add_column("Gross Mgn", justify="right", style=GREEN, min_width=9)
    t.add_column("Net Mgn",   justify="right", style=GREEN, min_width=8)
    t.add_column("EBITDA",    justify="right", style=GREEN, min_width=9)
    t.add_column("Net Debt",  justify="right", style=GREEN, min_width=9)
    t.add_column("Beta",      justify="right", style=DIM,   min_width=5)

    for p in peers:
        curr = p.get("currency") or ""
        t.add_row(
            p.get("symbol", ""),
            (p.get("name") or "")[:22],
            _fmt_large(p.get("market_cap"), curr),
            _fmt_large(p.get("revenue"), curr),
            _fmt_pct(p.get("gross_margin")),
            _fmt_pct(p.get("net_margin")),
            _fmt_large(p.get("ebitda"), curr),
            _fmt_large(p.get("total_debt"), curr),
            f"{p.get('beta'):.2f}" if p.get("beta") is not None else "N/A",
        )

    console.print()
    console.print(Panel(t, title=title, border_style="yellow", padding=(1, 2)))
    console.print()


# ─── Error / status ───────────────────────────────────────────────────────────

def render_error(message: str) -> None:
    console.print(f"[{RED}]ERROR:[/{RED}] {message}")


def render_status(message: str) -> None:
    console.print(f"[{DIM}]{message}[/{DIM}]")


def render_loaded(ticker_str: str) -> None:
    console.print(f"[{ORANGE}]Security loaded:[/{ORANGE}] [{GREEN}]{ticker_str}[/{GREEN}]")
