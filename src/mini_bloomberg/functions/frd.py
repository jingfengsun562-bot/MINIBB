"""FRD — Forward Rates.

CIP-implied forward rate curve (O/N → 1Y) for any currency pair.
Uses Covered Interest Parity: F = S × (1 + r_quote × T) / (1 + r_base × T)

Now includes an optional ASCII/matplotlib forward curve chart.

NOTE: Bloomberg's FRD uses live OIS/SOFR swap points from interbank market.
      This implementation approximates using static reference rates, which is
      sufficient for educational/indicative use. Displayed with a disclaimer.

Equivalent to Bloomberg's FRD function.

Accepted input styles
---------------------
Via CLI flags (recommended):
    FRD --base EUR --quote USD <GO>
    FRD --base GBP <GO>               # quote defaults to USD

Via positional pair string (convenience):
    FRD EURUSD <GO>                   # 6-char concatenated pair
    FRD EUR USD <GO>                  # two separate tokens
    FRD EURUSD=X <GO>                 # yfinance-style ticker, = and X stripped

Via LLM tool call:
    {"base": "EUR", "quote": "JPY"}

Chart output
------------
Pass --chart (CLI) or chart=True (tool call) to render a forward curve chart.
Requires matplotlib. Falls back gracefully to ASCII if unavailable.
"""

from mini_bloomberg.core.errors import DataSourceError, MiniBloombergError
from mini_bloomberg.data.fx import get_fx_forward_curve
from mini_bloomberg.functions.base import BloombergFunction


def _parse_pair(pair_str: str) -> tuple[str, str]:
    """
    Parse a currency pair string into (base, quote).

    Handles:
      "EURUSD"     → ("EUR", "USD")
      "EURUSD=X"   → ("EUR", "USD")
      "EUR/USD"    → ("EUR", "USD")
      "EUR-USD"    → ("EUR", "USD")
      "EUR USD"    → ("EUR", "USD")   # two tokens joined before calling
      "EUR"        → ("EUR", "USD")   # bare base, USD assumed
    """
    s = pair_str.upper().replace("=X", "").replace("/", "").replace("-", "").replace(" ", "")

    if len(s) == 6:
        return s[:3], s[3:]
    if len(s) == 3:
        return s, "USD"

    raise ValueError(
        f"Cannot parse currency pair '{pair_str}'. "
        "Use 'EURUSD', 'EUR/USD', '--base EUR --quote USD', or 'EUR USD'."
    )


def _chart_matplotlib(curve) -> None:
    """Render an interactive matplotlib forward curve chart."""
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    tenors = [t.tenor for t in curve.tenors]
    fwd_rates = [t.forward_rate for t in curve.tenors]
    fwd_pts = [t.forward_points for t in curve.tenors]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    fig.suptitle(
        f"FRD — {curve.pair}  Forward Curve\n"
        f"Spot: {curve.spot:.5f}   As of: {curve.as_of}",
        fontsize=13, fontweight="bold",
    )

    # ── Top panel: forward rates ──────────────────────────────────────
    ax1.plot(tenors, fwd_rates, marker="o", color="#2196F3", linewidth=2,
             markersize=6, label="Forward Rate")
    ax1.axhline(curve.spot, color="#FF5722", linewidth=1.2, linestyle="--",
                label=f"Spot ({curve.spot:.5f})")
    ax1.set_ylabel("Forward Rate", fontsize=10)
    ax1.legend(fontsize=9)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.5f"))
    ax1.grid(True, alpha=0.3)
    for i, (x, y) in enumerate(zip(tenors, fwd_rates)):
        ax1.annotate(f"{y:.5f}", xy=(x, y), xytext=(0, 8),
                     textcoords="offset points", ha="center", fontsize=7.5,
                     color="#2196F3")

    # ── Bottom panel: forward points ──────────────────────────────────
    colors = ["#4CAF50" if p >= 0 else "#F44336" for p in fwd_pts]
    bars = ax2.bar(tenors, fwd_pts, color=colors, alpha=0.75, width=0.6)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Forward Points (pips)", fontsize=10)
    ax2.set_xlabel("Tenor", fontsize=10)
    ax2.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars, fwd_pts):
        ypos = val + (max(fwd_pts) * 0.02) if val >= 0 else val - (max(abs(p) for p in fwd_pts) * 0.05)
        ax2.text(bar.get_x() + bar.get_width() / 2, ypos,
                 f"{val:+.1f}", ha="center", va="bottom", fontsize=7.5)

    fig.text(
        0.5, 0.01,
        "⚠  CIP-approximated using reference rates — indicative only.",
        ha="center", fontsize=8, color="gray",
    )
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.show()


