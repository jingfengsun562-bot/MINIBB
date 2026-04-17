from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_profile import get_profile
from mini_bloomberg.functions.base import BloombergFunction


class DES(BloombergFunction):
    name = "DES"
    description = "Company description: name, sector, exchange, market cap, and key identifiers."

    def run(self, ticker: str | None = None, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            profile = get_profile(t)
            return {"status": "ok", "data": profile.model_dump()}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "des",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Bloomberg-style ticker, e.g. 'AAPL US Equity' or '0700 HK Equity'",
                    }
                },
                "required": ["ticker"],
            },
        }
