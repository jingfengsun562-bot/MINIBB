"""
DCF valuation following DCF_Guide.md:
  FCFF = EBIT*(1-T) + D&A - ΔNWC - CapEx
  WACC = E/(E+D)*Ke + D/(E+D)*Kd*(1-T)
  Ke = Rf + β_L*(ERP + CRP)
  TV = FCFF_{n+1}/(WACC - g)
"""

from __future__ import annotations

import logging
import warnings
from html.parser import HTMLParser
from typing import Optional

import requests

from mini_bloomberg.core.cache import _cache as _disk_cache
from mini_bloomberg.data.schemas import DCFResult, FCFFYear, Financials

# suppress noisy urllib3 warnings when Damodaran is unreachable
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)  # type: ignore[attr-defined]

log = logging.getLogger(__name__)

_FALLBACK_RF  = 0.043   # 4.3%  — used when Treasury fetch fails
_FALLBACK_ERP = 0.0446  # 4.46% — Damodaran implied ERP (last verified value)
_TERMINAL_GROWTH = 0.025
_PROJECTION_YEARS = 5
_SESS = requests.Session()
_SESS.headers.update({"User-Agent": "Mozilla/5.0 (research/academic)"})


# ─── HTML table parser ────────────────────────────────────────────────────────

class _TableParser(HTMLParser):
    """Minimal stdlib HTML table → list[list[str]] extractor."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._in_table = 0
        self._row: list[str] = []
        self._cell: list[str] = []
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "table":
            self._in_table += 1
            if self._in_table == 1:
                self.tables.append([])
        elif tag in ("td", "th") and self._in_table:
            self._in_cell = True
            self._cell = []
        elif tag == "tr" and self._in_table:
            self._row = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            self._row.append("".join(self._cell).strip())
            self._in_cell = False
        elif tag == "tr" and self._in_table and self._row:
            self.tables[-1].append(self._row)
            self._row = []
        elif tag == "table":
            self._in_table = max(0, self._in_table - 1)

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell.append(data)


def _parse_pct(s: str) -> Optional[float]:
    """'4.60%' → 0.046  or  '4.60' → 0.046"""
    s = s.strip().replace("%", "").replace(",", "")
    try:
        return float(s) / 100
    except ValueError:
        return None


# ─── External data fetchers ───────────────────────────────────────────────────

@_disk_cache.memoize(expire=60 * 60 * 4)  # 4h — rates move during the day
def fetch_treasury_10y() -> float:
    """
    Fetch current 10-year US Treasury yield. Returns decimal (0.043 = 4.3%).

    The Treasury page requires a year parameter; without it the site returns
    the oldest historical data (1990). We try the current year first, then
    fall back to the prior year (in case it's early January and the page is empty).
    """
    from datetime import date as _date
    base = (
        "https://home.treasury.gov/resource-center/data-chart-center/"
        "interest-rates/TextView?type=daily_treasury_yield_curve"
        "&field_tdr_date_value="
    )
    for year in (_date.today().year, _date.today().year - 1):
        try:
            r = _SESS.get(base + str(year), timeout=10)
            r.raise_for_status()
            parser = _TableParser()
            parser.feed(r.text)
            for table in parser.tables:
                headers = [h.strip() for h in (table[0] if table else [])]
                try:
                    idx = next(i for i, h in enumerate(headers) if "10 yr" in h.lower())
                except StopIteration:
                    continue
                # iterate in reverse to get the most recent row first
                for row in reversed(table[1:]):
                    if idx < len(row) and row[idx].strip() not in ("", "N/A"):
                        v = _parse_pct(row[idx])
                        if v and 0.01 < v < 0.15:
                            log.debug("Treasury 10Y (%s): %.4f", year, v)
                            return v
        except Exception as exc:
            log.warning("Treasury fetch failed for year %s (%s)", year, exc)
    log.warning("Treasury 10Y: all fetches failed — using fallback %.3f", _FALLBACK_RF)
    return _FALLBACK_RF


@_disk_cache.memoize(expire=60 * 60 * 24)  # 24h
def fetch_damodaran_erp() -> float:
    """
    Fetch US mature-market ERP from Damodaran's ctryprem page.

    The old implprem.html URL is dead (404). ctryprem.html is alive and contains
    a column "Equity Risk Premium" for every country. The United States row value
    in that column is Damodaran's current implied ERP for the mature market.
    """
    url = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html"
    try:
        r = _SESS.get(url, timeout=15)
        r.raise_for_status()
        parser = _TableParser()
        parser.feed(r.text)
        for table in parser.tables:
            if not table:
                continue
            headers = [h.replace("\n", " ").strip().lower() for h in table[0]]
            # Find "Equity Risk Premium" column (col 4 in current page layout)
            erp_col = next(
                (i for i, h in enumerate(headers) if "equity risk" in h),
                None,
            )
            if erp_col is None:
                continue
            for row in table[1:]:
                if row and "united states" in row[0].lower():
                    if erp_col < len(row):
                        v = _parse_pct(row[erp_col])
                        if v and 0.01 < v < 0.15:
                            log.debug("Damodaran ERP (ctryprem US row): %.4f", v)
                            return v
    except Exception as exc:
        log.warning("Damodaran ERP fetch failed (%s) — using fallback %.4f", exc, _FALLBACK_ERP)
    return _FALLBACK_ERP


@_disk_cache.memoize(expire=60 * 60 * 24)  # 24h
def fetch_damodaran_crp(country: str) -> float:
    """Fetch country risk premium for a given country. Returns decimal (0 for US/failure)."""
    if not country or country.lower() in ("united states", "us", "usa", ""):
        return 0.0
    url = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html"
    try:
        r = _SESS.get(url, timeout=15)
        r.raise_for_status()
        parser = _TableParser()
        parser.feed(r.text)
        country_lower = country.lower()
        for table in parser.tables:
            # Try to find the CRP column index from headers
            headers = [h.lower() for h in (table[0] if table else [])]
            crp_col = next(
                (i for i, h in enumerate(headers) if "country risk" in h or "crp" in h),
                None,
            )
            for row in table[1:]:
                if not row:
                    continue
                if country_lower in row[0].lower():
                    col = crp_col if crp_col and crp_col < len(row) else -1
                    for cell in (row[col:col+3] if col >= 0 else row[1:4]):
                        v = _parse_pct(cell)
                        if v is not None and 0 <= v < 0.20:
                            log.debug("Damodaran CRP %s: %.4f", country, v)
                            return v
    except Exception as exc:
        log.warning("Damodaran CRP fetch failed for %s (%s)", country, exc)
    return 0.0


# ─── FCFF helpers ────────────────────────────────────────────────────────────

def _safe_tax_rate(tax_expense: Optional[int], net_income: Optional[int]) -> float:
    """Effective tax rate from income statement, clamped to [5%, 45%]."""
    if not tax_expense or not net_income:
        return 0.21
    pretax = net_income + tax_expense
    if pretax <= 0:
        return 0.21
    return max(0.05, min(0.45, tax_expense / pretax))


def _compute_fcff_history(financials: Financials) -> list[FCFFYear]:
    """Build historical FCFF rows from annual statements (oldest first)."""
    rows: list[FCFFYear] = []
    incs = financials.income_statements
    bals = financials.balance_sheets
    cfs = financials.cash_flows

    n = min(len(incs), len(cfs), 4)
    for i in range(n - 1, -1, -1):   # oldest → newest
        inc = incs[i]
        cf = cfs[i]
        fy = inc.fiscal_year or inc.date or f"Y-{i}"

        ebit = inc.ebit
        tax_rate = _safe_tax_rate(inc.income_tax_expense, inc.net_income)
        da = cf.depreciation_and_amortization
        # FMP change_in_working_capital: positive = cash inflow from NWC decrease
        # FCFF formula subtracts ΔNWC (increase in NWC is cash outflow)
        # So we negate: fcff -= (+nwc_change) means nwc_increase → subtract
        nwc_change_raw = cf.change_in_working_capital  # FMP sign convention
        nwc_change = -nwc_change_raw if nwc_change_raw is not None else None
        capex = abs(cf.capital_expenditure) if cf.capital_expenditure is not None else None

        if ebit is not None and da is not None and nwc_change is not None and capex is not None:
            ebit_at = ebit * (1 - tax_rate)
            fcff = ebit_at + da - nwc_change - capex
        else:
            ebit_at = None
            fcff = None

        rows.append(FCFFYear(
            year=str(fy),
            revenue=inc.revenue,
            ebit=ebit,
            tax_rate=tax_rate,
            ebit_after_tax=ebit_at,
            da=da,
            nwc_change=nwc_change,
            capex=capex,
            fcff=fcff,
        ))
    return rows


def _cagr(values: list[float]) -> float:
    """CAGR of a series (oldest first). Returns 0 if insufficient data."""
    vals = [v for v in values if v and v > 0]
    if len(vals) < 2:
        return 0.0
    n = len(vals) - 1
    return (vals[-1] / vals[0]) ** (1 / n) - 1


def _avg(values: list[Optional[float]]) -> float:
    good = [v for v in values if v is not None]
    return sum(good) / len(good) if good else 0.0


def _project_fcff(
    history: list[FCFFYear],
    wacc: float,
    tg: float,
    tax_rate: float,
) -> tuple[list[FCFFYear], float, float]:
    """
    Return (projections, revenue_cagr, ebit_margin_avg).
    Growth decays 10% each year (conservative tapering).
    """
    if not history:
        return [], 0.0, 0.0

    revenues = [h.revenue for h in history if h.revenue]
    ebits = [h.ebit for h in history if h.ebit and h.revenue]
    nwc_pcts = [
        h.nwc_change / h.revenue
        for h in history
        if h.nwc_change is not None and h.revenue and h.revenue > 0
    ]
    capex_pcts = [
        h.capex / h.revenue
        for h in history
        if h.capex is not None and h.revenue and h.revenue > 0
    ]

    rev_cagr = _cagr(revenues)  # type: ignore[arg-type]
    ebit_margins = [
        h.ebit / h.revenue
        for h in history
        if h.ebit is not None and h.revenue and h.revenue > 0
    ]
    ebit_margin_avg = _avg(ebit_margins)  # type: ignore[arg-type]
    avg_nwc_pct = _avg(nwc_pcts)
    avg_capex_pct = _avg(capex_pcts)
    avg_da = _avg([h.da for h in history])  # type: ignore[arg-type]

    last = history[-1]
    prev_rev = last.revenue or 0.0
    prev_da = last.da or avg_da

    rows: list[FCFFYear] = []
    from datetime import date as _date
    base_year = int(last.year) if last.year.isdigit() else _date.today().year

    for t in range(1, _PROJECTION_YEARS + 1):
        g = rev_cagr * (0.9 ** (t - 1))   # decay 10% per year
        rev = prev_rev * (1 + g)
        ebit = rev * ebit_margin_avg
        da = prev_da                        # hold constant
        nwc_change = rev * avg_nwc_pct
        capex = rev * avg_capex_pct
        ebit_at = ebit * (1 - tax_rate)
        fcff = ebit_at + da - nwc_change - capex
        pv_factor = 1 / (1 + wacc) ** t
        rows.append(FCFFYear(
            year=str(base_year + t),
            revenue=rev,
            ebit=ebit,
            tax_rate=tax_rate,
            ebit_after_tax=ebit_at,
            da=da,
            nwc_change=nwc_change,
            capex=capex,
            fcff=fcff,
            pv_factor=pv_factor,
            pv_fcff=fcff * pv_factor,
        ))
        prev_rev = rev

    return rows, rev_cagr, ebit_margin_avg


def _sensitivity_grid(
    pv_discrete: float,
    last_fcff: float,
    n: int,
    total_debt: float,
    cash: float,
    shares: int,
    base_wacc: float,
    base_tg: float,
) -> tuple[list[float], list[float], list[list[float]]]:
    """Build 5×5 sensitivity grid: rows=WACC variants, cols=tg variants."""
    wacc_variants = [round(base_wacc + d, 4) for d in (-0.02, -0.01, 0.0, 0.01, 0.02)]
    tg_variants = [0.015, 0.020, 0.025, 0.030, 0.035]
    grid: list[list[float]] = []

    for w in wacc_variants:
        row: list[float] = []
        for g in tg_variants:
            if w <= g:
                row.append(0.0)
                continue
            # Re-discount historical discrete CFs at new WACC (approximate: scale pv_discrete)
            pv_d = pv_discrete * ((1 + base_wacc) / (1 + w)) ** (n / 2)
            tv = last_fcff * (1 + g) / (w - g)
            pv_tv = tv / (1 + w) ** n
            ev = pv_d + pv_tv
            eq = ev - total_debt + cash
            price = eq / shares if shares else 0.0
            row.append(round(price, 2))
        grid.append(row)

    return wacc_variants, tg_variants, grid


# ─── Main entry point ─────────────────────────────────────────────────────────

def compute_dcf(report, current_price: Optional[float]) -> Optional[DCFResult]:  # type: ignore[type-arg]
    """
    Compute a full DCF for the report's ticker.
    Returns None on any unrecoverable error so the report still renders.
    """
    try:
        if not report.financials or not report.profile:
            return None

        fin = report.financials
        profile = report.profile

        # ── External market data ───────────────────────────────────────────
        using_fallback = False
        try:
            rf = fetch_treasury_10y()
        except Exception:
            rf = _FALLBACK_RF
            using_fallback = True
        try:
            erp = fetch_damodaran_erp()
        except Exception:
            erp = _FALLBACK_ERP
            using_fallback = True

        country = profile.country or ""
        try:
            crp = fetch_damodaran_crp(country)
        except Exception:
            crp = 0.0

        # ── Historical FCFF ────────────────────────────────────────────────
        history = _compute_fcff_history(fin)
        if not history:
            return None

        # Average tax rate from history
        tax_rate = _avg([h.tax_rate for h in history])  # type: ignore[arg-type]

        # ── Capital structure ──────────────────────────────────────────────
        mkt_cap = profile.market_cap or 0
        latest_bs = fin.balance_sheets[0] if fin.balance_sheets else None
        total_debt = float(latest_bs.total_debt or 0) if latest_bs else 0.0
        cash_bal = float(latest_bs.cash_and_equivalents or 0) if latest_bs else 0.0

        E = float(mkt_cap)
        D = total_debt
        total_cap = E + D
        equity_weight = E / total_cap if total_cap > 0 else 1.0
        debt_weight = D / total_cap if total_cap > 0 else 0.0

        # ── Beta & cost of equity ──────────────────────────────────────────
        beta_raw = profile.beta
        beta_levered = beta_raw if beta_raw and 0.1 < beta_raw < 5.0 else 1.0

        ke = rf + beta_levered * (erp + crp)

        # ── Cost of debt ───────────────────────────────────────────────────
        latest_inc = fin.income_statements[0] if fin.income_statements else None
        int_exp = abs(latest_inc.interest_expense or 0) if latest_inc else 0.0
        kd = (int_exp / D) if D > 1e6 else (rf + 0.02)
        kd = max(rf, min(rf + 0.10, kd))

        # ── WACC ───────────────────────────────────────────────────────────
        wacc = equity_weight * ke + debt_weight * kd * (1 - tax_rate)
        wacc = max(0.04, min(0.20, wacc))

        # ── Project FCFF ───────────────────────────────────────────────────
        projections, rev_cagr, ebit_margin_avg = _project_fcff(
            history, wacc, _TERMINAL_GROWTH, tax_rate
        )
        if not projections:
            return None

        # ── Terminal value & bridge ────────────────────────────────────────
        last_proj_fcff = projections[-1].fcff or 0.0
        tv = last_proj_fcff * (1 + _TERMINAL_GROWTH) / (wacc - _TERMINAL_GROWTH)
        pv_tv = tv / (1 + wacc) ** _PROJECTION_YEARS
        pv_disc = sum(p.pv_fcff or 0.0 for p in projections)
        ev_dcf = pv_disc + pv_tv

        shares = profile.shares_outstanding
        eq_value = ev_dcf - D + cash_bal
        dcf_per_share = eq_value / shares if shares and shares > 0 else None
        upside = (
            (dcf_per_share - current_price) / current_price
            if dcf_per_share and current_price and current_price > 0
            else None
        )

        # ── Sensitivity ────────────────────────────────────────────────────
        if shares and shares > 0:
            s_wacc, s_tg, s_grid = _sensitivity_grid(
                pv_disc, last_proj_fcff, _PROJECTION_YEARS,
                D, cash_bal, shares, wacc, _TERMINAL_GROWTH,
            )
        else:
            s_wacc, s_tg, s_grid = [], [], []

        return DCFResult(
            rf=rf,
            erp=erp,
            crp=crp,
            using_fallback_rates=using_fallback,
            beta_raw=beta_raw,
            beta_levered=beta_levered,
            tax_rate=tax_rate,
            cost_of_equity=ke,
            cost_of_debt=kd,
            equity_weight=equity_weight,
            debt_weight=debt_weight,
            wacc=wacc,
            terminal_growth=_TERMINAL_GROWTH,
            revenue_cagr=rev_cagr,
            ebit_margin_avg=ebit_margin_avg,
            fcff_history=history,
            fcff_projections=projections,
            pv_discrete=pv_disc,
            terminal_value=tv,
            pv_terminal=pv_tv,
            enterprise_value_dcf=ev_dcf,
            total_debt=D,
            cash=cash_bal,
            equity_value_dcf=eq_value,
            shares_outstanding=shares,
            dcf_per_share=dcf_per_share,
            current_price=current_price,
            upside_pct=upside,
            sensitivity_wacc=s_wacc,
            sensitivity_tg=s_tg,
            sensitivity_grid=s_grid,
        )

    except Exception as exc:
        log.warning("compute_dcf failed: %s", exc, exc_info=True)
        return None
