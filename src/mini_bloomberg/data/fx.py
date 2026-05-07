"""
FX data layer.

All FX data comes from yfinance via OpenBB (no special FX subscription needed).
yfinance ticker format for FX pairs: "EURUSD=X", "GBPUSD=X", etc.

Functions:
  get_fx_rate(base, quote)           → FXRate (spot)
  get_fx_board(pairs)                → FXBoard (multi-currency monitor)
  get_fx_history(base, quote, days)  → PriceHistory (OHLCV)
  get_fx_volatility(base, quote)     → FXVolatility
  get_fx_forward_curve(base, quote)  → FXForwardCurve (CIP-implied, no real swap points)
  get_fx_ranking(currencies)         → FXRanking
"""

import math
from datetime import date, timedelta
from typing import Optional

import yfinance as yf

from mini_bloomberg.core.cache import cached
from mini_bloomberg.core.errors import DataSourceError
from mini_bloomberg.data.schemas import (
    FXBoard,
    FXConversion,
    FXForwardCurve,
    FXForwardPoint,
    FXRankRow,
    FXRanking,
    FXRate,
    FXVolatility,
    PriceBar,
    PriceHistory,
)

# ─── G10 + major EM currency list for FXIP / WCR ─────────────────────────────

G10_CURRENCIES = ["EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "NOK", "SEK", "DKK"]
EM_CURRENCIES  = ["CNY", "HKD", "SGD", "KRW", "INR", "TWD", "BRL", "MXN", "ZAR", "TRY",
                  "THB", "IDR", "MYR", "PHP", "CZK", "PLN", "HUF", "ILS"]

# Standard FRD tenors with approximate day counts
FRD_TENORS = [
    ("O/N",  1),
    ("1W",   7),
    ("2W",  14),
    ("1M",  30),
    ("2M",  60),
    ("3M",  91),
    ("6M", 182),
    ("9M", 273),
    ("1Y", 365),
]

# Approximate risk-free rates (annualised %) used for CIP forward approximation.
# These are rough mid-point values; real Bloomberg uses live OIS/LIBOR/SOFR.
# Keep as a fallback when live rates are unavailable.
_APPROX_RATES: dict[str, float] = {
    "USD": 5.30, "EUR": 4.00, "GBP": 5.25, "JPY": 0.10, "CHF": 1.75,
    "AUD": 4.35, "NZD": 5.50, "CAD": 5.00, "NOK": 4.50, "SEK": 3.75,
    "DKK": 3.75, "CNY": 2.50, "HKD": 5.50, "SGD": 3.50, "KRW": 3.50,
    "INR": 6.50, "BRL": 10.50, "MXN": 11.25, "ZAR": 8.25, "TRY": 42.50,
    "TWD": 2.00, "IDR": 6.25, "MYR": 3.00, "THB": 2.50, "PHP": 6.50,
    "CZK": 5.25, "PLN": 5.75, "HUF": 9.00, "ILS": 4.50,
}


def _yf_pair(base: str, quote: str) -> str:
    """Return yfinance FX ticker, e.g. 'EURUSD=X'."""
    return f"{base.upper()}{quote.upper()}=X"


def _download_history(ticker: str, period: str = "1y") -> list[dict]:
    """
    Download OHLCV history from yfinance.
    Returns list of {'date', 'open', 'high', 'low', 'close', 'volume'} dicts.
    """
    import logging
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        if df.empty:
            return []
        df = df.reset_index()
        rows = []
        for _, row in df.iterrows():
            dt = row["Date"]
            date_str = dt.date().isoformat() if hasattr(dt, "date") else str(dt)[:10]
            close_val = row["Close"]
            # Handle MultiIndex columns from yfinance >=0.2.38
            if hasattr(close_val, "item"):
                close_val = float(close_val.item())
            elif hasattr(close_val, "__len__"):
                close_val = float(close_val.iloc[0]) if len(close_val) > 0 else None
            else:
                close_val = float(close_val) if close_val is not None else None

            def _safe(v):
                try:
                    if hasattr(v, "item"):
                        return float(v.item())
                    if hasattr(v, "__len__"):
                        return float(v.iloc[0]) if len(v) > 0 else None
                    return float(v) if v is not None else None
                except Exception:
                    return None

            rows.append({
                "date":   date_str,
                "open":   _safe(row["Open"]),
                "high":   _safe(row["High"]),
                "low":    _safe(row["Low"]),
                "close":  close_val,
                "volume": None,
            })
        return rows
    except Exception as e:
        raise DataSourceError(f"yfinance download failed for {ticker}: {e}") from e


def _annualised_vol(closes: list[float], window: int) -> Optional[float]:
    """Compute annualised historical volatility (%) from a list of closing prices."""
    if len(closes) < window + 1:
        return None
    subset = closes[-(window + 1):]
    log_returns = [
        math.log(subset[i] / subset[i - 1])
        for i in range(1, len(subset))
        if subset[i] and subset[i - 1] and subset[i] > 0 and subset[i - 1] > 0
    ]
    if len(log_returns) < 2:
        return None
    n = len(log_returns)
    mean = sum(log_returns) / n
    variance = sum((r - mean) ** 2 for r in log_returns) / (n - 1)
    return math.sqrt(variance) * math.sqrt(252) * 100  # annualised %


# ─── Public data functions ────────────────────────────────────────────────────

@cached(ttl=300)  # 5-min TTL — FX rates change fast
def get_fx_rate(base: str, quote: str = "USD") -> FXRate:
    """Fetch current spot rate for base/quote, with 52-week range."""
    pair_str = f"{base.upper()}{quote.upper()}"
    yfticker  = _yf_pair(base, quote)
    rows      = _download_history(yfticker, period="1y")
    if not rows:
        raise DataSourceError(f"No FX data for {pair_str}")

    closes = [r["close"] for r in rows if r["close"] is not None]
    if not closes:
        raise DataSourceError(f"No closing prices for {pair_str}")

    spot    = closes[-1]
    prev    = closes[-2] if len(closes) >= 2 else None
    chg_pct = ((spot - prev) / prev * 100) if prev and prev != 0 else None

    return FXRate(
        pair=pair_str,
        base=base.upper(),
        quote=quote.upper(),
        rate=spot,
        change_pct=chg_pct,
        high_52w=max(closes),
        low_52w=min(closes),
        date=rows[-1]["date"],
    )


@cached(ttl=300)
def get_fx_board(pairs: Optional[list[tuple[str, str]]] = None) -> FXBoard:
    """
    Multi-currency spot board.
    Default: G10 vs USD.  Pass [(base, quote), ...] to override.
    """
    if pairs is None:
        pairs = [(ccy, "USD") for ccy in G10_CURRENCIES]

    rates = []
    for base, quote in pairs:
        try:
            rates.append(get_fx_rate(base, quote))
        except DataSourceError:
            # Add a placeholder so the board always shows all rows
            rates.append(FXRate(
                pair=f"{base}{quote}",
                base=base, quote=quote,
                rate=None, change_pct=None,
            ))

    return FXBoard(as_of=date.today().isoformat(), rates=rates)


@cached(ttl=3600)
def get_fx_history(base: str, quote: str = "USD", days: int = 365) -> PriceHistory:
    """Return OHLCV history for an FX pair as a PriceHistory object."""
    pair_str = f"{base.upper()}{quote.upper()}"
    yfticker  = _yf_pair(base, quote)
    # Map days → yfinance period string
    if days <= 30:
        period = "1mo"
    elif days <= 90:
        period = "3mo"
    elif days <= 180:
        period = "6mo"
    elif days <= 365:
        period = "1y"
    elif days <= 730:
        period = "2y"
    else:
        period = "5y"

    rows = _download_history(yfticker, period=period)
    if not rows:
        raise DataSourceError(f"No price history for FX pair {pair_str}")

    bars = [
        PriceBar(
            date=r["date"],
            open=r["open"],
            high=r["high"],
            low=r["low"],
            close=r["close"],
            volume=r["volume"],
        )
        for r in rows[-days:]
    ]
    return PriceHistory(symbol=pair_str, bars=bars)


@cached(ttl=3600)
def get_fx_volatility(base: str, quote: str = "USD") -> FXVolatility:
    """Compute annualised historical volatility over multiple windows."""
    pair_str = f"{base.upper()}{quote.upper()}"
    yficker  = _yf_pair(base, quote)
    rows     = _download_history(yficker, period="2y")
    if not rows:
        raise DataSourceError(f"No FX data for volatility calculation: {pair_str}")

    closes = [r["close"] for r in rows if r["close"] is not None]
    as_of  = rows[-1]["date"] if rows else None

    bars = [
        PriceBar(date=r["date"], open=r["open"], high=r["high"],
                 low=r["low"], close=r["close"])
        for r in rows[-252:]  # last year for charting
    ]

    return FXVolatility(
        pair=pair_str,
        as_of=as_of,
        vol_10d=_annualised_vol(closes, 10),
        vol_20d=_annualised_vol(closes, 20),
        vol_30d=_annualised_vol(closes, 30),
        vol_60d=_annualised_vol(closes, 60),
        vol_90d=_annualised_vol(closes, 90),
        vol_180d=_annualised_vol(closes, 180),
        vol_1y=_annualised_vol(closes, 252),
        bars=bars,
    )


@cached(ttl=3600)
def get_fx_forward_curve(base: str, quote: str = "USD") -> FXForwardCurve:
    """
    Build a forward-rate curve using Covered Interest Parity (CIP):

        F = S × (1 + r_quote × T) / (1 + r_base × T)

    where T is tenor in years, S is spot, and rates come from _APPROX_RATES.
    This is an approximation — real Bloomberg uses live OIS/SOFR swap points.
    """
    pair_str = f"{base.upper()}{quote.upper()}"
    spot_obj = get_fx_rate(base, quote)
    if spot_obj.rate is None:
        raise DataSourceError(f"Cannot build forward curve — no spot rate for {pair_str}")

    spot   = spot_obj.rate
    r_base = _APPROX_RATES.get(base.upper(), 3.0) / 100
    r_qte  = _APPROX_RATES.get(quote.upper(), 3.0) / 100

    tenors = []
    for tenor_label, days in FRD_TENORS:
        T = days / 365.0
        forward = spot * (1 + r_qte * T) / (1 + r_base * T)
        fwd_pts  = (forward - spot) * 10_000  # in pips (4th decimal)
        impl_diff = (r_qte - r_base) * 100    # annualised bp differential

        tenors.append(FXForwardPoint(
            tenor=tenor_label,
            days=days,
            forward_rate=round(forward, 6),
            forward_points=round(fwd_pts, 2),
            implied_yield_diff=round(impl_diff, 2),
        ))

    return FXForwardCurve(
        pair=pair_str,
        spot=spot,
        as_of=spot_obj.date,
        tenors=tenors,
    )


@cached(ttl=600)  # 10-min TTL
def get_fx_ranking(currencies: Optional[list[str]] = None, quote: str = "USD") -> FXRanking:
    """
    Rank currencies by performance vs USD over 1d / 1w / 1m / 3m / YTD.
    Default: G10 currencies.
    """
    if currencies is None:
        currencies = G10_CURRENCIES

    today      = date.today()
    year_start = date(today.year, 1, 1)

    rows: list[FXRankRow] = []
    for ccy in currencies:
        yficker = _yf_pair(ccy, quote)
        try:
            hist = _download_history(yficker, period="1y")
            if not hist:
                continue
            closes = {r["date"]: r["close"] for r in hist if r["close"] is not None}
            dates  = sorted(closes.keys())
            if not dates:
                continue

            def _closest(target_date: date) -> Optional[float]:
                target_str = target_date.isoformat()
                # find nearest date <= target
                candidates = [d for d in dates if d <= target_str]
                return closes[candidates[-1]] if candidates else None

            spot   = closes[dates[-1]]
            p_1d   = _closest(today - timedelta(days=1))
            p_1w   = _closest(today - timedelta(days=7))
            p_1m   = _closest(today - timedelta(days=30))
            p_3m   = _closest(today - timedelta(days=91))
            p_ytd  = _closest(year_start)

            def _chg(prev):
                if prev and prev != 0 and spot:
                    return (spot - prev) / prev * 100
                return None

            rows.append(FXRankRow(
                currency=ccy,
                pair_vs_usd=f"{ccy}{quote}",
                spot=spot,
                change_1d=_chg(p_1d),
                change_1w=_chg(p_1w),
                change_1m=_chg(p_1m),
                change_3m=_chg(p_3m),
                change_ytd=_chg(p_ytd),
            ))
        except Exception:
            continue  # skip currencies with no data

    # Sort by 1-day change descending (best performers first)
    rows.sort(key=lambda r: r.change_1d or 0, reverse=True)

    return FXRanking(as_of=today.isoformat(), rows=rows)


def convert_fx(amount: float, from_ccy: str, to_ccy: str) -> FXConversion:
    """
    Convert `amount` from from_ccy to to_ccy at current spot rate.
    Routes through USD if a direct pair is unavailable.
    """
    from_ccy = from_ccy.upper()
    to_ccy   = to_ccy.upper()

    if from_ccy == to_ccy:
        return FXConversion(
            from_currency=from_ccy, to_currency=to_ccy,
            amount=amount, rate=1.0, converted=amount,
            as_of=date.today().isoformat(),
        )

    # Try direct pair: from_ccy / to_ccy
    try:
        fx = get_fx_rate(from_ccy, to_ccy)
        if fx.rate:
            return FXConversion(
                from_currency=from_ccy, to_currency=to_ccy,
                amount=amount, rate=fx.rate,
                converted=round(amount * fx.rate, 6),
                as_of=fx.date,
            )
    except DataSourceError:
        pass

    # Try inverse: to_ccy / from_ccy and invert
    try:
        fx_inv = get_fx_rate(to_ccy, from_ccy)
        if fx_inv.rate and fx_inv.rate != 0:
            rate = 1 / fx_inv.rate
            return FXConversion(
                from_currency=from_ccy, to_currency=to_ccy,
                amount=amount, rate=round(rate, 8),
                converted=round(amount * rate, 6),
                as_of=fx_inv.date,
            )
    except DataSourceError:
        pass

    # Cross via USD: from_ccy → USD → to_ccy
    try:
        fx_to_usd   = get_fx_rate(from_ccy, "USD")
        fx_from_usd = get_fx_rate(to_ccy, "USD")
        if fx_to_usd.rate and fx_from_usd.rate and fx_from_usd.rate != 0:
            rate = fx_to_usd.rate / fx_from_usd.rate
            return FXConversion(
                from_currency=from_ccy, to_currency=to_ccy,
                amount=amount, rate=round(rate, 8),
                converted=round(amount * rate, 6),
                as_of=fx_to_usd.date,
            )
    except DataSourceError:
        pass

    raise DataSourceError(
        f"Cannot obtain FX rate for {from_ccy}/{to_ccy} — "
        "direct pair and USD cross both unavailable."
    )
