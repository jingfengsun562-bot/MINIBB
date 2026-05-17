# The Three Core Financial Statements — General Structure

The income statement, balance sheet, and cash flow statement are the three core financial statements that every public company is required to publish. They all follow the same underlying logic — **inflows minus outflows equals a residual** — but they measure different things over different time frames.

| Statement | What it measures | Time frame |
|---|---|---|
| Income statement | Performance (profitability) | Over a period (quarter / year) |
| Balance sheet | Position (resources & claims) | Snapshot at a point in time |
| Cash flow statement | Cash movement | Over a period (quarter / year) |

---

## 1. Income Statement

A waterfall structure. Each line strips out one more category of cost to expose a different driver of profitability.

| Group | Line items | Subtotal produced |
|---|---|---|
| Revenue | Sales, service revenue, other operating income | — |
| Cost of goods sold (COGS) | Direct materials, direct labor, manufacturing overhead | **Gross profit** |
| Operating expenses | SG&A, R&D, depreciation & amortization | **Operating income (EBIT)** |
| Non-operating items | Interest income / expense, FX gains/losses, one-off gains/losses | **Pre-tax income** |
| Income tax expense | Current tax + deferred tax | — |
| **Bottom line** | | **Net income** (→ EPS) |



---

## 2. Balance Sheet

An identity, not a flow: **Assets = Liabilities + Shareholders' Equity** must hold at every reporting date. Items are split by liquidity (current = within one year, non-current = beyond one year).

### Assets — what the company owns

| Group | Line items |
|---|---|
| Current assets | Cash & equivalents, accounts receivable, inventory, prepaid expenses, short-term investments |
| Non-current assets | Property, plant & equipment (PP&E); intangibles; goodwill; long-term investments; deferred tax assets |

### Liabilities — what the company owes

| Group | Line items |
|---|---|
| Current liabilities | Accounts payable, short-term debt, accrued expenses, current portion of long-term debt |
| Non-current liabilities | Long-term debt, lease liabilities, deferred tax liabilities, pension obligations |

### Shareholders' equity — residual claim of owners

| Group | Line items |
|---|---|
| Contributed capital | Common stock / share capital, additional paid-in capital (APIC) |
| Earned capital | Retained earnings |
| Other | Accumulated other comprehensive income (AOCI), treasury stock |

---

## 3. Cash Flow Statement

A translator: it takes net income (accrual-based) and converts it to actual cash movement. Three sections answer three questions about cash.

| Section | Question answered | Key line items |
|---|---|---|
| **Operating (CFO)** | How much cash did the core business generate? | Net income (starting point), + D&A, + stock-based comp, ± changes in working capital (AR, inventory, AP) |
| **Investing (CFI)** | How much cash was spent on long-term assets? | CapEx, acquisitions, asset sales, purchases/sales of investments |
| **Financing (CFF)** | How was the business funded? | Debt issued / repaid, equity issued / share buybacks, dividends paid |
| **Bottom line** | | **Net change in cash** (reconciles to balance sheet cash) |

---

## The Common Structural Pattern

Every statement, despite looking different, follows the same three-part pattern:

| Step | Income statement | Balance sheet | Cash flow statement |
|---|---|---|---|
| 1. Inflows / resources | Revenue | Assets | Cash inflows |
| 2. Outflows / claims | Expenses | Liabilities | Cash outflows |
| 3. Residual / result | Net income | Shareholders' equity | Net change in cash |

---

## How the Three Statements Articulate

The statements are not three independent reports — they form a tightly linked system. Three articulation points must hold:

1. **Net income (IS) → Retained earnings (BS)**
   Net income from the income statement flows into retained earnings on the balance sheet (less any dividends paid).

2. **Net income (IS) → Starting line of CFO (CF)**
   Under the indirect method, net income is the starting point of the cash flow statement; it then gets adjusted for non-cash items and working-capital changes.

3. **Net change in cash (CF) → Cash balance (BS)**
   The "net change in cash" at the bottom of the cash flow statement must equal the difference between this period's and last period's cash balance on the balance sheet.

If any of these don't tie, the financials are wrong — which is exactly the kind of check that can be automated when ingesting filings programmatically.

---

## Time-Frame Relationship

Two consecutive balance sheets bracket each income statement and cash flow statement:

```
BS (Dec 31, Year 1) ──── IS for Year 2 ────► BS (Dec 31, Year 2)
                    ──── CF for Year 2 ────►
```

The income statement and cash flow statement explain **how** the company moved from one balance sheet snapshot to the next.
