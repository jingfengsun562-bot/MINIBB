# Claude Code Master Prompt

**Copy-paste this into Claude Code as your opening message.** It sets up the project, loads the rules, and tells Claude Code what to build and in what order.

---

## How to Use

1. Open Claude Code in an empty directory
2. Copy `CLAUDE.md` and `WORKFLOW.md` into that directory
3. Paste the prompt below as your first message to Claude Code
4. Let it ask follow-up questions; answer them
5. Review each milestone before moving on

---

## The Prompt

```
I'm building a project called Mini-Bloomberg — a CLI terminal that mimics
Bloomberg for equity analysis, powered by OpenBB + Financial Modeling Prep
(FMP) for data and Claude (you, via the Anthropic API) as a natural-language
orchestrator.

Before writing any code, read these two files carefully and treat them as
authoritative:

1. CLAUDE.md — architecture rules, scope lock, tech stack, what NOT to do
2. WORKFLOW.md — end-to-end data flow from API to terminal

After reading them, confirm you understand:
- The three-layer separation (data / functions / render)
- The scope lock (only 5 functions: DES, FA, GP, ANR, COMP)
- The dual-path design (CLI direct call + LLM agent call use the SAME function code)
- The tech stack (typer, prompt-toolkit, rich, plotext, pydantic, anthropic,
  openbb, FMP REST, diskcache)

Then build the project in this order, pausing at each milestone for me to
review before continuing:

MILESTONE 1 — Skeleton & data sanity check
  - Initialize uv project with the pyproject.toml from CLAUDE.md
  - Create the full directory structure from CLAUDE.md (empty files are fine)
  - Write a throwaway script that pulls AAPL profile from FMP AND from OpenBB,
    prints both, so we can see the data shape
  - STOP and show me the output

MILESTONE 2 — Core + data layer for company profile
  - Implement core/ (ticker parser, session, cache decorator, errors)
  - Implement data/schemas.py with CompanyProfile Pydantic model
  - Implement data/providers/fmp_provider.py and openbb_provider.py for profile only
  - Implement data/equity_profile.py (router: US→FMP, else→OpenBB, with fallback)
  - Write a short test that: parses "AAPL US Equity", fetches profile, prints it
  - STOP and show me the test output

MILESTONE 3 — First function end-to-end: DES
  - Implement functions/base.py (BloombergFunction ABC)
  - Implement functions/des.py using the data layer
  - Implement render/cli_renderer.py with a render_des() function using Rich
  - Wire up a minimal cli/app.py that takes a ticker as argument and runs DES
  - Demo: `uv run mini-bb des "AAPL US Equity"` shows a Rich panel
  - STOP and show me a screenshot

MILESTONE 4 — Remaining 4 functions
  - Implement the rest of data/ for fundamentals, price, estimates
  - Implement functions/fa.py, gp.py (plotext), anr.py, comp.py
  - Add renderers for each
  - Extend cli/app.py to support all five as commands
  - STOP and show me all five running against AAPL

MILESTONE 5 — REPL with session state
  - Implement core/session.py (loaded ticker state)
  - Implement cli/repl.py with prompt-toolkit (history, autocomplete for
    function names, Bloomberg-style prompt)
  - Implement cli/dispatcher.py (parse "DES <GO>" vs "AAPL US Equity <GO>")
  - Add HELP and QUIT commands
  - STOP and show me a screen recording of a session

MILESTONE 6 — LLM agent
  - Implement agents/tools.py: auto-generate Anthropic tool specs from every
    BloombergFunction's .tool_schema()
  - Implement agents/prompts.py with a junior equity analyst system prompt
  - Implement agents/orchestrator.py: tool-use loop with claude-opus-4-5
  - Extend dispatcher: "?" prefix routes to agent instead of function registry
  - STOP and show me: `? compare NVDA and AMD profitability <GO>`

MILESTONE 7 — Polish
  - Error handling: bad tickers, rate limits, API failures — never crash
  - README with screenshots
  - Demo script: scripts/demo_cli.sh
  - Final smoke test with 5 tickers across 3 markets (US, HK, JP)

Rules while building:
- Read CLAUDE.md's "What NOT to Do" section before every milestone
- If you're tempted to add a 6th function, ask me first
- If you hit a non-US data normalization issue, document as TODO and move on
- Commit after each milestone with a clear message
- If something in the rules is ambiguous, ASK rather than guess

Ready? Start with Milestone 1 and ask me any clarifying questions you have
before writing code.

Also, make some technical suggestion to make my project better. ask me for my opinions for the suggestions
```

---

## Why This Prompt Works

A few things are doing heavy lifting here:

**Front-loaded context**: CLAUDE.md + WORKFLOW.md are read first, so Claude Code never invents architecture that contradicts them.

**Explicit milestones with STOP points**: prevents Claude Code from running ahead and building Milestone 5 with bugs that compound from a broken Milestone 2.

**"ASK rather than guess"**: Claude Code tends to make reasonable-looking assumptions that turn out to be wrong. Explicit permission to ask saves debugging time later.

**Scope defense baked in**: the "if tempted to add a 6th function, ask me first" line is critical. Without it, Claude Code will helpfully add ESG data, news, technical indicators, etc., and you'll end up with a half-finished mess.

**Commits at milestones**: makes it trivial to roll back when something goes sideways.

---

## Follow-Up Prompts

Once Claude Code is working through milestones, these short prompts keep things on track:

**If it's adding scope:**
> Stop. Is this in CLAUDE.md's scope lock? If not, remove it and continue with the locked 5 functions.

**If it's mixing layers:**
> You're printing inside the function layer. Move all formatting to render/cli_renderer.py. Functions return dicts only.

**If it's using raw DataFrames:**
> Convert this to a Pydantic model before returning from the data layer. Check schemas.py for the pattern.

**If it gets stuck on non-US data:**
> Document this edge case as a TODO in the file header and move on. We're not fixing it in v1.

**If it's over-engineering:**
> Simpler. Ship > perfect. What's the minimum that works?

**When you want to test:**
> Run the demo: load AAPL, then run all 5 functions in sequence. Show me the terminal output.
