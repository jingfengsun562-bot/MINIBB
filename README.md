# Mini-Bloomberg

A CLI terminal that mimics Bloomberg for equity analysis, powered by **OpenBB + FMP** for data and **Claude** as a natural-language orchestrator.

```
╭─────────────────────────────────────────────────────────────────────────────╮
│  MINI-BLOOMBERG  Equity Analysis Terminal                                   │
│                                                                             │
│  Type a ticker to load it, then run DES / FA / GP / ANR / COMP.            │
│  Prefix with ? to ask the AI analyst. HELP <GO> for all commands.          │
╰─────────────────────────────────────────────────────────────────────────────╯

MINI-BB> AAPL US Equity <GO>
Security loaded: AAPL US Equity

MINI-BB> DES <GO>
╭─────────────────────── DES  Apple Inc.  AAPL ─────────────────────────────╮
│  Name        Apple Inc.    Market Cap    $3.87T                            │
│  Sector      Technology    Beta          1.109                             │
│  Exchange    NMS           Dividend Yld  0.39%                             │
╰────────────────────────────────────────────────────────────────────────────╯

MINI-BB> ? compare NVDA and AMD profitability <GO>
╭──────────────────────────────── AI Analyst ────────────────────────────────╮
│  NVDA wins on every metric — by a wide margin. Gross margin 71% vs 49%.   │
│  NVDA generated more FCF ($96.7B) than AMD's entire revenue ($34.6B)...   │
╰────────────────────────────────────────────────────────────────────────────╯
```

---

## Features

| Function | Bloomberg equivalent | What it does |
|---|---|---|
| `DES` | Description | Company profile: name, sector, market cap, identifiers |
| `FA` | Financial Analysis | 4-year income statement, balance sheet, cash flow |
| `GP` | Graph Price | ASCII price chart via plotext |
| `ANR` | Analyst Recommendations | Consensus target price + buy/hold/sell breakdown |
| `COMP` | Comparables | Peer table: margins, EBITDA, debt, beta |
| `? <query>` | NLP | Claude agent with tool-use — runs functions and synthesises |

**Global coverage**: US, HK, JP, FR, DE, UK and more via `SYMBOL EXCHANGE Equity` format.

---

## Architecture

```
User input
    │
    ▼
cli/repl.py          ← prompt-toolkit REPL (history, tab-complete, status bar)
    │
    ▼
cli/dispatcher.py    ← routes: TICKER <GO> | FUNCTION <GO> | ? query <GO>
    │
    ├── functions/   ← DES / FA / GP / ANR / COMP  (BloombergFunction ABC)
    │       │              each implements .run() and .tool_schema()
    │       ▼
    │   data/        ← provider routers → FMP (US) or OpenBB/yfinance (non-US)
    │       │              returns Pydantic models, cached 24h via diskcache
    │       ▼
    │   render/      ← cli_renderer.py (Rich panels/tables/plotext charts)
    │
    └── agents/      ← orchestrator.py: Claude tool-use loop (streaming)
            │              prompts.py: junior analyst system prompt
            └── tools.py: auto-generates Anthropic tool specs from functions
```

**Key design**: the CLI path and the LLM agent path both call the **same** `fn.run()` — zero code duplication.

---

## Setup

### 1. Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) — `pip install uv`

### 2. Install

```bash
git clone <repo>
cd mini-bloomberg
uv sync
```

### 3. API Keys

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

| Key | Where to get it | Required for |
|---|---|---|
| `FMP_API_KEY` | [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs) (free) | FA, GP, ANR, COMP |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | `? <query>` AI agent |
| `OPENBB_PAT` | [my.openbb.co](https://my.openbb.co/app/platform/pat) (optional) | Enhanced non-US data |

> **FMP free tier**: 250 calls/day. All data is cached 24h so normal use stays well within limits.

### 4. Run

```bash
uv run mini-bb          # launch interactive REPL
uv run mini-bb des "AAPL US Equity"   # one-shot command
```

---

## Usage

### REPL commands

```
AAPL US Equity <GO>     Load a security
DES <GO>                Company description
FA <GO>                 Financial analysis (4 years)
GP <GO>                 Price chart (default 1 year)
GP --days 90 <GO>       Price chart (custom period)
ANR <GO>                Analyst ratings
COMP <GO>               Peer comparison table
? <your question> <GO>  Ask the AI analyst
HELP <GO>               List all commands
QUIT <GO>               Exit
```

### Supported ticker formats

```
AAPL US Equity      Apple Inc (NYSE/NASDAQ)
0700 HK Equity      Tencent Holdings (HKEX)
7203 JP Equity      Toyota Motor (Tokyo)
MC FP Equity        LVMH (Euronext Paris)
SAP GR Equity       SAP SE (XETRA)
HSBA LN Equity      HSBC Holdings (London)
```

### Direct subcommands (no REPL)

```bash
uv run mini-bb des "AAPL US Equity"
uv run mini-bb fa  "AAPL US Equity" --years 4
uv run mini-bb gp  "AAPL US Equity" --days 180
uv run mini-bb anr "AAPL US Equity"
uv run mini-bb comp "AAPL US Equity"
```

---

## Data sources

| Data | US equities | Non-US equities |
|---|---|---|
| Company profile | OpenBB/yfinance | OpenBB/yfinance |
| Financials | FMP `/stable/income-statement` etc. | OpenBB/yfinance |
| Price history | FMP `/stable/historical-price-eod/full` | OpenBB/yfinance |
| Price targets | FMP `/stable/price-target-consensus` | — |
| Analyst ratings | OpenBB/yfinance consensus | OpenBB/yfinance |
| Peers | FMP `/stable/stock-peers` | — |

---

## AI Agent

The `?` prefix routes to Claude (`claude-sonnet-4-6` by default, switchable to `claude-opus-4-7` via `CLAUDE_MODEL` in `.env`).

The agent uses **prompt caching** on the system prompt and **streaming output** so you see the answer token-by-token. It runs tool calls in **parallel** (e.g. `FA` for two tickers simultaneously).

```
MINI-BB> ? which of MSFT, GOOGL, META has the best FCF yield? <GO>
```

---

## Tech stack

```
Data        openbb, httpx, pydantic, diskcache
CLI         typer, rich, plotext, prompt-toolkit
LLM         anthropic (claude-sonnet-4-6)
Infra       uv, python-dotenv, pytest
```

---

## Known limitations (v1)

- **Chinese A-shares**: requires tushare/akshare — not supported
- **India BSE**: ticker mapping unreliable via yfinance
- **COMP for non-US**: FMP peer list is US-centric; non-US peers may be incomplete
- **ANR for non-US**: price targets only available for US tickers via FMP
- **Sony revenue in COMP**: displays in JPY (native), not USD-converted

---

## Demo

```bash
bash scripts/demo_cli.sh
```

Runs 8 scripted demos: all 5 functions on AAPL, 3 non-US DES calls, and 2 AI analyst queries.
