"""FXCA — FX Calculator.

Convert amounts between any two currencies at the current spot rate.
Routes through USD if a direct quote is unavailable.
Equivalent to Bloomberg's FXCA currency converter.
"""

from mini_bloomberg.core.errors import MiniBloombergError
from mini_bloomberg.data.fx import convert_fx
from mini_bloomberg.functions.base import BloombergFunction

# Common currency choices presented to the user
CURRENCY_CHOICES = [
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD",
    "HKD", "SGD", "SEK", "NOK", "DKK", "MXN", "BRL", "ZAR",
    "CNY", "INR", "KRW", "TRY",
]


class FXCA(BloombergFunction):
    name = "FXCA"
    description = (
        "FX Calculator — convert an amount from one currency to another "
        "at the current spot rate."
    )

    def run(
        self,
        ticker: str | None = None,
        amount: float = 1.0,
        from_ccy: str | None = None,
        to_ccy: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Args:
            amount:   amount to convert (default 1.0)
            from_ccy: source currency ISO code (e.g. "USD").
                      If omitted, the user is prompted to pick from a list.
            to_ccy:   target currency ISO code (e.g. "EUR").
                      If omitted, the user is prompted to pick from a list.
        """
        # Prompt for missing currencies interactively
        if from_ccy is None:
            from_ccy = self._prompt_currency("source (from) currency")
        if to_ccy is None:
            to_ccy = self._prompt_currency("target (to) currency")

        from_ccy = from_ccy.upper().strip()
        to_ccy = to_ccy.upper().strip()

        if from_ccy == to_ccy:
            return {
                "status": "error",
                "message": "from_ccy and to_ccy must be different currencies.",
            }

        try:
            result = convert_fx(amount=amount, from_ccy=from_ccy, to_ccy=to_ccy)
            return {"status": "ok", "data": result.model_dump()}
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
            # Also accept a direct ISO code typed by the user
            elif raw.upper() in CURRENCY_CHOICES or (raw.isalpha() and len(raw) == 3):
                return raw.upper()
            print("  Invalid choice — please try again.")

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
                        "description": (
                            "Source currency ISO code, e.g. 'USD'. "
                            f"Common choices: {', '.join(CURRENCY_CHOICES)}. "
                            "Any valid ISO 4217 code is accepted."
                        ),
                    },
                    "to_ccy": {
                        "type": "string",
                        "description": (
                            "Target currency ISO code, e.g. 'EUR'. "
                            f"Common choices: {', '.join(CURRENCY_CHOICES)}. "
                            "Any valid ISO 4217 code is accepted."
                        ),
                    },
                },
                "required": ["from_ccy", "to_ccy"],
            },
        }
