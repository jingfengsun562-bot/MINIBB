# CLAUDE.md

Rules and context for Claude Code to follow while building this project. Read this before touching any code. Re-read it before each milestone.

---

## Project: Mini-Bloomberg

A CLI terminal that mimics Bloomberg for equity analysis, powered by OpenBB + FMP for data and Claude as the natural-language orchestrator.

**Primary goal**: Foundation for an LLM-powered financial analysis agent. The CLI is the UI; the real asset is a clean set of tool-callable functions that Claude can compose.

**Timeline**: 2 weeks. Ship a working prototype, not a perfect one.

---

## Non-Negotiable Architecture Rules

### 1. Three-layer separation — never violate

```
data/        → Thin wrappers around OpenBB/FMP. Return Pydantic models. NO printing, NO formatting.
functions/   → Bloomberg-style functions (DES, FA, GP, ANR, COMP). Return structured dicts. Define a tool_schema().
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

### 4. Cache aggressively during development

Use `diskcache` with 24h TTL on every data-layer call. OpenBB and FMP are slow and rate-limited. Caching turns 30s feedback loops into 0.1s.

### 5. Fail gracefully, never silently

- If FMP rate-limits, fall back to OpenBB. If OpenBB fails, raise a clean `DataSourceError`.
- Functions catch errors and return `{"status": "error", "message": "..."}` instead of crashing.
- The CLI and the LLM both handle error dicts, not exceptions.

---

## Scope Lock

**5 functions only. Do not add more.**

| Function | Bloomberg equivalent | What it does |
|---|---|---|
| `DES` | Description | Company profile: name, sector, exchange, market cap, identifiers |
| `FA` | Financial Analysis | Income statement, balance sheet, cash flow — last 4 years annual |
| `GP` | Graph Price | ASCII price chart, configurable lookback |
| `ANR` | Analyst Recommendations | Consensus rating, target price, # of analysts |
| `COMP` | Comparables | Side-by-side table of peers on key ratios |

If the user asks to add another function, push back: "Is this critical for the demo, or can it go in v2?"

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

Use `uv` for dependency management.

---

## Global Market Handling

User wants global coverage. Strategy to avoid data-normalization hell:

1. **Ticker format**: Accept Bloomberg-style input (`AAPL US Equity`, `0700 HK Equity`, `7203 JP Equity`). Parse into `Ticker(symbol, exchange_code, asset_class)` in `core/ticker.py`.
2. **Data source routing**:
   - US equities → FMP (best fundamentals)
   - Non-US equities → OpenBB (broader coverage via yfinance/other providers)
   - Fall back to the other if primary fails
3. **Currency**: Never auto-convert. Display in native currency, clearly labeled.
4. **Known pain points** (document as TODOs, don't fix in v1):
   - Chinese A-shares (would need tushare/akshare)
   - India BSE ticker mapping
   - Smaller European exchanges

---

## File Layout (Build in This Order)

```
mini-bloomberg/
├── pyproject.toml
├── README.md
├── CLAUDE.md                   # this file
├── WORKFLOW.md                 # data flow documentation
├── .env.example
│
├── src/mini_bloomberg/
│   ├── __init__.py
│   ├── config.py               # loads .env, exposes settings
│   │
│   ├── core/                   # BUILD IN MILESTONE 2
│   │   ├── errors.py           # DataSourceError, TickerError, etc.
│   │   ├── ticker.py           # "AAPL US Equity" → Ticker model
│   │   ├── cache.py            # diskcache decorator
│   │   └── session.py          # loaded-security state
│   │
│   ├── data/                   # BUILD IN MILESTONE 2-4
│   │   ├── schemas.py          # CompanyProfile, IncomeStatement, etc.
│   │   ├── providers/
│   │   │   ├── fmp_provider.py
│   │   │   └── openbb_provider.py
│   │   ├── equity_profile.py
│   │   ├── equity_fundamentals.py
│   │   ├── equity_price.py
│   │   └── equity_estimates.py
│   │
│   ├── functions/              # BUILD IN MILESTONE 3-4
│   │   ├── base.py             # BloombergFunction ABC
│   │   ├── des.py
│   │   ├── fa.py
│   │   ├── gp.py
│   │   ├── anr.py
│   │   └── comp.py
│   │
│   ├── render/                 # BUILD ALONGSIDE functions/
│   │   ├── cli_renderer.py     # Rich tables, panels, plotext charts
│   │   └── json_renderer.py    # clean JSON for LLM consumption
│   │
│   ├── cli/                    # BUILD IN MILESTONE 5
│   │   ├── app.py              # Typer entry point
│   │   ├── repl.py             # prompt-toolkit interactive loop
│   │   └── dispatcher.py       # parse commands, route to function or agent
│   │
│   └── agents/                 # BUILD IN MILESTONE 6
│       ├── tools.py            # auto-generate Anthropic tool specs
│       ├── orchestrator.py     # single-agent tool-use loop
│       └── prompts.py          # junior analyst system prompt
│
├── tests/
│   ├── fixtures/               # cached API responses for offline testing
│   └── test_*.py
│
└── scripts/
    ├── demo_cli.sh
    └── demo_agent.py
