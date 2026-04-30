# CLAUDE.md

Rules and context for Claude Code to follow while building this project. Read this before touching any code. Re-read it before each new function.

---

## Project: Mini-Bloomberg

A CLI terminal that mimics Bloomberg for equity analysis, powered by OpenBB + FMP for data and Claude as the natural-language orchestrator.

**Primary goal**: Progressively implement Bloomberg equity functions from `Bloomberg Functions/02_Equity.md`, building toward a comprehensive equity analysis terminal. The CLI is the UI; the real asset is a clean set of tool-callable functions that Claude can compose.

**Approach**: Add functions one at a time, in priority order. Each function follows the same three-layer pattern. Quality over quantity — a well-implemented function beats a broken one.

---

## Non-Negotiable Architecture Rules

### 1. Three-layer separation — never violate

```
data/        → Thin wrappers around OpenBB/FMP. Return Pydantic models. NO printing, NO formatting.
functions/   → Bloomberg-style functions (DES, FA, GP, ANR, COMP, …). Return structured dicts. Define a tool_schema().
render/      → Turn structured output into CLI tables OR JSON for the LLM. THIS is the only layer that formats.
```

If you find yourself printing inside `data/` or `functions/`, stop. Move it to `render/`.

### 2. Every function is a tool

Every file in `functions/` must:
- Inherit from `BloombergFunction` (in `functions/base.py`)
- Implement `.run(**kwargs) -> dict`
- Implement `.tool_schema() -> dict` returning an Anthropic tool spec
- Return Pydantic-validated data (as `.model_dump()`)

This is so the same function powers both the CLI command AND the Claude agent tool call. ONE source of truth.

### 3. Pydantic everywhere

- Every data-layer return value: Pydantic model
- Every function output: dict of `.model_dump()` calls
- Never return raw DataFrames from `functions/`

Reason: LLMs reason reliably about typed, schema'd data. They struggle with raw DataFrames.

### 4. Cache aggressively

Use `diskcache` with 24h TTL on every data-layer call. OpenBB and FMP are slow and rate-limited. Caching turns 30s feedback loops into 0.1s.

### 5. Fail gracefully, never silently

- If FMP rate-limits, fall back to OpenBB. If OpenBB fails, raise a clean `DataSourceError`.
- Functions catch errors and return `{"status": "error", "message": "..."}` instead of crashing.
- The CLI and the LLM both handle error dicts, not exceptions.

---

## Function Roadmap

Target: all functions in `Bloomberg Functions/02_Equity.md`. Implement in priority order. Mark status as you go.

### ✅ Implemented

| Function | Bloomberg equivalent | What it does |
|---|---|---|
| `DES` | Security Description | Company profile: name, sector, exchange, market cap, identifiers |
| `FA` | Financial Analysis | Income statement, balance sheet, cash flow — last 4 years annual |
| `GP` | Graph Price | ASCII price chart, configurable lookback |
| `ANR` | Analyst Recommendations | Consensus rating, target price, # of analysts |
| `COMP` | Comparable Analysis | Side-by-side peer comparison on key ratios |
| `RPT` | (custom) | Full HTML equity report combining all of the above |
| `RV` | Relative Value | Valuation + margin comparison for ticker vs. peer group |

### 🔜 Next Priority (feasible with FMP/OpenBB free tier)

| Function | Bloomberg equivalent | Notes |
|---|---|---|
| `DVD` | Dividend | History, yield, payout ratio, ex-dates, growth |
| `ERN` | Earnings Analysis | EPS estimates, surprises, revision trends |
| `EE` | Earnings Estimates | Revenue/EPS/EBITDA estimates by broker |
| `SI` | Short Interest | Shares short, short ratio, days to cover |
| `OWN` | Ownership Summary | Institutional holders, insider transactions |
| `EVTS` | Events Calendar | Earnings dates, dividends, splits for a ticker |
| `MOST` | Most Active | Top gainers, losers, volume leaders by exchange |

### 🔭 Longer Term (more complex or limited data availability)

| Function | Bloomberg equivalent | Notes |
|---|---|---|
| `EQS` | Equity Screening | Screen stocks by fundamental/technical criteria |
| `GF` | Graph Financials | Chart any financial line item over time |
| `WEI` | World Equity Indices | Global index monitor with performance and valuation |
| `MA` | M&A Analysis | Deal search, premium analysis, comparable transactions |
| `IPO` | IPO Calendar | Upcoming/recent IPOs with filing details |
| `TECH` | Technical Analysis | Summary of technical signals and indicators |
| `EQRV` | Equity Relative Value | Scatter plots: valuation multiples vs. fundamentals |

### ⛔ Out of Scope (non-equity asset classes)

Functions from `03_Fixed_Income.md`, `04_FX.md`, `05_Commodities.md`, `06_Derivatives_Options.md`, etc. — equity only for now.

---

## Tech Stack (Locked)

```
python = ">=3.11"

# Data
openbb = ">=4.3"              # primary data source for non-US
requests = ">=2.31"           # FMP REST API
pydantic = ">=2.8"

# CLI
typer = ">=0.12"              # command-line framework
rich = ">=13.7"               # tables, colors, panels
plotext = ">=5.2"             # ASCII charts in terminal
prompt-toolkit = ">=3.0"      # REPL input with history

# LLM
anthropic = ">=0.40"

# Infra
diskcache = ">=5.6"           # disk-backed cache
python-dotenv = ">=1.0"       # .env file loading
pytest = ">=8.0"              # testing (dev only)
```

