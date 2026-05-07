class MiniBloombergError(Exception):
    pass


class TickerError(MiniBloombergError):
    """Ticker string cannot be parsed."""


class DataSourceError(MiniBloombergError):
    """All data providers failed for a given request."""


class NoLoadedSecurityError(MiniBloombergError):
    """Function called but no ticker loaded into session."""


class RateLimitError(DataSourceError):
    """Provider signalled rate limiting (HTTP 429)."""
