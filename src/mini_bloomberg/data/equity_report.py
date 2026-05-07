"""
Aggregator for RPT: pulls all five data layers, computes ratios and valuation
multiples, and assembles an EquityReport in one call.
All underlying calls hit the disk cache, so repeated RPT/RV runs are instant.
"""

from datetime import date
from typing import Optional

from mini_bloomberg.core.ticker import Ticker
from mini_bloomberg.data.equity_estimates import get_analyst_ratings
from mini_bloomberg.data.equity_fundamentals import get_financials
from mini_bloomberg.data.equity_peers import get_comparables
from mini_bloomberg.data.equity_price import get_price_history
from mini_bloomberg.data.equity_profile import get_profile
from mini_bloomberg.data.schemas import (
    AnalystRatings, Comparables, EquityReport, Financials,
    FinancialRatios, ValuationMultiples,
)


def get_equity_report(ticker: Ticker, price_days: int = 90) -> EquityReport:
    report = EquityReport(
        symbol=ticker.symbol,
        generated_at=date.today().isoformat(),
    )

    # ── Profile ────────────────────────────────────────────────────────────────
    try:
        report.profile = get_profile(ticker)
    except Exception:
        pass

    # ── Financials ─────────────────────────────────────────────────────────────
    try:
        report.financials = get_financials(ticker, years=4)
    except Exception:
        pass

    # ── Analyst ratings ────────────────────────────────────────────────────────
    try:
        report.analyst = get_analyst_ratings(ticker)
    except Exception:
        report.analyst = AnalystRatings(symbol=ticker.symbol)

    # ── Comparables ────────────────────────────────────────────────────────────
    try:
        report.comparables = get_comparables(ticker)
    except Exception:
        report.comparables = Comparables(symbol=ticker.symbol, peers=[])

    # ── Latest price (for valuation multiples) ─────────────────────────────────
    latest_price: Optional[float] = None
    price_date: Optional[str] = None
    try:
        history = get_price_history(ticker, days=price_days)
        if history.bars:
            latest_price = history.bars[-1].close
            price_date = history.bars[-1].date
    except Exception:
        pass

    # ── Computed ratios ────────────────────────────────────────────────────────
    if report.financials:
        report.ratios_by_year = _compute_ratios(report.financials)

    # ── Valuation multiples ────────────────────────────────────────────────────
    if report.financials or report.profile:
        report.valuation = _compute_valuation(report, latest_price, price_date)

    return report


# ── Ratio computation ──────────────────────────────────────────────────────────

def _safe_div(a, b) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _compute_ratios(financials: Financials) -> list[FinancialRatios]:
    bal_by_year = {b.fiscal_year: b for b in financials.balance_sheets}
    cf_by_year  = {c.fiscal_year: c for c in financials.cash_flows}

    result = []
    for inc in financials.income_statements:
        yr = inc.fiscal_year
        b  = bal_by_year.get(yr)
        cf = cf_by_year.get(yr)

        r = FinancialRatios(fiscal_year=yr)
        r.gross_margin     = _safe_div(inc.gross_profit,     inc.revenue)
        r.operating_margin = _safe_div(inc.operating_income, inc.revenue)
        r.net_margin       = _safe_div(inc.net_income,       inc.revenue)
        r.ebitda_margin    = _safe_div(inc.ebitda,           inc.revenue)

        if b:
            r.roe              = _safe_div(inc.net_income,           b.total_equity)
            r.roa              = _safe_div(inc.net_income,           b.total_assets)
            r.debt_to_equity   = _safe_div(b.total_debt,             b.total_equity)
            r.net_debt_to_ebitda = _safe_div(b.net_debt,            inc.ebitda)
            r.current_ratio    = _safe_div(b.total_current_assets,   b.total_current_liabilities)
            r.asset_turnover   = _safe_div(inc.revenue,              b.total_assets)

        if cf:
            r.fcf_margin = _safe_div(cf.free_cash_flow, inc.revenue)

        result.append(r)
    return result


# ── Valuation multiples ────────────────────────────────────────────────────────

def _compute_valuation(
    report: EquityReport,
    latest_price: Optional[float],
    price_date: Optional[str],
) -> ValuationMultiples:
    v = ValuationMultiples(current_price=latest_price, price_date=price_date)

    # Market cap — prefer profile (already computed by yfinance in trading currency)
    mktcap = report.profile.market_cap if report.profile else None
    v.market_cap = mktcap
    v.dividend_yield = report.profile.dividend_yield if report.profile else None

    fin = report.financials
    if not fin or not fin.income_statements:
        return v

    inc = fin.income_statements[0]   # latest year
    bal = fin.balance_sheets[0]      if fin.balance_sheets  else None
    cf  = fin.cash_flows[0]          if fin.cash_flows       else None

    # Enterprise value = market_cap + net_debt
    net_debt = bal.net_debt if bal else None
    if mktcap is not None and net_debt is not None:
        v.enterprise_value = int(mktcap + net_debt)

    ev = v.enterprise_value

    # P/E = price / eps_diluted
    if latest_price and inc.eps_diluted and inc.eps_diluted != 0:
        v.pe_ratio = round(latest_price / inc.eps_diluted, 2)

    # P/B = market_cap / total_equity
    if mktcap and bal and bal.total_equity and bal.total_equity != 0:
        v.pb_ratio = round(mktcap / bal.total_equity, 2)

    # EV/EBITDA
    if ev and inc.ebitda and inc.ebitda != 0:
        v.ev_to_ebitda = round(ev / inc.ebitda, 2)

    # EV/Sales
    if ev and inc.revenue and inc.revenue != 0:
        v.ev_to_sales = round(ev / inc.revenue, 2)

    # FCF yield = FCF / market_cap
    if cf and cf.free_cash_flow and mktcap and mktcap != 0:
        v.fcf_yield = round(cf.free_cash_flow / mktcap, 4)

    return v
