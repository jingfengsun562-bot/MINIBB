from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.equity_price import get_price_history
from mini_bloomberg.functions.base import BloombergFunction


class GP(BloombergFunction):
    name = "GP"
    description = (
        "Graph price: interactive OHLCV candlestick chart with volume bars, "
        "50/200-day SMAs, and key statistics. Configurable lookback period in days."
    )

    def run(self, ticker: str | None = None, days: int = 365, **kwargs) -> dict:
        try:
            t = self._resolve_ticker(ticker)
            history = get_price_history(t, days=days)
            bars = history.bars[-days:] if history.bars else []

            closes  = [b.close  for b in bars if b.close  is not None]
            highs   = [b.high   for b in bars if b.high   is not None]
            lows    = [b.low    for b in bars if b.low    is not None]
            volumes = [b.volume for b in bars if b.volume is not None]

            period_high = max(highs)   if highs   else None
            period_low  = min(lows)    if lows    else None
            avg_volume  = (sum(volumes) / len(volumes)) if volumes else None
            first_close = closes[0]    if closes  else None
            last_close  = closes[-1]   if closes  else None
            pct_chg = (
                (last_close - first_close) / first_close * 100
                if first_close and last_close else None
            )

            return {
                "status":       "ok",
                "data":         history.model_dump(),
                "lookback":     days,
                "period_high":  period_high,
                "period_low":   period_low,
                "avg_volume":   avg_volume,
                "pct_change":   pct_chg,
                "currency":     history.currency,
            }
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
