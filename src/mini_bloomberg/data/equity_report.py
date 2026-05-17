"""
Aggregator for RPT: pulls all five data layers, computes ratios and valuation
multiples, and assembles an EquityReport in one call.
All underlying calls hit the disk cache, so repeated RPT/RV runs are instant.
"""

import json
from datetime import date
from typing import Optional

from mini_bloomberg.core.cache import _cache as _disk_cache
from mini_bloomberg.core.llm import _get_client
from mini_bloomberg.core.ticker import Ticker
from mini_bloomberg.data.equity_classification import classify_financial_rows
from mini_bloomberg.data.equity_estimates import get_analyst_ratings
from mini_bloomberg.data.equity_fundamentals import get_financials
from mini_bloomberg.data.equity_news import fetch_company_news
from mini_bloomberg.data.equity_peers import get_comparables
from mini_bloomberg.data.equity_price import get_price_history
from mini_bloomberg.data.equity_profile import get_profile
from mini_bloomberg.data.equity_quarterly import get_quarterly_financials
from mini_bloomberg.data.schemas import (
    AnalystRatings, Comparables, EquityReport, Financials,
    FinancialRatios, InsightsData, ValuationMultiples,
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

    # ── Quarterly data (for XLSX download) ────────────────────────────────────
    try:
        report.quarterly = get_quarterly_financials(ticker)
    except Exception:
        pass  # quarterly is optional; RPT renders fine without it

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

    # ── Latest price + trading metrics ────────────────────────────────────────
    latest_price: Optional[float] = None
    price_date: Optional[str] = None
    try:
        history = get_price_history(ticker, days=365)
        if history.bars:
            latest_price = history.bars[-1].close
            price_date = history.bars[-1].date
            report.trading_metrics = _compute_trading_metrics(history.bars)
    except Exception:
        pass

    # ── Computed ratios ────────────────────────────────────────────────────────
    if report.financials:
        report.ratios_by_year = _compute_ratios(report.financials)

    # ── Valuation multiples ────────────────────────────────────────────────────
    if report.financials or report.profile:
        report.valuation = _compute_valuation(report, latest_price, price_date)

    # ── AI Insights ────────────────────────────────────────────────────────────
    try:
        news = fetch_company_news(ticker)
        report.insights = _generate_insights(ticker, news, report.financials, report.analyst)
    except Exception:
        pass

    # ── AI row classification (for XLSX structure) ─────────────────────────────
    try:
        extra_is, extra_bs, extra_cf = _extra_quarterly_rows(report.quarterly)
        report.financial_row_classification = classify_financial_rows(
            ticker, extra_is, extra_bs, extra_cf
        )
    except Exception:
        pass

    return report


def _extra_quarterly_rows(quarterly) -> tuple[list[str], list[str], list[str]]:
    """Extract company-specific (~-prefixed) row names from quarterly data."""
    def _extract(periods) -> list[str]:
        seen: dict[str, None] = {}
        for p in (periods or []):
            fields = p.fields if hasattr(p, "fields") else {}
            for k in fields:
                if k.startswith("~"):
                    seen[k[1:]] = None
        return list(seen)

    if quarterly is None:
        return [], [], []
    return (
        _extract(quarterly.income),
        _extract(quarterly.balance),
        _extract(quarterly.cashflow),
    )


# ── Trading metrics ────────────────────────────────────────────────────────────

def _compute_trading_metrics(bars: list) -> dict:
    """Derive 52-week metrics from price history bars."""
    if not bars:
        return {}
    highs   = [b.high   for b in bars if b.high   is not None]
    lows    = [b.low    for b in bars if b.low    is not None]
    closes  = [b.close  for b in bars if b.close  is not None]
    volumes = [b.volume for b in bars if b.volume is not None]
    avg_vol = int(sum(volumes) / len(volumes)) if volumes else None
    avg_val = None
    if closes and volumes and len(closes) == len(volumes):
        avg_val = sum(c * v for c, v in zip(closes, volumes)) / len(closes)
    return {
        "high_52w":         max(highs)   if highs   else None,
        "low_52w":          min(lows)    if lows    else None,
        "avg_daily_volume": avg_vol,
        "avg_daily_value":  avg_val,
    }


# ── AI Insights ────────────────────────────────────────────────────────────────

def _generate_insights(
    ticker: Ticker,
    news: list[dict],
    fin: Optional[Financials],
    analyst,
) -> InsightsData:
    """Call Claude (Haiku) to generate What happened? + Our thoughts. Cached 24 h."""
    cache_key = f"insights:{ticker.symbol}:{ticker.exchange_code}:{date.today()}"
    cached = _disk_cache.get(cache_key)
    if isinstance(cached, dict):
        return InsightsData(**cached)

    headlines = [f"[{n['date']}] {n['title']}" for n in news if n.get("title")]
    news_text = "\n".join(headlines) or "No recent news available."

    fin_summary = ""
    if fin and fin.income_statements:
        for r in fin.income_statements[:2]:
            fin_summary += (
                f"FY{r.fiscal_year}: revenue={r.revenue}, "
                f"net_income={r.net_income}, "
                f"operating_income={r.operating_income}\n"
            )

    prompt = (
        f"You are a senior equity analyst writing the opening section of an equity research report on {ticker.symbol}.\n\n"
        f"Recent news headlines:\n{news_text}\n\n"
        f"Recent financial highlights:\n{fin_summary or 'Not available.'}\n\n"
        "Write two sections:\n\n"
        "WHAT_HAPPENED:\n"
        f"One concise paragraph (3-5 sentences) summarising the most significant recent developments for {ticker.symbol} "
        "— earnings releases, strategic announcements, guidance updates, or macro events. Cite specific figures where available.\n\n"
        "OUR_THOUGHTS:\n"
        "Two to three short prose paragraphs sharing analytical perspective covering: "
        "(1) what the recent news implies for the investment thesis, "
        "(2) key financial trends (revenue trajectory, margin direction, cash generation), "
        "(3) the main risk or opportunity to watch. Be specific and opinionated but balanced.\n\n"
        'Format your response as JSON: {"what_happened": "...", "our_thoughts": "<p>...</p><p>...</p><p>...</p>"}'
    )

    client = _get_client()
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text_block = next(b for b in msg.content if b.type == "text")
    raw = text_block.text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    parsed = json.loads(raw)
    result = InsightsData(
        what_happened=parsed.get("what_happened", ""),
        our_thoughts=parsed.get("our_thoughts", ""),
        news_headlines=headlines,
    )
    _disk_cache.set(cache_key, result.model_dump(), expire=86400)
    return result


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
