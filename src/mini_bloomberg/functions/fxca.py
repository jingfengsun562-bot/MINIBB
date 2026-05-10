"""FXCA — FX Calculator.

Convert amounts between any two currencies at the current spot rate.
Routes through USD if a direct quote is unavailable.
Equivalent to Bloomberg's FXCA currency converter.

Accepted input styles (same pattern as FRD)
-------------------------------------------
Positional pair string (recommended):
    FXCA USDJPY <GO>               # 6-char concatenated pair, amount defaults to 1
    FXCA USD JPY <GO>              # two separate tokens, amount defaults to 1
    FXCA USD JPY 1000 <GO>         # with amount
    FXCA USDJPY 1000 <GO>          # concatenated pair + amount
    FXCA USD <GO>                  # bare from-ccy, to defaults to USD... actually shows rate

Via flags (also accepted):
    FXCA --from USD --to JPY --amount 1000 <GO>

Via LLM tool call:
    {"from_ccy": "USD", "to_ccy": "JPY", "amount": 1000}
"""

from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.fx import convert_fx
from mini_bloomberg.functions.base import BloombergFunction


def _parse_ccy_args(ticker: str) -> tuple[str, str, float]:
    """
    Parse a positional argument string into (from_ccy, to_ccy, amount).

    Handles:
      "USDJPY"        -> ("USD", "JPY", 1.0)
      "USDJPY 1000"   -> ("USD", "JPY", 1000.0)
      "USD JPY"       -> ("USD", "JPY", 1.0)
      "USD JPY 1000"  -> ("USD", "JPY", 1000.0)
      "USD"           -> ("USD", "USD", 1.0)  [will error gracefully downstream]
      "EURUSD=X"      -> ("EUR", "USD", 1.0)
    """
    # normalise
    s = ticker.upper().replace("=X", "").replace("/", " ").replace("-", " ")
    tokens = s.split()

    amount = 1.0
    ccys: list[str] = []

    for tok in tokens:
        try:
            amount = float(tok)
        except ValueError:
            # Could be "USDJPY" (6-char) or "USD" (3-char)
            clean = tok.replace(" ", "")
            if len(clean) == 6 and clean.isalpha():
                ccys.append(clean[:3])
                ccys.append(clean[3:])
            elif len(clean) == 3 and clean.isalpha():
                ccys.append(clean)

    if len(ccys) >= 2:
        return ccys[0], ccys[1], amount
    if len(ccys) == 1:
        return ccys[0], "USD", amount

    raise ValueError(
        f"Cannot parse currencies from '{ticker}'. "
        "Use 'USD JPY', 'USDJPY', 'USD JPY 1000', or '--from USD --to JPY --amount 1000'."
    )


class FXCA(BloombergFunction):
    name = "FXCA"
    description = (
        "FX Calculator -- convert an amount from one currency to another "
        "at the current spot rate. "
        "Accepts: USD JPY 1000  |  USDJPY 1000  |  USDJPY  |  --from USD --to JPY --amount 1000."
    )

    def run(
        self,
        ticker: str | None = None,
        amount: float = 1.0,
        from_ccy: str | None = None,
        to_ccy: str | None = None,
        pair: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Resolve currencies and amount from whichever input form was supplied.

        Priority order:
          1. explicit from_ccy + to_ccy keyword args
          2. pair keyword arg, e.g. pair="USDJPY"
          3. ticker positional string from the CLI dispatcher
          4. Hard-coded fallback: USD -> EUR
        """
        try:
            if from_ccy is not None and to_ccy is not None:
                resolved_from  = from_ccy.upper().strip()
                resolved_to    = to_ccy.upper().strip()
                resolved_amount = amount

            elif pair is not None:
                resolved_from, resolved_to, resolved_amount = _parse_ccy_args(pair)
                if amount != 1.0:          # explicit --amount flag overrides
                    resolved_amount = amount

            elif ticker is not None:
                resolved_from, resolved_to, resolved_amount = _parse_ccy_args(ticker)
                if amount != 1.0:
                    resolved_amount = amount

            else:
                resolved_from, resolved_to, resolved_amount = "USD", "EUR", amount

            # Sanity checks
            for label, code in (("from", resolved_from), ("to", resolved_to)):
                if not (len(code) == 3 and code.isalpha()):
                    return {
                        "status": "error",
                        "message": (
                            f"'{code}' is not a valid ISO currency code for {label}. "
                            "Use a 3-letter code such as USD, EUR, JPY, GBP."
                        ),
                    }

            if resolved_from == resolved_to:
                return {
                    "status": "error",
                    "message": "from_ccy and to_ccy must be different currencies.",
                }

            result = convert_fx(amount=resolved_amount, from_ccy=resolved_from, to_ccy=resolved_to)
            return {"status": "ok", "data": result.model_dump()}

        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "fxca",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert (default 1.0)",
                        "default": 1.0,
                    },
                    "from_ccy": {
                        "type": "string",
                        "description": "Source currency ISO code, e.g. 'USD'.",
                    },
                    "to_ccy": {
                        "type": "string",
                        "description": "Target currency ISO code, e.g. 'JPY'.",
                    },
                    "pair": {
                        "type": "string",
                        "description": (
                            "Convenience: full pair string such as 'USDJPY' or 'USD/JPY'. "
                            "Ignored when 'from_ccy' and 'to_ccy' are also supplied."
                        ),
                    },
                },
                "required": [],
            },
        }
