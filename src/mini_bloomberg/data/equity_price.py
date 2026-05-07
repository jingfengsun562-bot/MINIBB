"""
Price history router: FMP for US, OpenBB fallback for non-US.
"""

from mini_bloomberg.core.errors import DataSourceError
from mini_bloomberg.core.ticker import Ticker
from mini_bloomberg.data.providers import fmp_provider, openbb_provider
from mini_bloomberg.data.schemas import PriceHistory


def get_price_history(ticker: Ticker, days: int = 365) -> PriceHistory:
    if ticker.is_us:
        try:
            history = fmp_provider.get_price_history(ticker, limit=days)
            # FMP returns newest-first; reverse to chronological order
            history.bars = list(reversed(history.bars))
            return history
        except DataSourceError:
            pass

    try:
        history = openbb_provider.get_price_history(ticker, days=days)
        return history
    except DataSourceError:
        raise
    except Exception as e:
        raise DataSourceError(f"All price providers failed for {ticker}: {e}") from e
