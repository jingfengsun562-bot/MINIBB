"""WCR — World Currency Ranker.

Rank currencies by % performance vs a chosen base currency over 1D / 1W / 1M / 3M / YTD.
Supports G10, EM, combined, or a custom selection of currencies.
Equivalent to Bloomberg's WCR function.
"""

from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.fx import G10_CURRENCIES, EM_CURRENCIES, get_fx_ranking
from mini_bloomberg.functions.base import BloombergFunction

# Currencies the user can choose as the comparison (quote) leg
QUOTE_CHOICES = [
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD",
    "HKD", "SGD", "CNY", "SEK", "NOK", "DKK",
]


class WCR(BloombergFunction):
    name = "WCR"
    description = (
        "World Currency Ranker — rank currencies by % performance vs a chosen "
        "currency over 1D, 1W, 1M, 3M, and YTD horizons."
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
        Args:
            group:   "g10" (default) | "em" | "all"
            sort_by: "1d" (default) | "1w" | "1m" | "3m" | "ytd"
            quote:   currency to rank against, e.g. "EUR", "JPY".
                     Defaults to "USD". If omitted interactively, the user
                     is prompted to choose from a list.
        """
        # Resolve quote currency — prompt if not supplied
        if quote is None:
            quote = self._prompt_quote_currency()
        quote = quote.upper().strip()

        try:
            group = group.lower()
            if group == "em":
                currencies = list(EM_CURRENCIES)
            elif group == "all":
                currencies = list(G10_CURRENCIES) + list(EM_CURRENCIES)
            else:
                currencies = list(G10_CURRENCIES)

            # Exclude the quote currency itself from the ranking
            currencies = [c for c in currencies if c != quote]

            ranking = get_fx_ranking(currencies=currencies, quote=quote)

            # Re-sort by the requested horizon
            sort_by = sort_by.lower()
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prompt_quote_currency(self) -> str:
        """Display a numbered menu and return the chosen quote ISO code."""
        print("\nSelect comparison (quote) currency:")
        for i, ccy in enumerate(QUOTE_CHOICES, start=1):
            print(f"  {i:>2}. {ccy}")
        print("   0. Enter a custom currency code")

        while True:
            raw = input("Choice [default USD]: ").strip()
            if raw == "":
                return "USD"
            if raw == "0":
                code = input("Enter ISO currency code: ").strip().upper()
                if code:
                    return code
            elif raw.isdigit():
                idx = int(raw)
                if 1 <= idx <= len(QUOTE_CHOICES):
                    return QUOTE_CHOICES[idx - 1]
            elif raw.upper() in QUOTE_CHOICES or (raw.isalpha() and len(raw) == 3):
                return raw.upper()
            print("  Invalid choice — please try again.")

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
                        "description": (
                            "Currency to rank all others against (default 'USD'). "
                            f"Common choices: {', '.join(QUOTE_CHOICES)}. "
                            "Any valid ISO 4217 code is accepted."
                        ),
                        "default": "USD",
                    },
                },
                "required": [],
            },
        }
