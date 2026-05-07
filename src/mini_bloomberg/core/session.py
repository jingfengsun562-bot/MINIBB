from mini_bloomberg.core.errors import NoLoadedSecurityError
from mini_bloomberg.core.ticker import Ticker, parse_ticker


class Session:
    """Module-level singleton holding the currently loaded security."""

    def __init__(self) -> None:
        self.loaded_ticker: Ticker | None = None

    def load(self, ticker_str: str) -> Ticker:
        self.loaded_ticker = parse_ticker(ticker_str)
        return self.loaded_ticker

    def require_loaded(self) -> Ticker:
        if self.loaded_ticker is None:
            raise NoLoadedSecurityError(
                "No security loaded. Type a ticker first, e.g.: AAPL US Equity <GO>"
            )
        return self.loaded_ticker

    def clear(self) -> None:
        self.loaded_ticker = None

    @property
    def is_loaded(self) -> bool:
        return self.loaded_ticker is not None


# Singleton — import this everywhere
session = Session()
