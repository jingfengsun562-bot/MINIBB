"""FXIP — FX Information & Pricing.

Multi-currency spot rate monitor. Supports G10, EM, all, or a custom
list of currencies chosen interactively.
Equivalent to Bloomberg's FXIP multi-currency dashboard.
"""

from mini_bloomberg.core.errors import DataSourceError, MiniBloombergError
from mini_bloomberg.data.fx import G10_CURRENCIES, EM_CURRENCIES, get_fx_board
from mini_bloomberg.functions.base import BloombergFunction

# Ordered list shown to the user when building a custom set
ALL_KNOWN_CURRENCIES = sorted(set(G10_CURRENCIES + EM_CURRENCIES))

# Additional currencies not in G10/EM lists but commonly requested
EXTRA_CURRENCIES = [
    "HKD", "SGD", "CNY", "INR", "KRW", "IDR", "THB", "PHP",
    "MYR", "VND", "AED", "SAR", "ILS", "QAR", "KWD",
]

_DISPLAY_CURRENCIES = sorted(set(ALL_KNOWN_CURRENCIES + EXTRA_CURRENCIES))


class FXIP(BloombergFunction):
    name = "FXIP"
    description = (
        "FX Information & Pricing — spot rates, daily change, and 52-week range "
        "for G10, EM, all, or a custom selection of currencies vs a chosen quote."
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
        Args:
            group:      "g10" (default) | "em" | "all" | "custom"
                        Use "custom" to pick individual currencies interactively.
            quote:      counter currency (default "USD").
                        If omitted, the user is prompted to choose.
            currencies: explicit list of base currencies to use when group="custom"
                        and the caller supplies them directly (bypasses the prompt).
        """
        # Resolve quote currency
        if quote is None:
            quote = self._prompt_quote_currency()
        quote = quote.upper().strip()

        # Resolve base currencies
        group = group.lower().strip()
        if group == "em":
            base_currencies = list(EM_CURRENCIES)
        elif group == "all":
            base_currencies = list(G10_CURRENCIES) + list(EM_CURRENCIES)
        elif group == "custom":
            if currencies:
                base_currencies = [c.upper().strip() for c in currencies]
            else:
                base_currencies = self._prompt_custom_currencies(quote)
        else:
            # Default: g10
            base_currencies = list(G10_CURRENCIES)

        # Remove quote ccy from base list if present (e.g. USD vs USD makes no sense)
        base_currencies = [c for c in base_currencies if c != quote]

        if not base_currencies:
            return {"status": "error", "message": "No base currencies selected."}

        pairs = [(ccy, quote) for ccy in base_currencies]

        try:
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prompt_quote_currency(self) -> str:
        """Ask the user which currency to use as the quote (counter) leg."""
        common = ["USD", "EUR", "GBP", "JPY", "CHF"]
        print("\nSelect quote (counter) currency:")
        for i, ccy in enumerate(common, start=1):
            print(f"  {i}. {ccy}")
        print("  0. Enter a custom currency code")

        while True:
            raw = input("Choice [default USD]: ").strip()
            if raw == "" or raw.upper() == "USD":
                return "USD"
            if raw == "0":
                code = input("Enter ISO currency code: ").strip().upper()
                if code:
                    return code
            elif raw.isdigit():
                idx = int(raw)
                if 1 <= idx <= len(common):
                    return common[idx - 1]
            elif raw.upper() in _DISPLAY_CURRENCIES or (raw.isalpha() and len(raw) == 3):
                return raw.upper()
            print("  Invalid choice — please try again.")

    def _prompt_custom_currencies(self, quote: str) -> list[str]:
        """Interactive multi-select for base currencies."""
        available = [c for c in _DISPLAY_CURRENCIES if c != quote]
        print(f"\nAvailable currencies (quote: {quote}):")
        cols = 5
        for i, ccy in enumerate(available, start=1):
            end = "\n" if i % cols == 0 else "  "
            print(f"  {i:>3}. {ccy}", end=end)
        if len(available) % cols != 0:
            print()  # newline after last partial row

        print(
            "\nEnter numbers separated by spaces/commas, or type ISO codes directly."
            "\nExamples:  1 3 5     or     USD EUR GBP     or     1,4,EUR"
        )

        selected: list[str] = []
        while not selected:
            raw = input("Your selection: ").strip()
            tokens = raw.replace(",", " ").split()
            for token in tokens:
                if token.isdigit():
                    idx = int(token)
                    if 1 <= idx <= len(available):
                        ccy = available[idx - 1]
                        if ccy not in selected:
                            selected.append(ccy)
                elif token.upper() in _DISPLAY_CURRENCIES or (token.isalpha() and len(token) == 3):
                    ccy = token.upper()
                    if ccy not in selected:
                        selected.append(ccy)
            if not selected:
                print("  No valid currencies found — please try again.")

        print(f"\nSelected: {', '.join(selected)}")
        return selected

    def tool_schema(self) -> dict:
        return {
            "name": "fxip",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": (
                            "Currency group: 'g10' (default), 'em', 'all', or 'custom'. "
                            "Use 'custom' together with the 'currencies' field to specify "
                            "an arbitrary list."
                        ),
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
                            "Explicit list of base currency ISO codes to display. "
                            "Only used when group='custom', e.g. ['EUR', 'GBP', 'SGD']."
                        ),
                    },
                },
                "required": [],
            },
        }
