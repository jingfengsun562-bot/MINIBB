"""
Investment-bank-style HTML report renderer for RPT.
Writes a self-contained .html file to reports/{SYMBOL}_{YYYYMMDD}.html.
Returns the Path of the written file.
"""

import html as _html
from pathlib import Path
from typing import Optional

_REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"

_CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
    "HKD": "HK$", "CNY": "¥", "KRW": "₩", "AUD": "A$",
    "SGD": "S$", "INR": "₹",
}

_RATING_COLORS = {
    "buy":        "#176a3e",
    "strong buy": "#176a3e",
    "hold":       "#d97706",
    "sell":       "#b91c1c",
    "strong sell":"#b91c1c",
}


# ── Value formatters ───────────────────────────────────────────────────────────

def _e(v) -> str:
    """HTML-escape a string value."""
    return _html.escape(str(v)) if v is not None else ""


def _sym(currency: str) -> str:
    return _CURRENCY_SYMBOLS.get(currency, f"{currency}&nbsp;" if currency else "")


def _n(v, currency: str = "") -> str:
    if v is None:
        return "N/A"
    prefix = _sym(currency)
    sign = "−" if v < 0 else ""
    av = abs(v)
    if av >= 1e12:
        return f"{sign}{prefix}{av/1e12:.2f}T"
    if av >= 1e9:
        return f"{sign}{prefix}{av/1e9:.1f}B"
    if av >= 1e6:
        return f"{sign}{prefix}{av/1e6:.1f}M"
    return f"{sign}{prefix}{av:,.0f}"


def _pct(v) -> str:
    """Ratio → percent: 0.469 → '46.9%'."""
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%"


def _pct_raw(v) -> str:
    """Already-percent → percent string: 0.38 → '0.38%'."""
    if v is None:
        return "N/A"
    return f"{v:.2f}%"


def _x(v) -> str:
    if v is None:
        return "N/A"
    return f"{v:.1f}×"


def _p(v, currency: str = "") -> str:
    if v is None:
        return "N/A"
    return f"{_sym(currency)}{v:.2f}"


# ── CSS ────────────────────────────────────────────────────────────────────────

