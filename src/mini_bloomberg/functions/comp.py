from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_peers import get_comparables
from mini_bloomberg.functions.base import BloombergFunction


class COMP(BloombergFunction):
    name = "COMP"
    description = "Comparable companies: side-by-side table of peers on market cap, revenue, margins, EBITDA, and debt."

    def run(self, ticker: str | None = None, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            comparables = get_comparables(t)
            return {"status": "ok", "data": comparables.model_dump()}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "comp",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Bloomberg-style ticker, e.g. 'AAPL US Equity'",
                    }
                },
                "required": ["ticker"],
            },
        }
