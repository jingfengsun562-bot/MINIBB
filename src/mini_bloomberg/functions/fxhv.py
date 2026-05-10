"""FXHV — FX Historical Volatility.

Annualised realised volatility for an FX pair over 10d / 20d / 30d / 60d / 90d / 180d / 1Y.
Equivalent to Bloomberg's FXHV function.

Accepted input styles (same pattern as FRD)
-------------------------------------------
Positional pair string (recommended):
    FXHV EURUSD <GO>           # 6-char concatenated pair
    FXHV EUR USD <GO>          # two separate tokens
    FXHV EUR <GO>              # bare base, quote defaults to USD

Via flags (also accepted):
    FXHV --base EUR --quote USD <GO>

Via LLM tool call:
    {"base": "EUR", "quote": "USD"}
"""

from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.fx import get_fx_volatility
from mini_bloomberg.functions.base import BloombergFunction


def _parse_pair(pair_str: str) -> tuple[str, str]:
    """
    Parse a currency pair string into (base, quote).

    Handles:
      "EURUSD"   -> ("EUR", "USD")
      "EURUSD=X" -> ("EUR", "USD")
      "EUR/USD"  -> ("EUR", "USD")
      "EUR-USD"  -> ("EUR", "USD")
      "EUR"      -> ("EUR", "USD")   # bare base, USD assumed
    """
    s = pair_str.upper().replace("=X", "").replace("/", "").replace("-", "").replace(" ", "")
    if len(s) == 6:
        return s[:3], s[3:]
    if len(s) == 3:
        return s, "USD"
    raise ValueError(
        f"Cannot parse currency pair '{pair_str}'. "
        "Use 'EURUSD', 'EUR/USD', 'EUR USD', or '--base EUR --quote USD'."
    )


class FXHV(BloombergFunction):
    name = "FXHV"
    description = (
        "FX Historical Volatility -- annualised realised vol for a currency pair "
        "over 10d, 20d, 30d, 60d, 90d, 180d, and 1Y rolling windows. "
        "Accepts: EURUSD  |  EUR USD  |  EUR  |  --base EUR --quote USD."
    )

    def run(
        self,
        ticker: str | None = None,
        base: str | None = None,
        quote: str = "USD",
        pair: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Resolve the currency pair from whichever input form was supplied.

        Priority order:
          1. explicit base (+ optional quote) keyword args
          2. pair keyword arg, e.g. pair="EURUSD"
          3. ticker positional string from the CLI dispatcher (e.g. "EUR USD")
          4. Hard-coded fallback: EUR/USD
        """
        try:
            if base is not None:
                resolved_base  = base.upper().strip()
                resolved_quote = quote.upper().strip()

            elif pair is not None:
                resolved_base, resolved_quote = _parse_pair(pair)

            elif ticker is not None:
                resolved_base, resolved_quote = _parse_pair(ticker.replace(" ", ""))

            else:
                resolved_base, resolved_quote = "EUR", "USD"

            for label, code in (("base", resolved_base), ("quote", resolved_quote)):
                if not (len(code) == 3 and code.isalpha()):
                    return {
                        "status": "error",
                        "message": (
                            f"'{code}' is not a valid ISO currency code for {label}. "
                            "Use a 3-letter code such as EUR, USD, JPY, GBP."
                        ),
                    }

            if resolved_base == resolved_quote:
                return {
                    "status": "error",
                    "message": "base and quote must be different currencies.",
                }

            vol = get_fx_volatility(base=resolved_base, quote=resolved_quote)
            return {"status": "ok", "data": vol.model_dump()}

        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "fxhv",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "base": {
                        "type": "string",
                        "description": (
                            "Base currency ISO code, e.g. 'EUR'. "
                            "Alternatively pass the full pair in 'pair'."
                        ),
                    },
                    "quote": {
                        "type": "string",
                        "description": "Counter currency ISO code (default 'USD').",
                        "default": "USD",
                    },
                    "pair": {
                        "type": "string",
                        "description": (
                            "Convenience: full pair string such as 'EURUSD' or 'EUR/USD'. "
                            "Ignored when 'base' is also supplied."
                        ),
                    },
                },
                "required": [],
            },
        }
