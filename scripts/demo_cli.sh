#!/usr/bin/env bash
# Mini-Bloomberg CLI Demo
# Runs a scripted session showing all 5 functions + AI agent across 3 markets.
# Usage: bash scripts/demo_cli.sh

set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="uv run python"

run() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $*"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

dispatch() {
    $PYTHON -c "
from mini_bloomberg.cli.dispatcher import dispatch
dispatch('$1')
dispatch('$2')
" 2>/dev/null
}

run "1 / 8  DES — Apple Inc (US)"
uv run mini-bb des "AAPL US Equity"

run "2 / 8  FA  — Apple 4-year financials"
uv run mini-bb fa "AAPL US Equity"

run "3 / 8  GP  — Apple 1-year price chart"
uv run mini-bb gp "AAPL US Equity" --days 365

run "4 / 8  ANR — Apple analyst ratings"
uv run mini-bb anr "AAPL US Equity"

run "5 / 8  COMP — Apple peer comparison"
uv run mini-bb comp "AAPL US Equity"

run "6 / 8  Non-US: Tencent (HK), Toyota (JP), LVMH (FR)"
dispatch "0700 HK Equity" "DES"
dispatch "7203 JP Equity" "DES"
dispatch "MC FP Equity"   "DES"

run "7 / 8  AI Analyst — compare NVDA and AMD profitability"
$PYTHON -c "
from mini_bloomberg.agents.orchestrator import run_agent
run_agent('compare NVDA and AMD profitability')
" 2>/dev/null

run "8 / 8  AI Analyst — why has AAPL underperformed NVDA over 1 year?"
$PYTHON -c "
from mini_bloomberg.agents.orchestrator import run_agent
run_agent('Why has AAPL underperformed NVDA over the past year? Use price history and financial data.')
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Demo complete."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
