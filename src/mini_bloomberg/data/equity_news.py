"""
Fetch recent company news via OpenBB.
Tries providers in order: yfinance → fmp → benzinga.
Results cached 24 h.
"""

from mini_bloomberg.core.cache import _cache as _disk_cache
from mini_bloomberg.core.ticker import Ticker

_PROVIDERS = ["yfinance", "fmp", "benzinga"]


def fetch_company_news(ticker: Ticker, limit: int = 10) -> list[dict]:
    """Return [{title, date, text}] for the ticker; [] if all providers fail."""
    cache_key = f"news:{ticker.symbol}:{ticker.exchange_code}"
    cached = _disk_cache.get(cache_key)
    if cached is not None:
        return cached

    from openbb import obb

    symbol = ticker.symbol
    for provider in _PROVIDERS:
        try:
            result = obb.news.company(symbol=symbol, provider=provider, limit=limit)
            items = getattr(result, "results", None) or []
            if items:
                news = [
                    {
                        "title": getattr(i, "title", "") or "",
                        "date":  str(getattr(i, "date",  "") or ""),
                        "text":  getattr(i, "text", "") or getattr(i, "summary", "") or "",
                    }
                    for i in items[:limit]
                ]
                _disk_cache.set(cache_key, news, expire=86400)
                return news
        except Exception:
            continue

    _disk_cache.set(cache_key, [], expire=86400)
    return []