```

---

## Bloomberg-Style UX Rules

To make this feel like the real thing:

- **Command syntax**: `<TICKER> <GO>` loads a security, then function commands run against it
  - `AAPL US Equity <GO>` → loads AAPL into session
  - `DES <GO>` → shows description of loaded security
- **Uppercase commands**: Always `DES`, never `des`. Dispatcher uppercases input before lookup.
- **Yellow prompt, green/black aesthetic**: Rich's `Style(color="bright_green", bgcolor="black")` + yellow prompts
- **Status bar at bottom**: Show loaded ticker, time, connection status
- **HELP command**: `HELP <GO>` lists all available functions

---

## LLM Integration Rules (Milestone 6)

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

### Orchestrator loop (essence)

```python
def run_agent(query: str) -> str:
    messages = [{"role": "user", "content": query}]
    tools = [fn.tool_schema() for fn in ALL_FUNCTIONS]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            system=ANALYST_PROMPT,
            tools=tools,
            messages=messages,
            max_tokens=4096,
        )

        if response.stop_reason == "end_turn":
            return extract_text(response)

        # stop_reason == "tool_use"
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})

        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(FUNCTIONS_BY_NAME[tu.name].run(**tu.input)),
            }
            for tu in tool_uses
        ]
        messages.append({"role": "user", "content": tool_results})
```

### CLI dispatch rule

- `DES <GO>` → direct function call
- `? why has AAPL outperformed MSFT <GO>` → agent mode

---

## What NOT to Do

- ❌ Don't add functions beyond the 5 locked ones
- ❌ Don't build a web UI. CLI only.
- ❌ Don't support options/futures/FX. Equity only.
- ❌ Don't build a charting library. Use `plotext`.
- ❌ Don't use LangChain or LlamaIndex. Raw Anthropic SDK only.
- ❌ Don't over-engineer the cache. `diskcache` with TTL is enough.
- ❌ Don't build multi-agent. Single agent only.
- ❌ Don't skip Pydantic.
- ❌ Don't print inside `data/` or `functions/`. Rendering is a separate layer.
- ❌ Don't catch exceptions silently. Either handle them or let them bubble to a top-level handler.

---

## Definition of Done

By end of the build, this repo should:

1. `uv sync && uv run mini-bb` launches the REPL
2. `AAPL US Equity <GO>` loads the security, all 5 functions work
3. At least 3 non-US tickers work (e.g., `0700 HK Equity`, `7203 JP Equity`, `MC FP Equity`)
4. `? compare NVDA and AMD profitability <GO>` → agent executes multi-tool workflow, returns analyst-style answer
5. README with screenshots, architecture diagram, demo commands
6. Graceful error handling — no crashes on bad tickers, API failures, rate limits

---

## Communication Rules

- Before adding a dependency not in this file: ask the user
- Before changing the architecture: ask the user
- Before adding a function beyond the 5: push back
- When stuck on a data normalization issue: document as TODO, skip, move on
- Commit after each milestone with a clear message
- If something in the rules is ambiguous, ASK rather than guess
