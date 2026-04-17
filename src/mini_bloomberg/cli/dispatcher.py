"""
Dispatcher: parse a raw input line and route to the right handler.

Rules:
  "AAPL US Equity <GO>"  → load security into session
  "DES <GO>"             → run Bloomberg function
  "? <query> <GO>"       → run LLM agent
  "HELP <GO>"            → print help table
  "QUIT <GO>" / "EXIT"   → exit REPL
  "<GO>" alone           → re-run last command (not implemented in v1, ignored)

Input is normalised: strip whitespace, strip trailing "<GO>" / "GO", uppercase.
"""

from mini_bloomberg.core.errors import MiniBloombergError, NoLoadedSecurityError, TickerError
from mini_bloomberg.core.session import session
from mini_bloomberg.core.ticker import parse_ticker
from mini_bloomberg.render.cli_renderer import (
    console, render_anr, render_comp, render_des, render_fa, render_gp,
    render_error, render_loaded, render_status, ORANGE, HEADER, DIM, GREEN,
)

from rich.table import Table
from rich.panel import Panel

# ── Function registry ──────────────────────────────────────────────────────────

def _registry():
    from mini_bloomberg.functions.des  import DES
    from mini_bloomberg.functions.fa   import FA
    from mini_bloomberg.functions.gp   import GP
    from mini_bloomberg.functions.anr  import ANR
    from mini_bloomberg.functions.comp import COMP
    return {"DES": DES, "FA": FA, "GP": GP, "ANR": ANR, "COMP": COMP}

RENDERERS = {
    "DES": render_des,
    "FA":  render_fa,
    "GP":  render_gp,
    "ANR": render_anr,
    "COMP": render_comp,
}

ASSET_CLASSES = {"EQUITY", "BOND", "COMDTY", "CURNCY", "INDEX"}


# ── Normalise input ────────────────────────────────────────────────────────────

def _normalise(raw: str) -> str:
    """Strip trailing <GO> / GO and extra whitespace."""
    s = raw.strip()
    if s.upper().endswith("<GO>"):
        s = s[:-4].strip()
    elif s.upper().endswith("GO"):
        # only strip bare "GO" if preceded by whitespace
        if len(s) > 2 and s[-3] == " ":
            s = s[:-2].strip()
    return s


# ── Ticker detection ───────────────────────────────────────────────────────────

def _looks_like_ticker(tokens: list[str]) -> bool:
    """
    Heuristic: 2–3 tokens where the last is an asset class keyword,
    or a single token that is 1–5 uppercase letters/digits with no spaces.
    """
    if not tokens:
        return False
    if len(tokens) >= 2 and tokens[-1].upper() in ASSET_CLASSES:
        return True
    if len(tokens) == 1:
        t = tokens[0]
        return t.isalnum() and t.isupper() and 1 <= len(t) <= 6
    return False


# ── Main dispatch ──────────────────────────────────────────────────────────────

def dispatch(raw: str) -> bool:
    """
    Process one input line. Returns False if the REPL should exit, True otherwise.
    """
    line = _normalise(raw)
    if not line:
        return True

    upper = line.upper()

    # ── Exit ─────────────────────────────────────────────────────────────────
    if upper in ("QUIT", "EXIT", "Q"):
        console.print(f"[{DIM}]Goodbye.[/{DIM}]")
        return False

    # ── Help ─────────────────────────────────────────────────────────────────
    if upper == "HELP":
        _render_help()
        return True

    # ── Agent mode: "? <query>" ───────────────────────────────────────────────
    if line.startswith("?"):
        query = line[1:].strip()
        if not query:
            render_error("Usage: ? <your question>  e.g. ? compare NVDA and AMD margins")
            return True
        _run_agent(query)
        return True

    # ── Bloomberg function: "DES", "FA 4", "GP --days 90" etc. ───────────────
    tokens = line.split()
    cmd = tokens[0].upper()
    registry = _registry()

    if cmd in registry:
        kwargs = _parse_function_kwargs(cmd, tokens[1:])
        fn_class = registry[cmd]
        renderer = RENDERERS[cmd]
        try:
            result = fn_class().run(**kwargs)
            renderer(result)
        except NoLoadedSecurityError as e:
            render_error(str(e))
        except Exception as e:
            render_error(f"Unexpected error running {cmd}: {e}")
        return True

    # ── Load security: "AAPL US Equity" ──────────────────────────────────────
    if _looks_like_ticker(tokens):
        try:
            t = session.load(line)
            render_loaded(str(t))
        except TickerError as e:
            render_error(str(e))
        return True

    # ── Unknown ───────────────────────────────────────────────────────────────
    render_error(
        f"Unknown command '{cmd}'. "
        "Type HELP <GO> for available commands, or load a ticker first."
    )
    return True