Use `uv` for dependency management. Ask before adding any new dependency.

---

## Global Market Handling

1. **Ticker format**: Accept Bloomberg-style input (`AAPL US Equity`, `0700 HK Equity`, `7203 JP Equity`). Parse into `Ticker(symbol, exchange_code, asset_class)` in `core/ticker.py`.
2. **Data source routing**:
   - US equities → FMP (best fundamentals)
   - Non-US equities → OpenBB/yfinance first, FMP as fallback (exchange-suffix format e.g. `3693.HK`)
   - Fall back to the other if primary fails
3. **Currency**: Never auto-convert. Display in native currency, clearly labeled.
4. **Known pain points** (document as TODOs, don't fix unless asked):
   - Chinese A-shares (would need tushare/akshare)
   - India BSE ticker mapping
   - Smaller European exchanges

---

## File Layout

```
mini-bloomberg/
├── pyproject.toml
├── README.md
├── CLAUDE.md                   # this file
├── Bloomberg Functions/        # reference specs for all Bloomberg functions
│
├── src/mini_bloomberg/
│   ├── config.py               # loads .env, exposes settings
│   ├── core/
│   │   ├── errors.py
│   │   ├── ticker.py           # "AAPL US Equity" → Ticker model
│   │   ├── cache.py
│   │   └── session.py
│   ├── data/
│   │   ├── schemas.py          # Pydantic models for all data types
│   │   ├── providers/
│   │   │   ├── fmp_provider.py
│   │   │   └── openbb_provider.py
│   │   ├── equity_profile.py
│   │   ├── equity_fundamentals.py
│   │   ├── equity_price.py
│   │   ├── equity_estimates.py
│   │   └── equity_peers.py
│   ├── functions/
│   │   ├── base.py             # BloombergFunction ABC
│   │   ├── des.py
│   │   ├── fa.py
│   │   ├── gp.py
│   │   ├── anr.py
│   │   ├── comp.py
│   │   └── rpt.py              # Full HTML report
│   ├── render/
│   │   ├── cli_renderer.py     # Rich tables, panels, plotext charts
│   │   ├── html_renderer.py    # IB-style HTML report (RPT output)
│   │   └── json_renderer.py    # clean JSON for LLM consumption
│   ├── cli/
│   │   ├── app.py
│   │   ├── repl.py
│   │   └── dispatcher.py
│   └── agents/
│       ├── tools.py
│       ├── orchestrator.py
│       └── prompts.py
│
├── reports/                    # generated HTML reports
└── scripts/
    └── demo_cli.sh
```

---

## Bloomberg-Style UX Rules

- **Command syntax**: `<TICKER> <GO>` loads a security, then function commands run against it
  - `AAPL US Equity <GO>` → loads AAPL into session
  - `DES <GO>` → shows description of loaded security
- **Uppercase commands**: Always `DES`, never `des`. Dispatcher uppercases input before lookup.
- **Yellow prompt, green/black aesthetic**: Rich's `Style(color="bright_green", bgcolor="black")` + yellow prompts
- **Status bar at bottom**: Show loaded ticker, time, connection status
- **HELP command**: `HELP <GO>` lists all available functions

---

## LLM Integration Rules

### Tool schema generation pattern

```python
class DES(BloombergFunction):
    name = "DES"
    description = "Get company description and key identifiers for a ticker"

    def tool_schema(self) -> dict:
        return {
            "name": "des",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Bloomberg-style ticker, e.g. 'AAPL US Equity'"
                    }
                },
                "required": ["ticker"]
            }
        }

    def run(self, ticker: str) -> dict:
        # ... returns {"status": "ok", "data": profile.model_dump()}
```

### CLI dispatch rule

- `DES <GO>` → direct function call
- `? why has AAPL outperformed MSFT <GO>` → agent mode

---

## What NOT to Do

- ❌ Don't implement non-equity asset class functions (Fixed Income, FX, Commodities, etc.)
- ❌ Don't build a web UI. CLI only.
- ❌ Don't build a charting library. Use `plotext` for terminal charts.
- ❌ Don't use LangChain or LlamaIndex. Raw Anthropic SDK only.
- ❌ Don't over-engineer the cache. `diskcache` with TTL is enough.
- ❌ Don't build multi-agent. Single agent only.
- ❌ Don't skip Pydantic.
- ❌ Don't print inside `data/` or `functions/`. Rendering is a separate layer.
- ❌ Don't catch exceptions silently. Either handle them or let them bubble to a top-level handler.
- ❌ Don't add a new dependency without asking first.

---

## Communication Rules

- Before adding a dependency not in this file: ask the user
- Before changing the architecture: ask the user
- When starting a new function: confirm which Bloomberg function from `02_Equity.md` it maps to
- When a data field is unavailable from FMP/OpenBB free tier: document as TODO, show N/A gracefully, move on
- If something in the rules is ambiguous, ASK rather than guess
