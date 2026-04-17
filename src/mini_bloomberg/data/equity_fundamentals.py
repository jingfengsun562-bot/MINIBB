"""
Fundamentals router: FMP for US tickers, OpenBB fallback for non-US.
"""

from mini_bloomberg.core.errors import DataSourceError
from mini_bloomberg.core.ticker import Ticker
from mini_bloomberg.data.providers import fmp_provider, openbb_provider
from mini_bloomberg.data.schemas import BalanceSheet, CashFlow, Financials, IncomeStatement


def get_financials(ticker: Ticker, years: int = 4) -> Financials:
    if ticker.is_us:
        try:
            return _from_fmp(ticker, years)
        except DataSourceError:
            pass  # fall through to OpenBB

    try:
        return _from_openbb(ticker, years)
    except Exception as e:
        raise DataSourceError(f"All fundamentals providers failed for {ticker}: {e}") from e


def _from_fmp(ticker: Ticker, years: int) -> Financials:
    income   = fmp_provider.get_income_statements(ticker, limit=years)
    balance  = fmp_provider.get_balance_sheets(ticker, limit=years)
    cashflow = fmp_provider.get_cash_flows(ticker, limit=years)
    currency = income[0].reported_currency if income else None
    return Financials(
        symbol=ticker.symbol,
        currency=currency,
        income_statements=income,
        balance_sheets=balance,
        cash_flows=cashflow,
    )


def _from_openbb(ticker: Ticker, years: int) -> Financials:
    obb = openbb_provider._obb()
    sym = ticker.yfinance_symbol
    kwargs = dict(symbol=sym, provider="yfinance", period="annual", limit=years)

    inc_raw = openbb_provider._all(obb.equity.fundamental.income(**kwargs))
    bal_raw = openbb_provider._all(obb.equity.fundamental.balance(**kwargs))
    cf_raw  = openbb_provider._all(obb.equity.fundamental.cash(**kwargs))

    currency = (inc_raw[0].get("reported_currency") or inc_raw[0].get("currency")) if inc_raw else None

    def _income(r: dict) -> IncomeStatement:
        return IncomeStatement(
            symbol=ticker.symbol,
            date=str(r.get("date", ""))[:10],
            fiscal_year=str(r.get("date", ""))[:4],
            period="FY",
            reported_currency=currency,
            revenue=r.get("revenue") or r.get("total_revenue"),
            cost_of_revenue=r.get("cost_of_revenue"),
            gross_profit=r.get("gross_profit"),
            operating_expenses=r.get("operating_expenses") or r.get("total_operating_expenses"),
            operating_income=r.get("operating_income") or r.get("ebit"),
            ebitda=r.get("ebitda"),
            ebit=r.get("ebit"),
            net_income=r.get("net_income"),
            eps=r.get("basic_earnings_per_share") or r.get("eps"),
            eps_diluted=r.get("diluted_earnings_per_share") or r.get("eps_diluted"),
            rd_expenses=r.get("research_and_development_expenses") or r.get("research_and_development"),
            depreciation_and_amortization=r.get("depreciation_and_amortization"),
        )

    def _balance(r: dict) -> BalanceSheet:
        return BalanceSheet(
            symbol=ticker.symbol,
            date=str(r.get("date", ""))[:10],
            fiscal_year=str(r.get("date", ""))[:4],
            period="FY",
            reported_currency=currency,
            cash_and_equivalents=r.get("cash_and_cash_equivalents") or r.get("cash"),
            total_current_assets=r.get("total_current_assets"),
            total_assets=r.get("total_assets"),
            total_current_liabilities=r.get("total_current_liabilities"),
            total_liabilities=r.get("total_liabilities") or r.get("total_liab"),
            total_stockholders_equity=r.get("total_stockholder_equity") or r.get("stockholders_equity"),
            total_equity=r.get("total_equity") or r.get("stockholders_equity"),
            total_debt=r.get("total_debt") or r.get("long_term_debt"),
            net_debt=r.get("net_debt"),
        )

    def _cf(r: dict) -> CashFlow:
        return CashFlow(
            symbol=ticker.symbol,
            date=str(r.get("date", ""))[:10],
            fiscal_year=str(r.get("date", ""))[:4],
            period="FY",
            reported_currency=currency,
            net_income=r.get("net_income"),
            depreciation_and_amortization=r.get("depreciation_and_amortization") or r.get("depreciation"),
            operating_cash_flow=r.get("operating_cash_flow") or r.get("total_cash_from_operating_activities"),
            capital_expenditure=r.get("capital_expenditure") or r.get("capital_expenditures"),
            free_cash_flow=r.get("free_cash_flow"),
            dividends_paid=r.get("dividends_paid") or r.get("common_dividends_paid"),
            common_stock_repurchased=r.get("repurchase_of_capital_stock") or r.get("common_stock_repurchased"),
        )

    return Financials(
        symbol=ticker.symbol,
        currency=currency,
        income_statements=[_income(r) for r in inc_raw],
        balance_sheets=[_balance(r) for r in bal_raw],
        cash_flows=[_cf(r) for r in cf_raw],
    )
