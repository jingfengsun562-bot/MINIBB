"""WCR — World Currency Ranker.

Rank currencies by % performance vs a chosen base currency over 1D / 1W / 1M / 3M / YTD.
Supports G10, EM, combined, or a custom selection of currencies.
Equivalent to Bloomberg's WCR function.

Accepted input styles
---------------------
Positional (recommended):
    WCR <GO>                   # G10 vs USD sorted by 1D (defaults)
    WCR EUR <GO>               # G10 vs EUR sorted by 1D
    WCR em <GO>                # EM vs USD sorted by 1D
    WCR em EUR <GO>            # EM vs EUR sorted by 1D
    WCR g10 JPY 1m <GO>        # G10 vs JPY sorted by 1M
    WCR all USD 1w <GO>        # all currencies vs USD sorted by 1W

Via flags (also accepted):
    WCR --group em --quote EUR --sort-by 1m <GO>

Via LLM tool call:
    {"group": "em", "quote": "EUR", "sort_by": "1m"}

Positional parsing rules
------------------------
Tokens (all optional, order flexible):
  - group keyword: g10 | em | all
  - sort horizon:  1d | 1w | 1m | 3m | ytd
  - quote ccy:     any remaining 2-3 letter token treated as ISO ccy code
"""

from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.fx import G10_CURRENCIES, EM_CURRENCIES, get_fx_ranking
from mini_bloomberg.functions.base import BloombergFunction

_GROUPS   = {"g10", "em", "all"}
_HORIZONS = {"1d", "1w", "1m", "3m", "ytd"}


def _parse_wcr_args(ticker: str) -> tuple[str, str, str]:
    """
    Parse positional ticker string into (group, quote, sort_by).

    Examples:
      ""            -> ("g10", "USD", "1d")
      "EUR"         -> ("g10", "EUR", "1d")
      "em"          -> ("em",  "USD", "1d")
      "em EUR"      -> ("em",  "EUR", "1d")
      "g10 JPY 1m"  -> ("g10", "JPY", "1m")
      "all USD 1w"  -> ("all", "USD", "1w")
      "1m"          -> ("g10", "USD", "1m")
    """
    tokens = ticker.upper().strip().split()
    group   = "g10"
    quote   = "USD"
    sort_by = "1d"

    for tok in tokens:
        low = tok.lower()
        if low in _GROUPS:
            group = low
        elif low in _HORIZONS:
            sort_by = low
        elif len(tok) <= 3 and tok.isalpha():
            quote = tok

    return group, quote, sort_by


class WCR(BloombergFunction):
    name = "WCR"
    description = (
        "World Currency Ranker -- rank currencies by % performance vs a chosen "
        "currency over 1D, 1W, 1M, 3M, and YTD horizons. "
        "Accepts: WCR  |  WCR EUR  |  WCR em  |  WCR em EUR  |  WCR g10 JPY 1m  |  --group em --quote EUR --sort-by 1m."
    )

    def run(
        self,
        ticker: str | None = None,
        group: str = "g10",
        sort_by: str = "1d",
        quote: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Resolve group, quote, and sort_by from whichever input form was supplied.

        Priority order:
          1. explicit keyword args (group, quote, sort_by)
          2. ticker positional string from the CLI dispatcher
          3. Defaults: g10 / USD / 1d
        """
        try:
            if ticker is not None:
                parsed_group, parsed_quote, parsed_sort = _parse_wcr_args(ticker)
                if group == "g10":      # still at default -> use parsed
                    group = parsed_group
                if quote is None:
                    quote = parsed_quote
                if sort_by == "1d":     # still at default -> use parsed
                    sort_by = parsed_sort

            if quote is None:
                quote = "USD"
            quote   = quote.upper().strip()
            group   = group.lower().strip()
            sort_by = sort_by.lower().strip()

            if group == "em":
                currencies = list(EM_CURRENCIES)
            elif group == "all":
                currencies = list(G10_CURRENCIES) + list(EM_CURRENCIES)
            else:
                currencies = list(G10_CURRENCIES)

            currencies = [c for c in currencies if c != quote]

            ranking = get_fx_ranking(currencies=currencies, quote=quote)

            sort_field_map = {
                "1d": "change_1d", "1w": "change_1w",
                "1m": "change_1m", "3m": "change_3m", "ytd": "change_ytd",
            }
            field = sort_field_map.get(sort_by, "change_1d")
            ranking.rows.sort(
                key=lambda r: getattr(r, field) or 0,
                reverse=True,
            )

            return {
                "status": "ok",
                "data": ranking.model_dump(),
                "group": group,
                "sort_by": sort_by,
                "quote": quote,
            }

        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "wcr",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": "Currency universe: 'g10' (default), 'em', or 'all'",
                        "enum": ["g10", "em", "all"],
                        "default": "g10",
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Sort horizon: '1d' (default), '1w', '1m', '3m', 'ytd'",
                        "enum": ["1d", "1w", "1m", "3m", "ytd"],
                        "default": "1d",
                    },
                    "quote": {
                        "type": "string",
                        "description": "Currency to rank all others against (default 'USD').",
                        "default": "USD",
                    },
                },
                "required": [],
            },
        }