_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 13px;
    background: #e8ecf2;
    color: #1a1a2e;
    line-height: 1.55;
  }
  .page {
    max-width: 980px;
    margin: 32px auto;
    background: #fff;
    box-shadow: 0 4px 32px rgba(0,0,0,0.15);
  }
  /* ── HEADER ── */
  .header {
    background: linear-gradient(135deg, #0a1628 0%, #16305a 100%);
    border-bottom: 3px solid #c9a227;
  }
  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 36px 14px;
    border-bottom: 1px solid rgba(201,162,39,0.25);
  }
  .firm-name {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #c9a227;
  }
  .report-type {
    font-size: 10.5px;
    color: rgba(255,255,255,0.45);
    text-align: right;
    line-height: 1.8;
  }
  .header-main { padding: 22px 36px 26px; }
  .company-name {
    font-family: 'Merriweather', Georgia, serif;
    font-size: 26px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.3px;
  }
  .ticker-badge {
    display: inline-block;
    background: #c9a227;
    color: #0a1628;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px 2px;
    border-radius: 2px;
    margin-left: 12px;
    letter-spacing: 0.8px;
    vertical-align: middle;
    position: relative;
    top: -3px;
  }
  .subtitle {
    color: rgba(255,255,255,0.5);
    font-size: 11.5px;
    margin-top: 5px;
  }
  .rating-strip {
    display: flex;
    align-items: center;
    gap: 28px;
    margin-top: 18px;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,0.1);
  }
  .rating-pill {
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    padding: 5px 18px;
    border-radius: 20px;
    letter-spacing: 1px;
  }
  .stat-item { color: rgba(255,255,255,0.85); }
  .stat-item .lbl {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: rgba(255,255,255,0.4);
    display: block;
  }
  .stat-item .val { font-size: 16px; font-weight: 600; }
  .stat-item .val.gold { color: #c9a227; }
  .stat-item .val.pos  { color: #6ee7a0; }
  .stat-item .val.neg  { color: #fca5a5; }
  /* ── KPI BAR ── */
  .kpi-bar {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    border-bottom: 2px solid #16305a;
  }
  .kpi {
    padding: 13px 14px;
    text-align: center;
    border-right: 1px solid #dde2ee;
    background: #f5f7fc;
  }
  .kpi:last-child { border-right: none; }
  .kpi-label {
    font-size: 9.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #8492a6;
  }
  .kpi-value {
    font-size: 16px;
    font-weight: 700;
    color: #0a1628;
    margin-top: 3px;
    font-variant-numeric: tabular-nums;
  }
  .pos { color: #176a3e; }
  .neg { color: #b91c1c; }
  /* ── BODY ── */
  .body { padding: 30px 36px 36px; }
  .section { margin-bottom: 30px; }
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 13px;
    padding-bottom: 8px;
    border-bottom: 2px solid #16305a;
  }
  .section-num {
    width: 24px; height: 24px;
    background: #16305a;
    color: #c9a227;
    border-radius: 50%;
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .section-title {
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #16305a;
  }
  .section-title .sub {
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0;
    text-transform: none;
    color: #8492a6;
    margin-left: 6px;
  }
  /* ── TABLES ── */
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  thead th {
    background: #16305a;
    color: #fff;
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    padding: 9px 12px;
    text-align: right;
    white-space: nowrap;
  }
  thead th:first-child { text-align: left; }
  thead th:not(:first-child) { font-size: 13px; font-weight: 700; letter-spacing: 0; text-transform: none; }
  tbody tr:nth-child(even) { background: #f7f9fd; }
  tbody tr:hover { background: #edf1fa; }
  tbody td {
    padding: 8px 12px;
    border-bottom: 1px solid #e8ecf4;
    color: #374151;
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
  tbody td:first-child {
    text-align: left;
    font-weight: 500;
    color: #111827;
  }
  .row-accent td { background: #eff3fc !important; font-weight: 600; }
  .peer-self td { background: #fefce8 !important; font-weight: 600; }
  .peer-self td:first-child { border-left: 3px solid #c9a227; }
  /* ── STATEMENT SECTION DIVIDERS ── */
  .row-section td {
    background: #E0E0E0 !important;
    color: #98FB98;
    font-weight: 700;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 7px 12px;
    border: none;
  }
  .row-section:hover td { background: #E0E0E0 !important; }
  .row-section td:first-child { border-left: none; }
  /* ── INLINE % ROWS ── */
  .row-pct td {
    background: #f0f2f8 !important;
    color: #6b7280;
    font-size: 11px;
    font-style: italic;
    padding: 3px 12px 3px 28px;
    border-bottom: none;
  }
  .row-pct:hover td { background: #e8ecf4 !important; }
  .row-pct td:first-child { color: #6b7280; font-weight: 400; text-align: left; padding-left: 28px; }
  /* ── PROFILE TWO-COL ── */
  .two-col { display: grid; grid-template-columns: 1fr 1.4fr; gap: 20px; }
  .profile-table tbody td { text-align: left; }
  .profile-table tbody td:first-child {
    color: #6b7280;
    font-weight: 400;
    width: 40%;
  }
  .desc-box {
    background: #f8fafd;
    border-left: 4px solid #c9a227;
    border-radius: 0 4px 4px 0;
    padding: 14px 16px;
    font-size: 12px;
    color: #4b5563;
    line-height: 1.75;
  }
  /* ── VALUATION CARDS ── */
  .val-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  .val-card {
    background: #f5f7fc;
    border: 1px solid #dde2ee;
    border-radius: 4px;
    padding: 12px 14px;
    text-align: center;
  }
  .val-card .lbl {
    font-size: 9.5px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #8492a6;
    font-weight: 600;
  }
  .val-card .val {
    font-size: 19px;
    font-weight: 700;
    color: #0a1628;
    margin-top: 4px;
    font-variant-numeric: tabular-nums;
  }
  /* ── ANALYST CONSENSUS ── */
  .consensus-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .bar-row { margin-bottom: 10px; }
  .bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    margin-bottom: 4px;
    color: #374151;
  }
  .bar-track { height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; }
  .bar-fill.buy  { background: #176a3e; }
  .bar-fill.hold { background: #d97706; }
  .bar-fill.sell { background: #b91c1c; }
  /* ── FOOTER ── */
  .footer {
    background: #0a1628;
    padding: 12px 36px 14px;
    border-top: 2px solid #c9a227;
  }
  .footer-disclaimer {
    font-size: 9.5px;
    color: rgba(255,255,255,0.3);
    line-height: 1.6;
  }
  .footer-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(201,162,39,0.2);
    font-size: 10px;
    color: rgba(255,255,255,0.35);
  }
  .footer-bar .pgnum { color: #c9a227; font-weight: 700; }
"""


# ── Section helper ─────────────────────────────────────────────────────────────

def _section(num: int, title: str, sub: str = "") -> str:
    sub_html = f'<span class="sub">{_e(sub)}</span>' if sub else ""
    return (
        f'<div class="section-header">'
        f'<div class="section-num">{num}</div>'
        f'<div class="section-title">{_e(title)}{sub_html}</div>'
        f'</div>'
    )


def _th(*cols) -> str:
    cells = "".join(f"<th>{_e(c)}</th>" for c in cols)
    return f"<thead><tr>{cells}</tr></thead>"


def _td_row(cells: list, cls: str = "") -> str:
    row_cls = f' class="{cls}"' if cls else ""
    tds = "".join(f"<td>{c}</td>" for c in cells)
    return f"<tr{row_cls}>{tds}</tr>"


# ── Statement table builder ────────────────────────────────────────────────────

def _build_table(specs: list, rows_raw: list, currency: str,
                 revenue_by_year: dict | None = None) -> str:
    """
    Build a financial statement HTML table from a list of row specs.

    Spec types:
      ("section",    "LABEL")                         → navy divider row
      ("data",       "Label", key, fmt)               → normal data row
      ("data_accent","Label", key, fmt)               → accented data row
      ("pct",        "Label", num_key, denom_key)     → % row, both keys in same statement
      ("pct_ext",    "Label", num_key)                → % row, denom from revenue_by_year dict

    fmt values: "money" (currency-prefixed), "price" (_p format), "count" (no currency prefix)
    """
    if not rows_raw:
        return "<p style='color:#8492a6;font-size:12px'>No data available.</p>"

    years  = [r.get("fiscal_year") or "" for r in rows_raw]
    n_cols = len(years) + 1
    th     = _th("", *years)

    body = []
    for spec in specs:
        kind = spec[0]

        if kind == "section":
            body.append(
                f'<tr class="row-section">'
                f'<td colspan="{n_cols}">{_e(spec[1])}</td>'
                f'</tr>'
            )

        elif kind in ("data", "data_accent"):
            label, key, fmt = spec[1], spec[2], spec[3]
            if fmt == "price":
                vals = [_p(r.get(key), currency) for r in rows_raw]
            elif fmt == "count":
                vals = [_n(r.get(key)) for r in rows_raw]
            else:
                vals = [_n(r.get(key), currency) for r in rows_raw]
            cls = "row-accent" if kind == "data_accent" else ""
            body.append(_td_row([label] + vals, cls))

        elif kind == "pct":
            label, num_key, denom_key = spec[1], spec[2], spec[3]
            vals = []
            for r in rows_raw:
                num   = r.get(num_key)
                denom = r.get(denom_key)
                vals.append(_pct(num / denom) if num is not None and denom else "N/A")
            body.append(_td_row([label] + vals, "row-pct"))

        elif kind == "pct_ext":
            label, num_key = spec[1], spec[2]
            vals = []
            for r in rows_raw:
                num   = r.get(num_key)
                yr    = r.get("fiscal_year")
                denom = (revenue_by_year or {}).get(yr)
                vals.append(_pct(num / denom) if num is not None and denom else "N/A")
            body.append(_td_row([label] + vals, "row-pct"))

    return f"<table>{th}<tbody>{''.join(body)}</tbody></table>"


# ── Statement specs ────────────────────────────────────────────────────────────

_IS_SPECS = [
    ("section",    "Revenue"),
    ("data",       "Total Revenue",             "revenue",                       "money"),
    ("data",       "Cost of Revenue",           "cost_of_revenue",               "money"),
    ("section",    "Gross Profit"),
    ("data",       "Gross Profit",              "gross_profit",                  "money"),
    ("pct",        "  Gross Margin %",          "gross_profit",    "revenue"),
    ("section",    "Operating Expenses"),
    ("data",       "R&D Expenses",              "rd_expenses",                   "money"),
    ("data",       "SG&A Expenses",             "sga_expenses",                  "money"),
    ("data",       "Total Operating Expenses",  "operating_expenses",            "money"),
    ("section",    "Operating Income"),
    ("data_accent","Operating Income",          "operating_income",              "money"),
    ("pct",        "  Operating Margin %",      "operating_income", "revenue"),
    ("data",       "EBIT",                      "ebit",                          "money"),
    ("data_accent","EBITDA",                    "ebitda",                        "money"),
    ("pct",        "  EBITDA Margin %",         "ebitda",          "revenue"),
    ("section",    "Below the Line"),
    ("data",       "D&A",                       "depreciation_and_amortization", "money"),
    ("data",       "Interest Expense",          "interest_expense",              "money"),
    ("data",       "Income Tax Expense",        "income_tax_expense",            "money"),
    ("section",    "Net Income & EPS"),
    ("data_accent","Net Income",                "net_income",                    "money"),
    ("pct",        "  Net Margin %",            "net_income",      "revenue"),
    ("data",       "EPS (Basic)",               "eps",                           "price"),
    ("data",       "EPS (Diluted)",             "eps_diluted",                   "price"),
    ("data",       "Wtd Avg Shares",            "weighted_avg_shares",           "count"),
    ("data",       "Wtd Avg Shares (Dil.)",     "weighted_avg_shares_diluted",   "count"),
]

_BS_SPECS = [
    ("section",    "Current Assets"),
    ("data",       "Cash & Equivalents",        "cash_and_equivalents",          "money"),
    ("data",       "Short-term Investments",    "short_term_investments",        "money"),
    ("data",       "Net Receivables",           "net_receivables",               "money"),
    ("data",       "Inventory",                 "inventory",                     "money"),
    ("data_accent","Total Current Assets",      "total_current_assets",          "money"),
    ("section",    "Non-Current Assets"),
    ("data",       "Goodwill",                  "goodwill",                      "money"),
    ("data",       "Total Non-Current Assets",  "total_non_current_assets",      "money"),
    ("data_accent","Total Assets",              "total_assets",                  "money"),
    ("section",    "Current Liabilities"),
    ("data",       "Accounts Payable",          "accounts_payable",              "money"),
    ("data",       "Short-term Debt",           "short_term_debt",               "money"),
    ("data_accent","Total Current Liabilities", "total_current_liabilities",     "money"),
    ("section",    "Non-Current Liabilities"),
    ("data",       "Long-term Debt",            "long_term_debt",                "money"),
    ("data",       "Total Non-Current Liab.",   "total_non_current_liabilities", "money"),
    ("data_accent","Total Liabilities",         "total_liabilities",             "money"),
    ("section",    "Equity"),
    ("data",       "Retained Earnings",         "retained_earnings",             "money"),
    ("data",       "Total Stockholders' Eq.",   "total_stockholders_equity",     "money"),
    ("data_accent","Total Equity",              "total_equity",                  "money"),
    ("data",       "Total Debt",                "total_debt",                    "money"),
    ("data_accent","Net Debt",                  "net_debt",                      "money"),
]

_CF_SPECS = [
    ("section",    "Operating Activities"),
    ("data",       "Net Income",                "net_income",                    "money"),
    ("data",       "D&A",                       "depreciation_and_amortization", "money"),
    ("data",       "Stock-Based Comp.",         "stock_based_compensation",      "money"),
    ("data",       "Change in Working Cap.",    "change_in_working_capital",     "money"),
    ("data_accent","Operating Cash Flow",       "operating_cash_flow",           "money"),
    ("pct_ext",    "  OCF Margin %",            "operating_cash_flow"),
    ("section",    "Investing Activities"),
    ("data",       "Capital Expenditure",       "capital_expenditure",           "money"),
    ("pct_ext",    "  CapEx % of Revenue",      "capital_expenditure"),
    ("data",       "Net Investing Activities",  "net_investing_activities",      "money"),
    ("section",    "Financing Activities"),
    ("data",       "Dividends Paid",            "dividends_paid",                "money"),
    ("data",       "Stock Repurchased",         "common_stock_repurchased",      "money"),
    ("data",       "Net Financing Activities",  "net_financing_activities",      "money"),
    ("section",    "Free Cash Flow"),
    ("data_accent","Free Cash Flow",            "free_cash_flow",                "money"),
    ("pct_ext",    "  FCF Margin %",            "free_cash_flow"),
    ("data",       "Net Change in Cash",        "net_change_in_cash",            "money"),
]


# ── Main render function ───────────────────────────────────────────────────────

def render_report_html(result: dict) -> Path:
    """Render the full equity report as an HTML file and return the path."""
    if result.get("status") != "ok":
        raise ValueError(result.get("message", "RPT returned error"))

    d        = result["data"]
    sym      = d.get("symbol", "")
    gendt    = d.get("generated_at", "")
    prof     = d.get("profile") or {}
    fin      = d.get("financials") or {}
    rlist    = d.get("ratios_by_year") or []
    val      = d.get("valuation") or {}
    anl      = d.get("analyst") or {}
    comp     = d.get("comparables") or {}

    currency = fin.get("currency") or prof.get("currency") or ""
    name     = prof.get("name") or sym
    income   = fin.get("income_statements") or []
    balance  = fin.get("balance_sheets") or []
    cashflow = fin.get("cash_flows") or []
    peers    = comp.get("peers") or []

    # ── Header derived values ──────────────────────────────────────────────────
    sector   = prof.get("sector") or ""
    exchange = prof.get("exchange") or ""
    rating_raw = (anl.get("consensus_rating") or "").strip()
    rating_color = _RATING_COLORS.get(rating_raw.lower(), "#4b5563")

    pt = anl.get("price_target") or {}
    target    = pt.get("target_consensus")
    cur_price = val.get("current_price")
    upside_html = ""
    if target and cur_price and cur_price != 0:
        upside_pct = (target - cur_price) / cur_price * 100
        cls = "pos" if upside_pct >= 0 else "neg"
        sign = "+" if upside_pct >= 0 else ""
        upside_html = (
            f'<div class="stat-item">'
            f'<span class="lbl">Upside</span>'
            f'<span class="val {cls}">{sign}{upside_pct:.1f}%</span>'
            f'</div>'
        )

    # ── KPI bar values ─────────────────────────────────────────────────────────
    kpi_pe       = _x(val.get("pe_ratio"))
    kpi_evebitda = _x(val.get("ev_to_ebitda"))
    kpi_fcfy     = _pct(val.get("fcf_yield"))
    kpi_divy     = _pct_raw(val.get("dividend_yield"))
    kpi_mktcap   = _n(val.get("market_cap"), currency)

    kpi_fcfy_cls = "pos" if (val.get("fcf_yield") or 0) > 0 else ""

    # ── Financial statement tables ─────────────────────────────────────────────
    revenue_by_year = {
        r.get("fiscal_year"): r.get("revenue")
        for r in income
        if r.get("revenue")
    }
    income_table  = _build_table(_IS_SPECS, income,   currency)
    balance_table = _build_table(_BS_SPECS, balance,  currency)
    cf_table      = _build_table(_CF_SPECS, cashflow, currency, revenue_by_year)

    # ── Ratios table ───────────────────────────────────────────────────────────
    def _ratio_table() -> str:
        if not rlist:
            return "<p style='color:#8492a6;font-size:12px'>No ratio data available.</p>"
        ryears = [r.get("fiscal_year") or "" for r in rlist]
        th = _th("Ratio", *ryears)
        metrics = [
            ("Gross Margin",      "gross_margin",       _pct,     False),
            ("Operating Margin",  "operating_margin",   _pct,     False),
            ("Net Margin",        "net_margin",         _pct,     False),
            ("EBITDA Margin",     "ebitda_margin",      _pct,     False),
            ("ROE",               "roe",                _pct,     False),
            ("ROA",               "roa",                _pct,     False),
            ("Debt / Equity",     "debt_to_equity",     _x,       False),
            ("Net Debt / EBITDA", "net_debt_to_ebitda", _x,       False),
            ("Current Ratio",     "current_ratio",      _x,       False),
            ("Asset Turnover",    "asset_turnover",     _x,       False),
            ("FCF Margin",        "fcf_margin",         _pct,     True),
        ]
        body_rows = []
        for label, key, fmt, accent in metrics:
            vals = [fmt(r.get(key)) for r in rlist]
            cls = "row-accent" if accent else ""
            body_rows.append(_td_row([label] + vals, cls))
        return f"<table>{th}<tbody>{''.join(body_rows)}</tbody></table>"

    # ── Valuation cards ────────────────────────────────────────────────────────
    def _val_card(label: str, value: str, cls: str = "") -> str:
        val_cls = f' class="val {cls}"' if cls else ' class="val"'
        return (
            f'<div class="val-card">'
            f'<div class="lbl">{label}</div>'
            f'<div{val_cls}>{value}</div>'
            f'</div>'
        )

    fcfy_cls = "pos" if (val.get("fcf_yield") or 0) > 0 else ""
    val_cards_html = (
        _val_card("Current Price",    _p(val.get("current_price"), currency)) +
        _val_card("Market Cap",       _n(val.get("market_cap"), currency)) +
        _val_card("Enterprise Value", _n(val.get("enterprise_value"), currency)) +
        _val_card("P / E",            _x(val.get("pe_ratio"))) +
        _val_card("P / B",            _x(val.get("pb_ratio"))) +
        _val_card("EV / EBITDA",      _x(val.get("ev_to_ebitda"))) +
        _val_card("EV / Sales",       _x(val.get("ev_to_sales"))) +
        _val_card("FCF Yield",        _pct(val.get("fcf_yield")), fcfy_cls)
    )

    # ── Analyst consensus ──────────────────────────────────────────────────────
    n_buy  = (anl.get("strong_buy") or 0) + (anl.get("buy") or 0)
    n_hold = anl.get("hold") or 0
    n_sell = (anl.get("sell") or 0) + (anl.get("strong_sell") or 0)
    n_total = n_buy + n_hold + n_sell or 1  # avoid div-by-zero

    def _bar(label: str, count: int, cls: str) -> str:
        pct = round(count / n_total * 100)
        return (
            f'<div class="bar-row">'
            f'<div class="bar-label"><span>{label}</span><span>{count}</span></div>'
            f'<div class="bar-track"><div class="bar-fill {cls}" style="width:{pct}%"></div></div>'
            f'</div>'
        )

    rating_display = rating_raw or "N/A"
    rating_style = f"color:{rating_color};font-weight:700"
    anl_table_rows = [
        f'<tr><td>Consensus Rating</td><td style="text-align:right;{rating_style}">{_e(rating_display)}</td></tr>',
        f'<tr><td># Analysts</td><td style="text-align:right">{anl.get("num_analysts") or "N/A"}</td></tr>',
        f'<tr><td>Price Target (Consensus)</td><td style="text-align:right">{_p(pt.get("target_consensus"), currency)}</td></tr>',
        f'<tr><td>Price Target High</td><td style="text-align:right">{_p(pt.get("target_high"), currency)}</td></tr>',
        f'<tr><td>Price Target Low</td><td style="text-align:right">{_p(pt.get("target_low"), currency)}</td></tr>',
    ]
    anl_bars = (
        _bar("Buy / Strong Buy",   n_buy,  "buy") +
        _bar("Hold",               n_hold, "hold") +
        _bar("Sell / Strong Sell", n_sell, "sell")
    ) if (n_buy + n_hold + n_sell) > 0 else "<p style='color:#8492a6;font-size:12px'>No breakdown available.</p>"

    # ── Peer comparison table ──────────────────────────────────────────────────
    def _peer_table() -> str:
        if not peers:
            return "<p style='color:#8492a6;font-size:12px'>No peer data available.</p>"
        th = _th("Ticker", "Company", "Mkt Cap", "P / E", "EV/EBITDA", "Gross Mgn", "Net Mgn", "FCF Yld")
        rows = []
        # Subject ticker row first (from valuation + ratios)
        sub_gm = sub_nm = sub_fcfy_peer = "N/A"
        if rlist:
            r0 = rlist[0]
            sub_gm   = _pct(r0.get("gross_margin"))
            sub_nm   = _pct(r0.get("net_margin"))
            sub_fcfy_peer = _pct(r0.get("fcf_margin"))
        ev_ebitda_sub = _x(val.get("ev_to_ebitda"))
        rows.append(_td_row(
            [sym, _e(name), _n(val.get("market_cap"), currency),
             _x(val.get("pe_ratio")), ev_ebitda_sub, sub_gm, sub_nm, sub_fcfy_peer],
            "peer-self"
        ))
        for p in peers:
            pc = p.get("currency") or ""
            mktcap = p.get("market_cap")
            ebitda_p = p.get("ebitda")
            total_debt_p = p.get("total_debt")
            ev_p = None
            if mktcap and total_debt_p is not None:
                ev_p = mktcap + (total_debt_p or 0)
            ev_ebitda_p = _x(ev_p / ebitda_p if ev_p and ebitda_p else None)
            # peer margins stored on 0-100 scale → divide by 100 for _pct()
            gm_p = _pct(p.get("gross_margin") / 100) if p.get("gross_margin") is not None else "N/A"
            nm_p = _pct(p.get("net_margin") / 100)   if p.get("net_margin")   is not None else "N/A"
            fcfy_p = _pct(p.get("fcf_yield")) if p.get("fcf_yield") is not None else "N/A"
            rows.append(_td_row([
                _e(p.get("symbol", "")),
                _e((p.get("name") or "")[:24]),
                _n(mktcap, pc),
                _x(p.get("pe_ratio")),
                ev_ebitda_p,
                gm_p, nm_p, fcfy_p,
            ]))
        return f"<table>{th}<tbody>{''.join(rows)}</tbody></table>"

    # ── Assemble HTML ──────────────────────────────────────────────────────────
    subtitle_parts = [s for s in [sector, exchange, currency] if s]
    subtitle = " &nbsp;·&nbsp; ".join(_e(p) for p in subtitle_parts)

    rating_pill_html = (
        f'<span class="rating-pill" style="background:{rating_color};border:1px solid {rating_color}">'
        f'{_e(rating_display)}'
        f'</span>'
    ) if rating_raw else ""

    target_html = (
        f'<div class="stat-item">'
        f'<span class="lbl">12-mo Target</span>'
        f'<span class="val gold">{_p(target, currency)}</span>'
        f'</div>'
    ) if target else ""

    price_html = (
        f'<div class="stat-item">'
        f'<span class="lbl">Current Price</span>'
        f'<span class="val">{_p(cur_price, currency)}</span>'
        f'</div>'
    ) if cur_price else ""

    desc = _e(prof.get("long_description") or "")
    if prof.get("long_description") and len(prof["long_description"]) > 600:
        desc = _e(prof["long_description"][:600]) + "…"

    date_display = gendt[:10] if gendt else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_e(name)} ({_e(sym)}) — Equity Report</title>
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>{_CSS}</style>
</head>
<body>
<div class="page">

<!-- HEADER -->
<header class="header">
  <div class="header-top">
    <div class="firm-name">Mini BB Research</div>
    <div class="report-type">Equity Research &nbsp;·&nbsp; {_e(sector or "Equity")}<br>{_e(date_display)} &nbsp;·&nbsp; Full Report</div>
  </div>
  <div class="header-main">
    <div>
      <span class="company-name">{_e(name)}</span>
      <span class="ticker-badge">{_e(sym)}</span>
    </div>
    <div class="subtitle">{subtitle}</div>
    <div class="rating-strip">
      {rating_pill_html}
      {target_html}
      {price_html}
      {upside_html}
    </div>
  </div>
</header>

<!-- KPI BAR -->
<div class="kpi-bar">
  <div class="kpi"><div class="kpi-label">Market Cap</div><div class="kpi-value">{kpi_mktcap}</div></div>
  <div class="kpi"><div class="kpi-label">P / E</div><div class="kpi-value">{kpi_pe}</div></div>
  <div class="kpi"><div class="kpi-label">EV / EBITDA</div><div class="kpi-value">{kpi_evebitda}</div></div>
  <div class="kpi"><div class="kpi-label">FCF Yield</div><div class="kpi-value {kpi_fcfy_cls}">{kpi_fcfy}</div></div>
  <div class="kpi"><div class="kpi-label">Div. Yield</div><div class="kpi-value">{kpi_divy}</div></div>
</div>

<!-- BODY -->
<div class="body">

  <!-- §1 Company Profile -->
  <div class="section">
    {_section(1, "Company Profile")}
    <div class="two-col">
      <table class="profile-table"><tbody>
        <tr><td>Sector</td><td>{_e(prof.get("sector") or "N/A")}</td></tr>
        <tr><td>Industry</td><td>{_e(prof.get("industry") or "N/A")}</td></tr>
        <tr><td>Country</td><td>{_e(prof.get("country") or "N/A")}</td></tr>
        <tr><td>Exchange</td><td>{_e(prof.get("exchange") or "N/A")}</td></tr>
        <tr><td>Currency</td><td>{_e(currency or "N/A")}</td></tr>
        <tr><td>Employees</td><td>{f"{prof['employees']:,}" if prof.get("employees") else "N/A"}</td></tr>
        <tr><td>Shares Outstanding</td><td>{_n(prof.get("shares_outstanding"))}</td></tr>
        <tr><td>Float</td><td>{_n(prof.get("shares_float"))}</td></tr>
        <tr><td>Beta</td><td>{f"{prof['beta']:.2f}" if prof.get("beta") is not None else "N/A"}</td></tr>
        <tr><td>Dividend Yield</td><td>{_pct_raw(prof.get("dividend_yield"))}</td></tr>
        <tr><td>Website</td><td>{_e(prof.get("website") or "N/A")}</td></tr>
      </tbody></table>
      <div class="desc-box">{desc if desc else "No description available."}</div>
    </div>
  </div>

  <!-- §2 Income Statement -->
  <div class="section">
    {_section(2, "Income Statement", currency)}
    {income_table}
  </div>

  <!-- §3 Balance Sheet -->
  <div class="section">
    {_section(3, "Balance Sheet", currency)}
    {balance_table}
  </div>

  <!-- §4 Cash Flow -->
  <div class="section">
    {_section(4, "Cash Flow", currency)}
    {cf_table}
  </div>

  <!-- §5 Financial Ratios -->
  <div class="section">
    {_section(5, "Financial Ratios")}
    {_ratio_table()}
  </div>

  <!-- §6 Valuation Multiples -->
  <div class="section">
    {_section(6, "Valuation Multiples", f"As of {date_display}")}
    <div class="val-grid">{val_cards_html}</div>
  </div>

  <!-- §7 Analyst Consensus -->
  <div class="section">
    {_section(7, "Analyst Consensus")}
    <div class="consensus-grid">
      <table><tbody>{''.join(anl_table_rows)}</tbody></table>
      <div>{anl_bars}</div>
    </div>
  </div>

  <!-- §8 Peer Comparison -->
  <div class="section">
    {_section(8, "Peer Comparison")}
    {_peer_table()}
  </div>

</div><!-- /body -->

<!-- FOOTER -->
<footer class="footer">
  <div class="footer-disclaimer">
    This report is generated by Mini-Bloomberg for informational and educational purposes only.
    It does not constitute investment advice or a solicitation to buy or sell any security.
    Data sourced from Financial Modeling Prep (FMP) and OpenBB / yfinance.
    Accuracy of financial data is not guaranteed. Past performance is not indicative of future results.
  </div>
  <div class="footer-bar">
    <span>Mini BB Research &nbsp;·&nbsp; {_e(date_display)}</span>
    <span class="pgnum">Page 1 of 1</span>
  </div>
</footer>

</div><!-- /page -->
</body>
</html>"""

    _REPORTS_DIR.mkdir(exist_ok=True)
    filename = f"{sym}_{(gendt or '').replace('-', '')[:8]}.html"
    out_path = _REPORTS_DIR / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path
