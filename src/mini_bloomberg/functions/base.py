from abc import ABC, abstractmethod

from mini_bloomberg.core.session import session
from mini_bloomberg.core.ticker import Ticker, parse_ticker


class BloombergFunction(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, ticker: str | None = None, **kwargs) -> dict:
        """
        Execute the function. Returns {"status": "ok", "data": {...}}
        or {"status": "error", "message": "..."} — never raises to the caller.

        If ticker is None, resolves from the loaded session.
        """

    @abstractmethod
    def tool_schema(self) -> dict:
        """Return an Anthropic-compatible tool spec dict."""

    def _resolve_ticker(self, ticker: str | None) -> Ticker:
        if ticker:
            return parse_ticker(ticker)
        return session.require_loaded()