def _chart_ascii(curve) -> None:
    """Fallback ASCII chart when matplotlib is unavailable."""
    tenors = [t.tenor for t in curve.tenors]
    fwd_rates = [t.forward_rate for t in curve.tenors]
    fwd_pts = [t.forward_points for t in curve.tenors]

    print(f"\n{'─'*55}")
    print(f"  FRD — {curve.pair} Forward Curve   (spot: {curve.spot:.5f})")
    print(f"  As of: {curve.as_of}")
    print(f"{'─'*55}")
    print(f"  {'Tenor':<6}  {'Fwd Rate':>10}  {'Fwd Pts':>10}  Bar")
    print(f"{'─'*55}")

    max_abs = max(abs(p) for p in fwd_pts) or 1
    bar_width = 20

    for tenor, rate, pts in zip(tenors, fwd_rates, fwd_pts):
        filled = int(abs(pts) / max_abs * bar_width)
        if pts >= 0:
            bar = "█" * filled
            bar_str = f"{'':>{bar_width}}│{bar:<{bar_width}}"
        else:
            bar = "█" * filled
            bar_str = f"{bar:>{bar_width}}│{'':>{bar_width}}"
        print(f"  {tenor:<6}  {rate:>10.5f}  {pts:>+10.2f}  {bar_str}")

    print(f"{'─'*55}")
    print("  ⚠  CIP-approximated — indicative only.\n")


class FRD(BloombergFunction):
    name = "FRD"
    description = (
        "Forward Rates — CIP-implied FX forward curve (O/N to 1Y) showing "
        "forward rate, forward points, and implied yield differential by tenor. "
        "Accepts: --base EUR --quote USD  |  EURUSD  |  EUR USD. "
        "Pass --chart or chart=True to render a forward curve chart."
    )

    def run(
        self,
        ticker: str | None = None,
        base: str | None = None,
        quote: str = "USD",
        pair: str | None = None,
        chart: bool = False,
        **kwargs,
    ) -> dict:
        """
        Resolve the currency pair from whichever input form was supplied,
        then fetch and return the forward curve.

        Priority order:
          1. explicit ``base`` (+ optional ``quote``) keyword args
          2. ``pair`` keyword arg, e.g. pair="EURUSD"
          3. ``ticker`` positional string passed by the CLI dispatcher
          4. Hard-coded fallback: EUR/USD

        Args:
            chart: set True to render a forward curve chart (matplotlib
                   with ASCII fallback). Default False.
        """
        try:
            resolved_base: str
            resolved_quote: str

            if base is not None:
                resolved_base  = base.upper().strip()
                resolved_quote = quote.upper().strip()

            elif pair is not None:
                resolved_base, resolved_quote = _parse_pair(pair)

            elif ticker is not None:
                resolved_base, resolved_quote = _parse_pair(ticker.replace(" ", ""))

            else:
                resolved_base, resolved_quote = "EUR", "USD"

            # Sanity check
            for label, code in (("base", resolved_base), ("quote", resolved_quote)):
                if not (len(code) == 3 and code.isalpha()):
                    return {
                        "status": "error",
                        "message": (
                            f"'{code}' is not a valid ISO currency code for {label}. "
                            "Use a 3-letter code such as EUR, USD, JPY, GBP."
                        ),
                    }

            curve = get_fx_forward_curve(base=resolved_base, quote=resolved_quote)

            # ── Chart rendering ───────────────────────────────────────────
            if chart:
                try:
                    _chart_matplotlib(curve)
                except ImportError:
                    _chart_ascii(curve)

            return {
                "status": "ok",
                "data": curve.model_dump(),
                "note": (
                    "Forward rates are CIP-approximated using reference rates. "
                    "Live Bloomberg FRD uses real interbank swap points."
                ),
            }

        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except MiniBloombergError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def tool_schema(self) -> dict:
        return {
            "name": "frd",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "base": {
                        "type": "string",
                        "description": (
                            "Base currency ISO code, e.g. 'EUR', 'GBP', 'JPY'. "
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
                    "chart": {
                        "type": "boolean",
                        "description": (
                            "Render a forward curve chart (matplotlib with ASCII fallback). "
                            "Default false."
                        ),
                        "default": False,
                    },
                },
                "required": [],
            },
        }
