"""FXHV — FX Historical Volatility.

Annualised realised volatility for an FX pair over 10d / 20d / 30d / 60d / 90d / 180d / 1Y.
Equivalent to Bloomberg's FXHV function.
"""

from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.fx import get_fx_volatility
from mini_bloomberg.functions.base import BloombergFunction

# Common currency choices presented to the user
CURRENCY_CHOICES = [
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD",
    "HKD", "SGD", "SEK", "NOK", "DKK", "MXN", "BRL", "ZAR",
    "CNY", "INR", "KRW", "TRY",
]


class FXHV(BloombergFunction):
    name = "FXHV"
    description = (
        "FX Historical Volatility — annualised realised vol for a currency pair "
        "over 10d, 20d, 30d, 60d, 90d, 180d, and 1Y rolling windows."
    )

    def run(
        self,
        ticker: str | None = None,
        base: str | None = None,
        quote: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Args:
            base:  base currency, e.g. "EUR".
                   If omitted, the user is prompted to pick from a list.
            quote: counter currency, e.g. "USD".
                   If omitted, the user is prompted to pick from a list.
        """
        if base is None:
            base = self._prompt_currency("base currency")
        if quote is None:
            quote = self._prompt_currency("quote (counter) currency")

        base = base.upper().strip()
        quote = quote.upper().strip()

        if base == quote:
            return {
                "status": "error",
                "message": "base and quote must be different currencies.",
            }

        try:
            vol = get_fx_volatility(base=base, quote=quote)
            return {"status": "ok", "data": vol.model_dump()}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prompt_currency(self, label: str) -> str:
        """Display a numbered menu and return the chosen ISO code."""
        print(f"\nSelect {label}:")
        for i, ccy in enumerate(CURRENCY_CHOICES, start=1):
            print(f"  {i:>2}. {ccy}")
        print(f"   0. Enter a custom currency code")

        while True:
            raw = input("Choice: ").strip()
            if raw == "0":
                code = input("Enter ISO currency code: ").strip().upper()
                if code:
                    return code
            elif raw.isdigit():
                idx = int(raw)
                if 1 <= idx <= len(CURRENCY_CHOICES):
                    return CURRENCY_CHOICES[idx - 1]
            elif raw.upper() in CURRENCY_CHOICES or (raw.isalpha() and len(raw) == 3):
                return raw.upper()
            print("  Invalid choice — please try again.")

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
                            f"Common choices: {', '.join(CURRENCY_CHOICES)}. "
                            "Any valid ISO 4217 code is accepted."
                        ),
                    },
                    "quote": {
                        "type": "string",
                        "description": (
                            "Counter currency ISO code, e.g. 'USD'. "
                            f"Common choices: {', '.join(CURRENCY_CHOICES)}. "
                            "Any valid ISO 4217 code is accepted."
                        ),
                        "default": "USD",
                    },
                },
                "required": ["base"],
            },
        }
