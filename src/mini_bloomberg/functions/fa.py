from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_fundamentals import get_financials
from mini_bloomberg.functions.base import BloombergFunction


class FA(BloombergFunction):
    name = "FA"
    description = "Financial analysis: income statement, balance sheet, and cash flow for the last N annual periods."

    def run(self, ticker: str | None = None, years: int = 4, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            financials = get_financials(t, years=years)
            return {"status": "ok", "data": financials.model_dump()}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "fa",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Bloomberg-style ticker, e.g. 'AAPL US Equity'",
                    },
                    "years": {
                        "type": "integer",
                        "description": "Number of annual periods to retrieve (default 4)",
                        "default": 4,
                    },
                },
                "required": ["ticker"],
            },
        }
