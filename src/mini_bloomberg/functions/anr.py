from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_estimates import get_analyst_ratings
from mini_bloomberg.functions.base import BloombergFunction


class ANR(BloombergFunction):
    name = "ANR"
    description = "Analyst recommendations: consensus price target (high/low/median) and buy/hold/sell breakdown."

    def run(self, ticker: str | None = None, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            ratings = get_analyst_ratings(t)
            return {"status": "ok", "data": ratings.model_dump()}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "anr",
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
