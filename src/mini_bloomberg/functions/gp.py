from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_price import get_price_history
from mini_bloomberg.functions.base import BloombergFunction


class GP(BloombergFunction):
    name = "GP"
    description = "Graph price: ASCII price chart with configurable lookback period in days."

    def run(self, ticker: str | None = None, days: int = 365, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            history = get_price_history(t, days=days)
            result = history.model_dump()
            return {"status": "ok", "data": result, "lookback": days}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "gp",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Bloomberg-style ticker, e.g. 'AAPL US Equity'",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Lookback in calendar days (default 365)",
                        "default": 365,
                    },
                },
                "required": ["ticker"],
            },
        }
