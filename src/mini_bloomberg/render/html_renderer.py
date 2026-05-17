"""
Investment-bank-style HTML report renderer for RPT.
Writes a self-contained .html file to reports/{SYMBOL}_{YYYYMMDD}.html.
Returns the Path of the written file.
"""

import html as _html
import json
from pathlib import Path
from typing import Optional

_REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "reports"
_XLSX_JS_PATH = Path(__file__).parent / "_xlsx_js_style.min.js"
_XLSX_JS_INLINE = _XLSX_JS_PATH.read_text(encoding="utf-8") if _XLSX_JS_PATH.exists() else ""

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
  /* ── Insights section ── */
  .insights-grid {
    display: grid;
    grid-template-columns: 1.6fr 1fr;
    gap: 28px;
    margin-top: 14px;
  }
  .insights-left { display: flex; flex-direction: column; gap: 22px; }
  .insights-block-title {
    font-size: 10.5px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; color: #8492a6; margin-bottom: 8px;
    border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;
  }
  .insights-text { font-size: 13px; line-height: 1.75; color: #1e293b; }
  .insights-text p { margin: 0 0 10px 0; }
  .insights-right { display: flex; flex-direction: column; gap: 22px; }
  .ins-anl-rating { display: flex; align-items: baseline; gap: 14px; margin-bottom: 10px; }
  .ins-anl-pill {
    font-size: 11px; font-weight: 700; letter-spacing: 1px;
    padding: 3px 10px; border-radius: 3px; color: #fff; text-transform: uppercase;
    flex-shrink: 0;
  }
  .ins-anl-target { font-size: 22px; font-weight: 700; color: #16305a; }
  .ins-anl-upside { font-size: 13px; font-weight: 600; }
  .ins-anl-table { width: 100%; border-collapse: collapse; font-size: 12px; }
  .ins-anl-table td { padding: 4px 6px; border-bottom: 1px solid #e8ecf2; }
  .ins-anl-table td:last-child { text-align: right; font-weight: 600; }
  .trading-table { width: 100%; border-collapse: collapse; font-size: 12px; }
  .trading-table td { padding: 5px 6px; border-bottom: 1px solid #e8ecf2; }
  .trading-table td:last-child { text-align: right; font-weight: 600; color: #16305a; }
  .xlsx-callout {
    display: flex;
    align-items: flex-start;
    gap: 18px;
    background: #f0f4ff;
    border: 1px solid #d0d9f0;
    border-left: 4px solid #16305a;
    border-radius: 6px;
    padding: 20px 24px;
    margin-top: 12px;
  }
  .xlsx-callout-body { flex: 1; }
  .xlsx-callout-title {
    font-size: 14px;
    font-weight: 700;
    color: #16305a;
    margin-bottom: 6px;
  }
  .xlsx-callout-sub {
    font-size: 12px;
    color: #4b5563;
    line-height: 1.6;
    margin-bottom: 14px;
  }
  .xlsx-callout-btn {
    background: #16305a;
    border: none;
    color: #c9a227;
    padding: 8px 18px;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    cursor: pointer;
    border-radius: 4px;
    white-space: nowrap;
  }
  .xlsx-callout-btn:hover { background: #c9a227; color: #0a1628; }
"""


# ── XLSX payload builder ───────────────────────────────────────────────────────

from mini_bloomberg.data.equity_quarterly import _IS_DISPLAY


def _build_xlsx_payload(d: dict) -> str:
    """
    Build the JSON string embedded in the HTML for the SheetJS XLSX download.
    Layout: 4 fiscal years × (Q1|Q2|Q3|Q4|Annual) = 20 data columns per sheet.
    """
    sym       = d.get("symbol", "")
    fin       = d.get("financials") or {}
    quarterly = d.get("quarterly") or {}

    # ── Determine the 4 fiscal years to show (oldest → newest) ────────────────
    ann_is = fin.get("income_statements") or []
    years: list[str] = sorted({r.get("fiscal_year", "") for r in ann_is if r.get("fiscal_year")})
    years = years[-4:]  # keep most recent 4

    # ── Annual lookup: {sheet: {year: {display_name: value}}} ─────────────────
    def _ann_map(rows, name_map: dict[str, str]) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for r in rows:
            fy = r.get("fiscal_year", "")
            if not fy:
                continue
            out[fy] = {disp: r.get(field) for field, disp in name_map.items()}
        return out

    # field-name → display-name maps matching the annual Pydantic schema fields
    _ANN_IS_MAP = {
        "revenue":                       "Total Revenue",
        "cost_of_revenue":               "Cost of Revenue",
        "gross_profit":                  "Gross Profit",
        "rd_expenses":                   "R&D Expenses",
        "sga_expenses":                  "SG&A Expenses",
        "operating_expenses":            "Total Operating Expenses",
        "operating_income":              "Operating Income",
        "ebitda":                        "EBITDA",
        "ebit":                          "EBIT",
        "net_income":                    "Net Income",
        "eps":                           "EPS (Basic)",
        "eps_diluted":                   "EPS (Diluted)",
        "weighted_avg_shares":           "Shares Outstanding (Basic)",
        "weighted_avg_shares_diluted":   "Shares Outstanding (Diluted)",
        "depreciation_and_amortization": "D&A",
        "income_tax_expense":            "Income Tax Expense",
    }
    _ANN_BS_MAP = {
        "cash_and_equivalents":          "Cash & Equivalents",
        "short_term_investments":        "ST Investments",
        "net_receivables":               "Accounts Receivable",
        "inventory":                     "Inventory",
        "total_current_assets":          "Total Current Assets",
        "total_assets":                  "Total Assets",
        "accounts_payable":              "Accounts Payable",
        "short_term_debt":               "ST Debt",
        "total_current_liabilities":     "Total Current Liabilities",
        "long_term_debt":                "Long-Term Debt",
        "total_non_current_liabilities": "Total Non-Current Liabilities",
        "total_liabilities":             "Total Liabilities",
        "total_stockholders_equity":     "Total Stockholders Equity",
        "retained_earnings":             "Retained Earnings",
        "total_debt":                    "Total Debt",
        "net_debt":                      "Net Debt",
        "goodwill":                      "Goodwill & Intangibles",
    }
    _ANN_CF_MAP = {
        "net_income":                "Net Income",
        "depreciation_and_amortization": "D&A",
        "stock_based_compensation":  "Stock-Based Compensation",
        "change_in_working_capital": "Change in Working Capital",
        "operating_cash_flow":       "Cash Flow from Operations",
        "capital_expenditure":       "Capital Expenditures",
        "free_cash_flow":            "Free Cash Flow",
        "net_investing_activities":  "Cash Flow from Investing",
        "dividends_paid":            "Dividends Paid",
        "common_stock_repurchased":  "Share Buybacks",
        "net_financing_activities":  "Cash Flow from Financing",
        "net_change_in_cash":        "Net Change in Cash",
    }

    annual_is  = _ann_map(fin.get("income_statements") or [], _ANN_IS_MAP)
    annual_bs  = _ann_map(fin.get("balance_sheets")    or [], _ANN_BS_MAP)
    annual_cf  = _ann_map(fin.get("cash_flows")        or [], _ANN_CF_MAP)

    # ── Quarterly lookup: {sheet: {year: {quarter: {display_name: value}}}} ───
    def _qtr_map(periods: list[dict]) -> dict[str, dict[str, dict]]:
        out: dict[str, dict[str, dict]] = {}
        for p in periods:
            fy = p.get("fiscal_year", "")
            q  = p.get("quarter", "")
            if not fy or not q:
                continue
            out.setdefault(fy, {})[q] = p.get("fields") or {}
        return out

    q_is  = _qtr_map((quarterly.get("income")   or []))
    q_bs  = _qtr_map((quarterly.get("balance")  or []))
    q_cf  = _qtr_map((quarterly.get("cashflow") or []))

    # ── Extend years to include fiscal years only in quarterly data ───────────
    # e.g. Lenovo FY2026 Q2 exists in quarterly but not yet in annual
    q_all_years: set[str] = set()
    for qmap in (q_is, q_bs, q_cf):
        q_all_years.update(fy for fy in qmap if fy)
    years = sorted(set(years) | q_all_years)[-4:]

    # ── Derive Q4 IS from Annual − Q1 − Q2 − Q3 ──────────────────────────────
    # SEC doesn't file Q4 standalone for income/expense items; derive it here
    # where we have access to both annual and quarterly data.
    for fy in years:
        fy_qtr = q_is.get(fy, {})
        if "Q4" not in fy_qtr and all(q in fy_qtr for q in ("Q1", "Q2", "Q3")):
            ann_fy = annual_is.get(fy, {})
            if ann_fy:
                q4 = {}
                for field in _IS_DISPLAY:
                    q1v = fy_qtr["Q1"].get(field)
                    q2v = fy_qtr["Q2"].get(field)
                    q3v = fy_qtr["Q3"].get(field)
                    annv = ann_fy.get(field)
                    if q1v is not None and q2v is not None and q3v is not None and annv is not None:
                        q4[field] = annv - q1v - q2v - q3v
                    else:
                        q4[field] = None
                q_is.setdefault(fy, {})["Q4"] = q4

    # ── Margin / ratio helpers ────────────────────────────────────────────────
    def _pct100(num, denom) -> Optional[float]:
        """Return num/denom × 100, rounded to 2 dp; None if either is falsy."""
        if num is None or not denom:
            return None
        return round(num / denom * 100, 2)

    def _add_is_margins(data: dict) -> dict:
        """Inject margin % rows into an IS data dict (display_name → value)."""
        rev = data.get("Total Revenue")
        out = dict(data)
        out["Gross Margin %"]     = _pct100(data.get("Gross Profit"),       rev)
        out["R&D % of Revenue"]   = _pct100(data.get("R&D Expenses"),       rev)
        out["SG&A % of Revenue"]  = _pct100(data.get("SG&A Expenses"),      rev)
        out["Operating Margin %"] = _pct100(data.get("Operating Income"),    rev)
        out["EBITDA Margin %"]    = _pct100(data.get("EBITDA"),              rev)
        out["Net Margin %"]       = _pct100(data.get("Net Income"),          rev)
        return out

    def _add_cf_ratios(data: dict, revenue) -> dict:
        """Inject % of revenue rows into a CF data dict."""
        out = dict(data)
        out["CFO % of Revenue"]   = _pct100(data.get("Cash Flow from Operations"), revenue)
        out["CapEx % of Revenue"] = _pct100(data.get("Capital Expenditures"),      revenue)
        out["FCF % of Revenue"]   = _pct100(data.get("Free Cash Flow"),            revenue)
        return out

    def _add_bs_ratios(data: dict, revenue) -> dict:
        """Inject % of revenue rows into a BS data dict."""
        out = dict(data)
        out["A/R % of Revenue"]        = _pct100(data.get("Accounts Receivable"),    revenue)
        out["Inventory % of Revenue"]  = _pct100(data.get("Inventory"),              revenue)
        out["A/P % of Revenue"]        = _pct100(data.get("Accounts Payable"),       revenue)
        return out

    # Apply margin rows to annual data
    annual_is_m = {fy: _add_is_margins(v)                             for fy, v in annual_is.items()}
    annual_cf_m = {fy: _add_cf_ratios(v, annual_is.get(fy, {}).get("Total Revenue"))
                   for fy, v in annual_cf.items()}
    annual_bs_m = {fy: _add_bs_ratios(v, annual_is.get(fy, {}).get("Total Revenue"))
                   for fy, v in annual_bs.items()}

    # Apply margin rows to quarterly data
    def _enrich_qtr_is(qtr_map: dict) -> dict:
        out: dict[str, dict[str, dict]] = {}
        for fy, fy_data in qtr_map.items():
            out[fy] = {}
            for q, q_data in fy_data.items():
                out[fy][q] = _add_is_margins(q_data)
        return out

    def _enrich_qtr_cf(qtr_map: dict, is_qtr: dict) -> dict:
        out: dict[str, dict[str, dict]] = {}
        for fy, fy_data in qtr_map.items():
            out[fy] = {}
            for q, q_data in fy_data.items():
                rev = is_qtr.get(fy, {}).get(q, {}).get("Total Revenue")
                out[fy][q] = _add_cf_ratios(q_data, rev)
        return out

    def _enrich_qtr_bs(qtr_map: dict, is_qtr: dict) -> dict:
        out: dict[str, dict[str, dict]] = {}
        for fy, fy_data in qtr_map.items():
            out[fy] = {}
            for q, q_data in fy_data.items():
                rev = is_qtr.get(fy, {}).get(q, {}).get("Total Revenue")
                out[fy][q] = _add_bs_ratios(q_data, rev)
        return out

    q_is_e = _enrich_qtr_is(q_is)
    q_cf_e = _enrich_qtr_cf(q_cf, q_is)
    q_bs_e = _enrich_qtr_bs(q_bs, q_is)

    # ── Section templates: ("kind", label/section_name) ──────────────────────
    # Kinds:
    #   "header"     → § section header row (no data)
    #   "ai_section" → slot filled by AI-classified rows for that section name
    #   "subtotal"   → Σ row: always included, JS looks up key = label minus "Σ "
    #   "metric"     → computed row (margins etc.) included if data exists

    _IS_TEMPLATE = [
        ("header",     "§ Revenue"),
        ("ai_section", "Revenue"),
        ("header",     "§ Cost of Revenue"),
        ("ai_section", "Cost of Revenue"),
        ("subtotal",   "Σ Gross Profit"),
        ("metric",     "Gross Margin %"),
        ("header",     "§ Operating Expenses"),
        ("ai_section", "Operating Expenses"),
        ("metric",     "R&D % of Revenue"),
        ("metric",     "SG&A % of Revenue"),
        ("subtotal",   "Σ Operating Income"),
        ("metric",     "EBITDA"),
        ("metric",     "EBITDA Margin %"),
        ("metric",     "Operating Margin %"),
        ("header",     "§ Non-Operating Items"),
        ("ai_section", "Non-Operating Items"),
        ("header",     "§ Income Tax"),
        ("ai_section", "Income Tax"),
        ("subtotal",   "Σ Net Income"),
        ("metric",     "Net Margin %"),
        ("header",     "§ Per Share Data"),
        ("ai_section", "Per Share Data"),
    ]

    _BS_TEMPLATE = [
        ("header",     "§ ASSETS"),
        ("header",     "§ Current Assets"),
        ("ai_section", "Current Assets"),
        ("metric",     "A/R % of Revenue"),
        ("metric",     "Inventory % of Revenue"),
        ("subtotal",   "Σ Total Current Assets"),
        ("header",     "§ Non-Current Assets"),
        ("ai_section", "Non-Current Assets"),
        ("subtotal",   "Σ Total Assets"),
        ("header",     "§ LIABILITIES"),
        ("header",     "§ Current Liabilities"),
        ("ai_section", "Current Liabilities"),
        ("metric",     "A/P % of Revenue"),
        ("subtotal",   "Σ Total Current Liabilities"),
        ("header",     "§ Non-Current Liabilities"),
        ("ai_section", "Non-Current Liabilities"),
        ("subtotal",   "Σ Total Non-Current Liabilities"),
        ("subtotal",   "Σ Total Liabilities"),
        ("header",     "§ SHAREHOLDERS' EQUITY"),
        ("header",     "§ Contributed Capital"),
        ("ai_section", "Contributed Capital"),
        ("header",     "§ Earned Capital"),
        ("ai_section", "Earned Capital"),
        ("header",     "§ Other Equity Items"),
        ("ai_section", "Other Equity Items"),
        ("subtotal",   "Σ Total Stockholders Equity"),
    ]

    _CF_TEMPLATE = [
        ("header",     "§ Operating Activities"),
        ("ai_section", "Operating Activities"),
        ("subtotal",   "Σ Cash Flow from Operations"),
        ("metric",     "CFO % of Revenue"),
        ("header",     "§ Investing Activities"),
        ("ai_section", "Investing Activities"),
        ("metric",     "CapEx % of Revenue"),
        ("subtotal",   "Σ Cash Flow from Investing"),
        ("header",     "§ Free Cash Flow"),
        ("ai_section", "Free Cash Flow"),
        ("metric",     "FCF % of Revenue"),
        ("header",     "§ Financing Activities"),
        ("ai_section", "Financing Activities"),
        ("subtotal",   "Σ Cash Flow from Financing"),
        ("subtotal",   "Σ Net Change in Cash"),
    ]

    # ── Re-key quarterly data stripping "~" prefix ────────────────────────────
    def _strip_tilde(qtr_map: dict) -> dict:
        out: dict[str, dict[str, dict]] = {}
        for fy, fy_data in qtr_map.items():
            out[fy] = {}
            for q, q_data in fy_data.items():
                out[fy][q] = {(k[1:] if k.startswith("~") else k): v for k, v in q_data.items()}
        return out

    # Strip tilde once; reuse for both row building and the payload
    q_is_s = _strip_tilde(q_is_e)
    q_bs_s = _strip_tilde(q_bs_e)
    q_cf_s = _strip_tilde(q_cf_e)

    def _any_data(key: str, annual: dict, quarterly: dict) -> bool:
        """True if the row has at least one non-None value in annual or quarterly."""
        if any(v is not None for fy_d in annual.values() for k, v in fy_d.items() if k == key):
            return True
        for fy_d in quarterly.values():
            for q_d in fy_d.values():
                if q_d.get(key) is not None:
                    return True
        return False

    def _build_rows(template: list, classification: dict, annual: dict, quarterly: dict) -> list[str]:
        """Build ordered rows list from template + AI classification.
        Data rows with no values in annual or quarterly are silently dropped."""
        by_section: dict[str, list[str]] = {}
        for row_name, section in classification.items():
            by_section.setdefault(section, []).append(row_name)

        rows: list[str] = []
        for item in template:
            kind, label = item[0], item[1]
            if kind == "header":
                rows.append(label)
            elif kind == "ai_section":
                for row in by_section.get(label, []):
                    if _any_data(row, annual, quarterly):
                        rows.append(row)
            elif kind == "subtotal":
                rows.append(label)
            elif kind == "metric":
                if _any_data(label, annual, quarterly):
                    rows.append(label)
        return rows

    # ── Build rows using AI classification ────────────────────────────────────
    classification = d.get("financial_row_classification") or {}
    is_cls = classification.get("IS") or {}
    bs_cls = classification.get("BS") or {}
    cf_cls = classification.get("CF") or {}

    # Default classification used when AI call failed or returned nothing
    _DEFAULT_IS_CLS: dict[str, str] = {
        "Total Revenue": "Revenue", "Net Revenue": "Revenue", "Net Sales": "Revenue",
        "Cost of Revenue": "Cost of Revenue", "Cost of Goods Sold": "Cost of Revenue",
        "R&D Expenses": "Operating Expenses", "SG&A Expenses": "Operating Expenses",
        "Total Operating Expenses": "Operating Expenses", "D&A": "Operating Expenses",
        "EBIT": "Operating Expenses",
        "Interest Income": "Non-Operating Items", "Interest Expense": "Non-Operating Items",
        "Income Tax Expense": "Income Tax",
        "Pretax Income": "Non-Operating Items",
        "EPS (Basic)": "Per Share Data", "EPS (Diluted)": "Per Share Data",
        "Shares Outstanding (Basic)": "Per Share Data",
        "Shares Outstanding (Diluted)": "Per Share Data",
    }
    _DEFAULT_BS_CLS: dict[str, str] = {
        "Cash & Equivalents": "Current Assets", "ST Investments": "Current Assets",
        "Cash & ST Investments": "Current Assets", "Accounts Receivable": "Current Assets",
        "Inventory": "Current Assets",
        "Net PPE": "Non-Current Assets", "Goodwill & Intangibles": "Non-Current Assets",
        "Long-Term Investments": "Non-Current Assets",
        "Accounts Payable": "Current Liabilities", "ST Debt": "Current Liabilities",
        "Long-Term Debt": "Non-Current Liabilities",
        "Total Debt": "Non-Current Liabilities", "Net Debt": "Non-Current Liabilities",
        "Retained Earnings": "Earned Capital",
    }
    _DEFAULT_CF_CLS: dict[str, str] = {
        "Net Income": "Operating Activities", "D&A": "Operating Activities",
        "Stock-Based Compensation": "Operating Activities",
        "Change in Working Capital": "Operating Activities",
        "Capital Expenditures": "Investing Activities",
        "Free Cash Flow": "Free Cash Flow",
        "Dividends Paid": "Financing Activities", "Share Buybacks": "Financing Activities",
        "Ending Cash": "Financing Activities",
    }

    is_cls = is_cls or _DEFAULT_IS_CLS
    bs_cls = bs_cls or _DEFAULT_BS_CLS
    cf_cls = cf_cls or _DEFAULT_CF_CLS

    is_rows_built = _build_rows(_IS_TEMPLATE, is_cls, annual_is_m, q_is_s)
    bs_rows_built = _build_rows(_BS_TEMPLATE, bs_cls, annual_bs_m, q_bs_s)
    cf_rows_built = _build_rows(_CF_TEMPLATE, cf_cls, annual_cf_m, q_cf_s)

    payload = {
        "symbol":    sym,
        "years":     years,
        "annual":    {"IS": annual_is_m, "BS": annual_bs_m, "CF": annual_cf_m},
        "quarterly": {
            "IS": q_is_s,
            "BS": q_bs_s,
            "CF": q_cf_s,
        },
        "rows": {
            "IS": is_rows_built,
            "BS": bs_rows_built,
            "CF": cf_rows_built,
        },
    }
    return json.dumps(payload, default=str)


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

    # ── Trading metrics ────────────────────────────────────────────────────────
    tm      = d.get("trading_metrics") or {}
    high_52 = tm.get("high_52w")
    low_52  = tm.get("low_52w")
    range_52w_str = f"{_p(low_52, currency)} – {_p(high_52, currency)}" if (high_52 and low_52) else "N/A"
    avg_vol   = tm.get("avg_daily_volume")
    avg_vol_str = f"{avg_vol:,.0f}" if avg_vol else "N/A"
    avg_val   = tm.get("avg_daily_value")
    avg_val_str = _n(avg_val, currency) if avg_val else "N/A"
    float_shares = prof.get("shares_float")
    float_pct    = (float_shares / prof.get("shares_outstanding") * 100
                    if float_shares and prof.get("shares_outstanding") else None)
    float_pct_str = f"{float_pct:.0f}%" if float_pct else "N/A"
    latest_ratio = rlist[0] if rlist else {}

    # ── Insights text ──────────────────────────────────────────────────────────
    ins = d.get("insights") or {}
    what_happened_html = _e(ins.get("what_happened") or "No recent news data available.")
    our_thoughts_raw   = ins.get("our_thoughts") or "<p>Analysis not available.</p>"

    # ── Assemble HTML ──────────────────────────────────────────────────────────
    subtitle_parts = [s for s in [sector, exchange, currency] if s]
    subtitle = " &nbsp;·&nbsp; ".join(_e(p) for p in subtitle_parts)

    rating_pill_html = (
        f'<span class="rating-pill" style="background:{rating_color};border:1px solid {rating_color}">'
        f'{_e(rating_raw)}'
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
    xlsx_payload = _build_xlsx_payload(d)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_e(name)} ({_e(sym)}) — Equity Report</title>
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script>{_XLSX_JS_INLINE}</script>
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

  <!-- §2 Insights -->
  <div class="section">
    {_section(2, "Insights", "Market Intelligence · Analyst View")}
    <div class="insights-grid">
      <!-- LEFT: What happened + Our thoughts -->
      <div class="insights-left">
        <div>
          <div class="insights-block-title">What happened?</div>
          <div class="insights-text"><p>{what_happened_html}</p></div>
        </div>
        <div>
          <div class="insights-block-title">Our thoughts</div>
          <div class="insights-text">{our_thoughts_raw}</div>
        </div>
      </div>
      <!-- RIGHT: Compact analyst consensus + Trading data -->
      <div class="insights-right">
        <div>
          <div class="insights-block-title">Analyst Consensus</div>
          <div class="ins-anl-rating">
            <span class="ins-anl-pill" style="background:{rating_color}">{_e(rating_raw) if rating_raw else "N/A"}</span>
            <span class="ins-anl-target">{_p(target, currency)}</span>
            <span class="ins-anl-upside {'pos' if (target and cur_price and target > cur_price) else 'neg' if (target and cur_price) else ''}">{
              f'+{(target - cur_price) / cur_price * 100:.1f}%' if target and cur_price and target > cur_price
              else f'{(target - cur_price) / cur_price * 100:.1f}%' if target and cur_price
              else ''
            }</span>
          </div>
          <table class="ins-anl-table">
            <tr><td># Analysts</td><td>{anl.get("num_analysts") or "N/A"}</td></tr>
            <tr><td>Target High</td><td>{_p(pt.get("target_high"), currency)}</td></tr>
            <tr><td>Target Low</td><td>{_p(pt.get("target_low"), currency)}</td></tr>
            <tr><td>Target Mean</td><td>{_p(pt.get("target_consensus"), currency)}</td></tr>
            <tr><td>Current Price</td><td>{_p(cur_price, currency)}</td></tr>
          </table>
        </div>
        <div>
          <div class="insights-block-title">Trading Data &amp; Key Metrics</div>
          <table class="trading-table">
            <tr><td>52-Wk Range</td><td>{range_52w_str}</td></tr>
            <tr><td>Market Cap</td><td>{_n(val.get("market_cap"), currency)}</td></tr>
            <tr><td>Shares O/S</td><td>{_n(prof.get("shares_outstanding"))}</td></tr>
            <tr><td>Free Float</td><td>{float_pct_str}</td></tr>
            <tr><td>Avg Daily Vol</td><td>{avg_vol_str}</td></tr>
            <tr><td>Avg Daily Value</td><td>{avg_val_str}</td></tr>
            <tr><td>Beta</td><td>{f"{prof['beta']:.2f}" if prof.get("beta") is not None else "N/A"}</td></tr>
            <tr><td>Div Yield</td><td>{_pct_raw(val.get("dividend_yield"))}</td></tr>
            <tr><td>P / BV</td><td>{_x(val.get("pb_ratio"))}</td></tr>
            <tr><td>Net Debt / EBITDA</td><td>{_x(latest_ratio.get("net_debt_to_ebitda"))}</td></tr>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- §3 Financial Statements -->
  <div class="section">
    {_section(3, "Financial Statements", "Income Statement · Balance Sheet · Cash Flow")}
    <div class="xlsx-callout">
      <div class="xlsx-callout-body">
        <div class="xlsx-callout-title">Quarterly &amp; Annual Financials</div>
        <div class="xlsx-callout-sub">
          Full IS / BS / CF breakdowns — Q1 through Q4 plus annual totals for each fiscal year,
          with margin rows and section groupings. All figures in millions except per-share data.
        </div>
        <button class="xlsx-callout-btn" onclick="downloadXLSX()">&#8675;&nbsp; Download Financial Reports in XLSX</button>
      </div>
    </div>
  </div>

  <!-- §4 Financial Ratios -->
  <div class="section">
    {_section(4, "Financial Ratios")}
    {_ratio_table()}
  </div>

  <!-- §5 Valuation Multiples -->
  <div class="section">
    {_section(5, "Valuation Multiples", f"As of {date_display}")}
    <div class="val-grid">{val_cards_html}</div>
  </div>

  <!-- §6 Peer Comparison -->
  <div class="section">
    {_section(6, "Peer Comparison")}
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

<script type="application/json" id="xlsx-data">{xlsx_payload}</script>
<script>
function downloadXLSX() {{
  if (typeof XLSX === 'undefined') {{
    alert('Excel library failed to load. Check browser console or internet connection.');
    return;
  }}
  var raw;
  try {{
    raw = JSON.parse(document.getElementById('xlsx-data').textContent);
  }} catch(e) {{
    alert('XLSX data error: ' + e.message); return;
  }}
  try {{
    var wb = XLSX.utils.book_new();
    ['IS','BS','CF'].forEach(function(sheet) {{
      XLSX.utils.book_append_sheet(wb, buildSheet(raw, sheet), sheet);
    }});
    XLSX.writeFile(wb, raw.symbol + '_financials.xlsx');
  }} catch(e) {{
    alert('Build error: ' + e.message + ' | ' + (e.stack || ''));
  }}
}}

function buildSheet(raw, sheet) {{
  var years  = raw.years || [];
  var allRows = ((raw.rows || {{}})[sheet]) || [];
  var annual = ((raw.annual    || {{}})[sheet]) || {{}};
  var qdata  = ((raw.quarterly || {{}})[sheet]) || {{}};

  // ── Borders ────────────────────────────────────────────────────────────────
  // White border used as "no-border" on every cell so Excel default gridlines
  // are overridden (showGridLines is not supported by this library build).
  var W    = {{style:"thin",  color:{{rgb:"FFFFFF"}}}};  // invisible
  var THIN = {{style:"thin",  color:{{rgb:"AAAAAA"}}}};  // visible separator
  var MED  = {{style:"medium",color:{{rgb:"888888"}}}};  // column divider
  var NO_BORD = {{top:W, bottom:W, left:W, right:W}};

  function withBorder(s, extra) {{
    var b = Object.assign({{}}, NO_BORD, (s && s.border) || {{}}, extra);
    return Object.assign({{}}, s || {{}}, {{border: b}});
  }}
  function labelRight(s) {{ return withBorder(s, {{right: MED}}); }}
  function annRight(s)   {{ return withBorder(s, {{right: MED}}); }}
  function hBottom(s)    {{ return withBorder(s, {{bottom: THIN}}); }}
  function hTop(s)       {{ return withBorder(s, {{top: THIN}}); }}
  function hTopBottom(s) {{ return hTop(hBottom(s)); }}

  var ANN_FILL = {{fill:{{fgColor:{{rgb:"F0F0F0"}}}}}};

  var ST = {{
    title:   {{font:{{bold:true, sz:13}}}},
    units:   {{font:{{italic:true, sz:9, color:{{rgb:"666666"}}}}}},
    yearHdr: {{font:{{bold:true,sz:11}}, alignment:{{horizontal:"center"}}, fill:{{fgColor:{{rgb:"D8E4F0"}}}}}},
    qHdr:    {{font:{{bold:true}},       alignment:{{horizontal:"center"}}}},
    annHdr:  {{font:{{bold:true}},       alignment:{{horizontal:"center"}}, fill:{{fgColor:{{rgb:"F0F0F0"}}}}}},
    major:   {{font:{{bold:true,sz:11}}, fill:{{fgColor:{{rgb:"D9D9D9"}}}}}},
    sub:     {{font:{{bold:true,sz:10}}, fill:{{fgColor:{{rgb:"F2F2F2"}}}}}},
    total:   {{font:{{bold:true}}}},
    pct:     {{font:{{color:{{rgb:"666666"}}, italic:true}}}},
    data:    {{}},
    empty:   {{}},
  }};

  var SHEET_TITLES = {{IS:"Income Statement", BS:"Balance Sheet", CF:"Statement of Cash Flows"}};
  var NO_MIL_KEYS  = ["EPS (Basic)", "EPS (Diluted)"];

  function toMil(key, v) {{
    if (v === null || v === undefined || v === '') return v;
    if (typeof v !== 'number') return v;
    if (key.indexOf('%') !== -1) return v;
    if (NO_MIL_KEYS.indexOf(key) !== -1) return v;
    return Math.round(v / 1e6 * 10) / 10;
  }}

  var ws = {{}};
  var nCols = 1 + years.length * 5;
  var rowNum = 0;

  function toCol(c) {{
    var s = ''; c += 1;
    while (c > 0) {{
      var r = (c - 1) % 26;
      s = String.fromCharCode(65 + r) + s;
      c = Math.floor((c - 1) / 26);
    }}
    return s;
  }}

  function sc(r, c, v, t, sty) {{
    ws[toCol(c) + (r + 1)] = {{v: v, t: t || 's', s: sty || {{}}}};
  }}

  function fillRow(r, sty) {{
    for (var c = 0; c < nCols; c++) {{ sc(r, c, '', 's', sty); }}
  }}

  ws['!merges'] = [];

  // ── Title row 1: sheet name ───────────────────────────────────────────────
  sc(rowNum, 0, SHEET_TITLES[sheet] || sheet, 's', withBorder(ST.title, {{right:W}}));
  for (var c = 1; c < nCols; c++) {{ sc(rowNum, c, '', 's', withBorder(ST.empty, {{}})); }}
  ws['!merges'].push({{s:{{r:rowNum,c:0}}, e:{{r:rowNum,c:nCols-1}}}});
  rowNum++;

  // ── Title row 2: units note ───────────────────────────────────────────────
  sc(rowNum, 0, 'In millions, except EPS', 's', withBorder(ST.units, {{right:W}}));
  for (var c = 1; c < nCols; c++) {{ sc(rowNum, c, '', 's', withBorder(ST.empty, {{}})); }}
  ws['!merges'].push({{s:{{r:rowNum,c:0}}, e:{{r:rowNum,c:nCols-1}}}});
  rowNum++;

  // ── h1: year header row ───────────────────────────────────────────────────
  sc(rowNum, 0, '', 's', hBottom(labelRight(ST.empty)));
  years.forEach(function(y, i) {{
    var s = 1 + i * 5;
    sc(rowNum, s,   'FY' + y, 's', hBottom(ST.yearHdr));
    sc(rowNum, s+1, '',       's', hBottom(ST.yearHdr));
    sc(rowNum, s+2, '',       's', hBottom(ST.yearHdr));
    sc(rowNum, s+3, '',       's', hBottom(ST.yearHdr));
    sc(rowNum, s+4, '',       's', hBottom(annRight(ST.yearHdr)));
    ws['!merges'].push({{s:{{r:rowNum,c:s}}, e:{{r:rowNum,c:s+4}}}});
  }});
  rowNum++;

  // ── h2: quarter header row ────────────────────────────────────────────────
  sc(rowNum, 0, '', 's', hBottom(labelRight(ST.empty)));
  years.forEach(function(_, i) {{
    var s = 1 + i * 5;
    sc(rowNum, s,   'Q1',     's', hBottom(ST.qHdr));
    sc(rowNum, s+1, 'Q2',     's', hBottom(ST.qHdr));
    sc(rowNum, s+2, 'Q3',     's', hBottom(ST.qHdr));
    sc(rowNum, s+3, 'Q4',     's', hBottom(ST.qHdr));
    sc(rowNum, s+4, 'Annual', 's', hBottom(annRight(ST.annHdr)));
  }});
  rowNum++;

  // ── data rows ─────────────────────────────────────────────────────────────
  function pushRow(label) {{
    var key     = label.replace(/^[§Σ] /, '');
    var isSec   = label.charAt(0) === '§';
    var isTotal = label.charAt(0) === 'Σ';
    var isPct   = !isSec && !isTotal && label.indexOf('%') !== -1;

    var secST = ST.sub;
    if (isSec) {{
      var rest = label.slice(2);
      secST = (rest.toUpperCase() === rest) ? ST.major : ST.sub;
    }}

    var lStyle, dStyle, aStyle;
    if (isSec) {{
      lStyle = hTopBottom(labelRight(secST));
      dStyle = hTopBottom(secST);
      aStyle = hTopBottom(annRight(secST));
    }} else if (isTotal) {{
      lStyle = labelRight(hTopBottom(ST.total));
      dStyle = hTopBottom(ST.total);
      aStyle = annRight(hTopBottom(Object.assign({{}}, ST.total, ANN_FILL)));
    }} else if (isPct) {{
      lStyle = labelRight(ST.pct);
      dStyle = withBorder(ST.pct, {{}});
      aStyle = annRight(Object.assign({{}}, ST.pct, ANN_FILL));
    }} else {{
      lStyle = labelRight(ST.data);
      dStyle = withBorder(ST.data, {{}});
      aStyle = annRight(Object.assign({{}}, ST.data, ANN_FILL));
    }}

    sc(rowNum, 0, key, 's', lStyle);

    if (isSec) {{
      years.forEach(function(_, i) {{
        var s = 1 + i * 5;
        sc(rowNum, s,   '', 's', dStyle);
        sc(rowNum, s+1, '', 's', dStyle);
        sc(rowNum, s+2, '', 's', dStyle);
        sc(rowNum, s+3, '', 's', dStyle);
        sc(rowNum, s+4, '', 's', aStyle);
      }});
    }} else {{
      years.forEach(function(y, i) {{
        var s = 1 + i * 5;
        var qy = (qdata[y] || {{}});
        var ay = (annual[y] || {{}});
        ['Q1','Q2','Q3','Q4'].forEach(function(q, qi) {{
          var raw_v = ((qy[q] || {{}})[key]);
          var v = toMil(key, raw_v);
          if (v !== undefined && v !== null && v !== '') {{
            sc(rowNum, s + qi, v, 'n', dStyle);
          }} else {{
            sc(rowNum, s + qi, '', 's', dStyle);
          }}
        }});
        var raw_av = ay[key];
        var av = toMil(key, raw_av);
        if (av !== undefined && av !== null && av !== '') {{
          sc(rowNum, s + 4, av, 'n', aStyle);
        }} else {{
          sc(rowNum, s + 4, '', 's', aStyle);
        }}
      }});
    }}
    rowNum++;
  }}

  allRows.forEach(function(r) {{ pushRow(r); }});

  ws['!ref'] = 'A1:' + toCol(nCols - 1) + rowNum;

  var colWidths = [{{wch: 36}}];
  years.forEach(function() {{
    for (var i = 0; i < 5; i++) {{ colWidths.push({{wch: 13}}); }}
  }});
  ws['!cols'] = colWidths;
  ws['!freeze'] = {{xSplit:1, ySplit:4, topLeftCell:'B5'}};
  return ws;
}}
</script>
</body>
</html>"""

    _REPORTS_DIR.mkdir(exist_ok=True)
    filename = f"{sym}_{(gendt or '').replace('-', '')[:8]}.html"
    out_path = _REPORTS_DIR / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path
