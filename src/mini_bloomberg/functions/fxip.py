"""FXIP — FX Information & Pricing.

Multi-currency spot rate monitor. Supports G10, EM, all, or a custom
list of currencies. Equivalent to Bloomberg's FXIP multi-currency dashboard.

Accepted input styles
---------------------
Positional (recommended):
    FXIP <GO>                  # G10 vs USD (defaults)
    FXIP g10 <GO>              # G10 vs USD
    FXIP em <GO>               # EM vs USD
    FXIP all <GO>              # G10 + EM vs USD
    FXIP em EUR <GO>           # EM currencies vs EUR
    FXIP g10 JPY <GO>          # G10 currencies vs JPY
    FXIP USD <GO>              # bare quote ccy -> G10 vs USD
    FXIP EUR <GO>              # bare quote ccy -> G10 vs EUR

Via flags (also accepted):
    FXIP --group em --quote EUR <GO>

Via LLM tool call:
    {"group": "em", "quote": "EUR"}

Positional parsing rules
------------------------
Token 1 (optional): group keyword (g10 | em | all) OR a 3-letter ccy code (treated as quote)
Token 2 (optional): 3-letter quote currency ISO code
"""

from mini_bloomberg.core.errors import DataSourceError, MiniBloombergError
from mini_bloomberg.data.fx import G10_CURRENCIES, EM_CURRENCIES, get_fx_board
from mini_bloomberg.functions.base import BloombergFunction

ALL_KNOWN_CURRENCIES = sorted(set(G10_CURRENCIES + EM_CURRENCIES))
EXTRA_CURRENCIES = [
    "HKD", "SGD", "CNY", "INR", "KRW", "IDR", "THB", "PHP",
    "MYR", "VND", "AED", "SAR", "ILS", "QAR", "KWD",
]
_DISPLAY_CURRENCIES = sorted(set(ALL_KNOWN_CURRENCIES + EXTRA_CURRENCIES))

_GROUPS = {"g10", "em", "all"}


def _parse_fxip_args(ticker: str) -> tuple[str, str]:
    """
    Parse positional ticker string into (group, quote).

    Examples:
      ""           -> ("g10", "USD")
      "g10"        -> ("g10", "USD")
      "em"         -> ("em",  "USD")
      "all"        -> ("all", "USD")
      "EUR"        -> ("g10", "EUR")   # bare 3-letter ccy -> quote
      "em EUR"     -> ("em",  "EUR")
      "g10 JPY"    -> ("g10", "JPY")
      "USD"        -> ("g10", "USD")   # bare USD -> quote
    """
    tokens = ticker.upper().strip().split()
    group = "g10"
    quote = "USD"

    for tok in tokens:
        if tok.lower() in _GROUPS:
            group = tok.lower()
        elif len(tok) == 3 and tok.isalpha():
            quote = tok

    return group, quote


class FXIP(BloombergFunction):
    name = "FXIP"
    description = (
        "FX Information & Pricing -- spot rates, daily change, and 52-week range "
        "for G10, EM, or all currencies vs a chosen quote currency. "
        "Accepts: FXIP  |  FXIP em  |  FXIP g10 EUR  |  FXIP em JPY  |  --group em --quote EUR."
    )

    def run(
        self,
        ticker: str | None = None,
        group: str = "g10",
        quote: str | None = None,
        currencies: list[str] | None = None,
        **kwargs,
    ) -> dict:
        """
        Resolve group and quote from whichever input form was supplied.

        Priority order:
          1. explicit group + quote keyword args
          2. ticker positional string from the CLI dispatcher
          3. Defaults: g10 / USD
        """
        try:
            # If ticker carries positional args, let them override defaults
            if ticker is not None:
                parsed_group, parsed_quote = _parse_fxip_args(ticker)
                # only override if the caller didn't supply explicit kwargs
                if group == "g10":    # still at default
                    group = parsed_group
                if quote is None:
                    quote = parsed_quote

            if quote is None:
                quote = "USD"
            quote = quote.upper().strip()
            group = group.lower().strip()

            if group == "em":
                base_currencies = list(EM_CURRENCIES)
            elif group == "all":
                base_currencies = list(G10_CURRENCIES) + list(EM_CURRENCIES)
            elif group == "custom":
                base_currencies = [c.upper().strip() for c in currencies] if currencies else list(G10_CURRENCIES)
            else:
                base_currencies = list(G10_CURRENCIES)

            base_currencies = [c for c in base_currencies if c != quote]

            if not base_currencies:
                return {"status": "error", "message": "No base currencies selected."}

            pairs = [(ccy, quote) for ccy in base_currencies]
            board = get_fx_board(pairs=pairs)
            return {
                "status": "ok",
                "data": board.model_dump(),
                "group": group,
                "quote": quote,
                "currencies": base_currencies,
            }

        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "fxip",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": "Currency group: 'g10' (default), 'em', 'all', or 'custom'.",
                        "enum": ["g10", "em", "all", "custom"],
                        "default": "g10",
                    },
                    "quote": {
                        "type": "string",
                        "description": "Counter currency ISO code (default 'USD').",
                        "default": "USD",
                    },
                    "currencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Explicit list of base currency ISO codes. "
                            "Only used when group='custom', e.g. ['EUR', 'GBP', 'SGD']."
                        ),
                    },
                },
                "required": [],
            },
        }
