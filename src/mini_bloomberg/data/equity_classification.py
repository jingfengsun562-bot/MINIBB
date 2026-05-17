"""
One-shot Claude Haiku call to classify financial statement row names
into the canonical sections defined in three_financial_statements_structure.md.
Cached 24h per ticker per calendar day.
"""

import json
from datetime import date
from pathlib import Path
from typing import Optional

from mini_bloomberg.core.cache import _cache as _disk_cache
from mini_bloomberg.core.llm import _get_client
from mini_bloomberg.core.ticker import Ticker

_RULES_PATH = (
    Path(__file__).parents[3]
    / "Schema for stocks analysis"
    / "financial_classification_rules.json"
)
_MD_PATH = (
    Path(__file__).parents[3]
    / "Schema for stocks analysis"
    / "three_financial_statements_structure.md"
)

# Standard rows from annual field maps that are sent to AI for classification.
# Rows that are pre-placed in the Excel template as Σ subtotals or computed
# metrics are excluded here — AI should not re-classify them.
_BASE_IS_ROWS: list[str] = [
    "Total Revenue",
    "Cost of Revenue",
    "R&D Expenses",
    "SG&A Expenses",
    "Total Operating Expenses",
    "EBIT",
    "EPS (Basic)",
    "EPS (Diluted)",
    "Shares Outstanding (Basic)",
    "Shares Outstanding (Diluted)",
    "D&A",
    "Income Tax Expense",
    "Pretax Income",
]

_BASE_BS_ROWS: list[str] = [
    "Cash & Equivalents",
    "ST Investments",
    "Cash & ST Investments",
    "Accounts Receivable",
    "Inventory",
    "Net PPE",
    "Goodwill & Intangibles",
    "Accounts Payable",
    "ST Debt",
    "Long-Term Debt",
    "Retained Earnings",
    "Total Debt",
    "Net Debt",
]

_BASE_CF_ROWS: list[str] = [
    "Net Income",
    "D&A",
    "Stock-Based Compensation",
    "Change in Working Capital",
    "Capital Expenditures",
    "Free Cash Flow",
    "Dividends Paid",
    "Share Buybacks",
    "Ending Cash",
]


def classify_financial_rows(
    ticker: Ticker,
    extra_is: list[str],
    extra_bs: list[str],
    extra_cf: list[str],
) -> Optional[dict]:
    """
    Classify all IS/BS/CF row names into their canonical sections.
    `extra_*` are company-specific rows (stripped of `~` prefix) from quarterly data.
    Returns {"IS": {row: section}, "BS": {...}, "CF": {...}} or None on failure.
    Cached 24h per ticker per calendar day.
    """
    cache_key = f"row_classify:{ticker.symbol}:{ticker.exchange_code}:{date.today()}"
    cached = _disk_cache.get(cache_key)
    if cached is not None:
        return cached

    is_rows = _dedup(_BASE_IS_ROWS + extra_is)
    bs_rows = _dedup(_BASE_BS_ROWS + extra_bs)
    cf_rows = _dedup(_BASE_CF_ROWS + extra_cf)

    try:
        rules = json.loads(_RULES_PATH.read_text(encoding="utf-8"))
        md_content = _MD_PATH.read_text(encoding="utf-8")
    except Exception:
        return None

    prompt = _build_prompt(rules, md_content, is_rows, bs_rows, cf_rows)

    try:
        client = _get_client()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = next(b for b in msg.content if b.type == "text").text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
    except Exception:
        return None

    _disk_cache.set(cache_key, result, expire=86400)
    return result


def _dedup(rows: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for r in rows:
        seen[r] = None
    return list(seen)


def _build_prompt(rules: dict, md: str, is_rows, bs_rows, cf_rows) -> str:
    def fmt_rules(stmt_rules: dict) -> str:
        lines = []
        for section, info in stmt_rules.items():
            lines.append(f'  "{section}": {info["description"]}')
            lines.append(f'    Examples: {", ".join(info["examples"][:4])}')
        return "\n".join(lines)

    return (
        "You are classifying financial statement row names into their correct sections.\n\n"
        "--- REFERENCE: Financial Statement Structure ---\n"
        f"{md}\n\n"
        "--- CLASSIFICATION RULES ---\n\n"
        f"INCOME STATEMENT sections (assign IS rows to exactly one of these):\n{fmt_rules(rules['IS'])}\n\n"
        f"BALANCE SHEET sections (assign BS rows to exactly one of these):\n{fmt_rules(rules['BS'])}\n\n"
        f"CASH FLOW sections (assign CF rows to exactly one of these):\n{fmt_rules(rules['CF'])}\n\n"
        "--- INSTRUCTIONS ---\n"
        "- Assign every row to exactly one section using the exact section name strings above.\n"
        "- No row may be left unassigned — pick the closest section if uncertain.\n"
        "- Return valid JSON only — no explanation, no markdown fences.\n\n"
        "--- ROWS TO CLASSIFY ---\n"
        f"IS rows: {json.dumps(is_rows)}\n"
        f"BS rows: {json.dumps(bs_rows)}\n"
        f"CF rows: {json.dumps(cf_rows)}\n\n"
        'Return: {"IS": {"row_name": "section_name", ...}, "BS": {...}, "CF": {...}}'
    )
