from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_report import get_equity_report
from mini_bloomberg.functions.base import BloombergFunction


class RPT(BloombergFunction):
    name = "RPT"
    description = (
        "Comprehensive equity report: company profile, 3-statement financials, "
        "computed ratios, valuation multiples, analyst consensus, and peer comparison. "
        "Saves a Markdown file to the reports/ directory."
    )

    def run(self, ticker: str | None = None, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            report = get_equity_report(t)
            return {"status": "ok", "data": report.model_dump()}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "rpt",
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
