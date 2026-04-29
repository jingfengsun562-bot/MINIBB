from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_report import get_equity_report
from mini_bloomberg.functions.base import BloombergFunction


class RV(BloombergFunction):
    name = "RV"
    description = (
        "Relative value: P/E, EV/EBITDA, P/B, EV/Sales, FCF yield, and margin "
        "comparison for the loaded ticker versus its peer group."
    )

    def run(self, ticker: str | None = None, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            report = get_equity_report(t)
            return {
                "status": "ok",
                "data": {
                    "symbol": t.symbol,
                    "name": report.profile.name if report.profile else None,
                    "currency": (report.financials.currency if report.financials else None)
                                or (report.profile.currency if report.profile else None),
                    "valuation": report.valuation.model_dump() if report.valuation else {},
                    "ratios": report.ratios_by_year[0].model_dump() if report.ratios_by_year else {},
                    "peers": [p.model_dump() for p in report.comparables.peers]
                             if report.comparables else [],
                },
            }
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "rv",
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