def _parse_function_kwargs(cmd: str, args: list[str]) -> dict:
    """
    Extract optional ticker and numeric params from remaining tokens.
    E.g. "FA AAPL US Equity" → {ticker: "AAPL US Equity"}
         "GP --days 90"      → {days: 90}
         "DES"               → {}  (uses session)
    """
    kwargs: dict = {}

    # Check if first arg looks like a ticker (word + optional exchange code)
    if args and not args[0].startswith("-"):
        # Could be ticker tokens: consume until we hit a flag or end
        ticker_parts = []
        remaining = []
        for i, token in enumerate(args):
            if token.startswith("-"):
                remaining = args[i:]
                break
            ticker_parts.append(token)
        else:
            remaining = []

        if ticker_parts:
            candidate = " ".join(ticker_parts)
            try:
                parse_ticker(candidate)
                kwargs["ticker"] = candidate
                args = remaining
            except TickerError:
                args = ticker_parts + remaining  # put back, not a ticker

    # Parse --days / --years flags
    i = 0
    while i < len(args):
        tok = args[i].lstrip("-")
        if tok in ("days", "d") and i + 1 < len(args):
            try:
                kwargs["days"] = int(args[i + 1])
                i += 2
                continue
            except ValueError:
                pass
        if tok in ("years", "y") and i + 1 < len(args):
            try:
                kwargs["years"] = int(args[i + 1])
                i += 2
                continue
            except ValueError:
                pass
        i += 1

    return kwargs


def _render_help() -> None:
    t = Table(border_style="dim", header_style=HEADER, show_lines=False, expand=False)
    t.add_column("Command",     style=ORANGE, min_width=16, no_wrap=True)
    t.add_column("Description", style=DIM,    min_width=42)
    t.add_column("Example",     style=GREEN,  min_width=24, no_wrap=True)

    rows = [
        ("<TICKER> <GO>", "Load a security into the session",          "AAPL US Equity <GO>"),
        ("DES <GO>",      "Company description and key stats",         "DES <GO>"),
        ("FA <GO>",       "Financial analysis (income/balance/CF)",    "FA <GO>"),
        ("GP <GO>",       "ASCII price chart (default 1 year)",        "GP --days 90 <GO>"),
        ("ANR <GO>",      "Analyst ratings and price targets",         "ANR <GO>"),
        ("COMP <GO>",     "Comparable companies side-by-side",         "COMP <GO>"),
        ("? <query>",     "Ask the AI analyst a question",             "? compare NVDA AMD <GO>"),
        ("HELP <GO>",     "Show this help screen",                     "HELP <GO>"),
        ("QUIT <GO>",     "Exit Mini-Bloomberg",                       "QUIT <GO>"),
    ]
    for row in rows:
        t.add_row(*row)

    console.print()
    console.print(Panel(
        t,
        title=f"[{ORANGE}]HELP[/{ORANGE}]  [{HEADER}]Mini-Bloomberg Commands[/{HEADER}]",
        border_style="yellow",
        padding=(1, 2),
    ))
    console.print()


def _run_agent(query: str) -> None:
    try:
        from mini_bloomberg.agents.orchestrator import run_agent
        run_agent(query)
    except ImportError:
        render_error("Agent not yet implemented (Milestone 6).")
    except Exception as e:
        render_error(f"Agent error: {e}")
