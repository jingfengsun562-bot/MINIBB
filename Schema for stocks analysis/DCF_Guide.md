# DCF Valuation Guide
### Data Sources: yfinance · US Treasury · Damodaran Online

---

## The Core DCF Formula

$$
\text{Intrinsic Value} = \sum_{t=1}^{n} \frac{FCFF_t}{(1 + WACC)^t} + \frac{\text{Terminal Value}}{(1 + WACC)^n}
$$

---

## Step 1 — Free Cash Flow to Firm (FCFF)

$$
FCFF = EBIT \times (1 - \text{Tax Rate}) + D\&A - \Delta NWC - CapEx
$$

| Element | Definition | Source | Where to Find |
|---|---|---|---|
| `EBIT` | Earnings Before Interest & Tax | **yfinance** | `income_stmt.loc['EBIT']` or `Operating Income` |
| `Tax Rate` | Effective tax rate (historical) | **yfinance** | `income_stmt.loc['Tax Rate For Calcs']` |
| `Tax Rate` | Marginal rate (terminal year) | **Damodaran** | [Country tax rates table](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/countrytax.html) |
| `D&A` | Depreciation & Amortization | **yfinance** | `cash_flow.loc['Depreciation And Amortization']` |
| `ΔNWC` | Change in Net Working Capital | **yfinance** | `balance_sheet`: `(Current Assets - Cash) - (Current Liabilities - ST Debt)`, delta YoY |
| `CapEx` | Capital Expenditure | **yfinance** | `cash_flow.loc['Capital Expenditure']` (negative → flip sign) |

> **Note:** Run 3–5 years of historical FCFF to identify trends before projecting forward.

---

## Step 2 — Project FCFF Forward (Years 1–5)

$$
FCFF_t = FCFF_{t-1} \times (1 + g_{\text{revenue}}) \quad \text{with margin assumptions held or adjusted}
$$

| Element | Definition | Source | Where to Find |
|---|---|---|---|
| `Revenue growth` | Historical CAGR as base | **yfinance** | `income_stmt.loc['Total Revenue']`, compute YoY |
| `EBIT margin` | Operating margin trend | **yfinance** | `EBIT / Total Revenue` across years |
| `Industry CapEx/Sales` | Normalise CapEx assumption | **Damodaran** | [capex.html](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/capex.html) — match sector |
| `Industry NWC/Sales` | Normalise working capital | **Damodaran** | [wcdata.html](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wcdata.html) — match sector |

---

## Step 3 — Terminal Value

$$
\text{Terminal Value} = \frac{FCFF_{n+1}}{WACC - g_{\text{perpetuity}}}
$$

| Element | Definition | Source | Where to Find |
|---|---|---|---|
| `FCFF_{n+1}` | Final projected year FCFF × (1 + g) | Derived from Step 2 | — |
| `g (perpetuity)` | Long-run stable growth rate | **US Treasury + Damodaran** | Use 10-yr Treasury yield as ceiling; Damodaran's implied ERP page for country growth context |
| `WACC` | Discount rate (see Step 4) | Computed below | — |

> **Rule of thumb:** `g` should never exceed the long-term GDP growth rate of the country (~2–3% for US). Use the **10-yr Treasury yield** as a sanity cap.

---

## Step 4 — WACC

$$
WACC = \frac{E}{E+D} \times K_e + \frac{D}{E+D} \times K_d \times (1 - \text{Tax Rate})
$$

### 4a — Capital Structure Weights

$$
\frac{E}{E+D} \quad \text{and} \quad \frac{D}{E+D}
$$

| Element | Definition | Source | Where to Find |
|---|---|---|---|
| `E` (Equity) | Market capitalisation | **yfinance** | `ticker.info['marketCap']` |
| `D` (Debt) | Total interest-bearing debt | **yfinance** | `balance_sheet`: `Short Term Debt + Long Term Debt` |

---

### 4b — Cost of Equity (Ke) via CAPM

$$
K_e = R_f + \beta_L \times (ERP + CRP)
$$

| Element | Definition | Source | Where to Find |
|---|---|---|---|
| `Rf` | Risk-free rate | **US Treasury** | [Daily Treasury Yields](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve) → 10-yr yield |
| `β (raw)` | Historical market beta | **yfinance** | `ticker.info['beta']` |
| `β_L (relevered)` | Relevered beta for company's leverage | **Damodaran** | Use unlevered industry beta from [betas.html](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/betas.html), then relever: `β_L = β_U × (1 + (1 - T) × D/E)` |
| `ERP` | Equity Risk Premium | **Damodaran** | [Implied ERP page](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/implprem.html) — use current implied ERP for US |
| `CRP` | Country Risk Premium (if non-US) | **Damodaran** | [ctryprem.html](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html) |

> **Beta relevering formula:**
> 1. Get **unlevered beta** for the company's sector from Damodaran
> 2. Relever using company's own D/E: `β_L = β_U × [1 + (1 − Tax Rate) × (D/E)]`
> 3. Use `β_L` in CAPM — more accurate than raw yfinance beta

---

### 4c — Cost of Debt (Kd)

$$
K_d = \frac{\text{Interest Expense}}{\text{Total Debt}} \quad \text{(or use synthetic spread)}
$$

| Element | Definition | Source | Where to Find |
|---|---|---|---|
| `Interest Expense` | From income statement | **yfinance** | `income_stmt.loc['Interest Expense']` |
| `Total Debt` | ST + LT debt | **yfinance** | `balance_sheet`: `Short Term Debt + Long Term Debt` |
| `Synthetic Kd` | If Kd from above seems off | **Damodaran** | Compute interest coverage ratio → match to [ratings.html](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html) → add spread to `Rf` |

---

## Step 5 — Equity Value (Bridge)

$$
\text{Equity Value} = \text{Enterprise Value} - \text{Net Debt} + \text{Cash}
$$

$$
\text{Intrinsic Share Price} = \frac{\text{Equity Value}}{\text{Shares Outstanding}}
$$

| Element | Source | Where to Find |
|---|---|---|
| `Enterprise Value` | Derived — PV of FCFFs + Terminal Value | Computed in Steps 1–4 |
| `Total Debt` | **yfinance** | `balance_sheet`: `Short Term Debt + Long Term Debt` |
| `Cash` | **yfinance** | `balance_sheet.loc['Cash And Cash Equivalents']` |
| `Shares Outstanding` | **yfinance** | `ticker.info['sharesOutstanding']` |

---

## Full Data Pull Cheatsheet

```python
import yfinance as yf

ticker = yf.Ticker("AAPL")

income_stmt     = ticker.financials          # EBIT, Revenue, Tax, Interest Expense
balance_sheet   = ticker.balance_sheet       # Debt, Cash, Current Assets/Liabilities
cash_flow       = ticker.cashflow            # D&A, CapEx
info            = ticker.info                # marketCap, beta, sharesOutstanding
```

| Variable | yfinance call |
|---|---|
| Revenue | `income_stmt.loc['Total Revenue']` |
| EBIT | `income_stmt.loc['EBIT']` |
| Tax Rate | `income_stmt.loc['Tax Rate For Calcs']` |
| Interest Expense | `income_stmt.loc['Interest Expense']` |
| D&A | `cash_flow.loc['Depreciation And Amortization']` |
| CapEx | `cash_flow.loc['Capital Expenditure']` |
| Current Assets | `balance_sheet.loc['Current Assets']` |
| Current Liabilities | `balance_sheet.loc['Current Liabilities']` |
| Cash | `balance_sheet.loc['Cash And Cash Equivalents']` |
| Short-Term Debt | `balance_sheet.loc['Current Debt']` |
| Long-Term Debt | `balance_sheet.loc['Long Term Debt']` |
| Market Cap | `info['marketCap']` |
| Beta | `info['beta']` |
| Shares Outstanding | `info['sharesOutstanding']` |

---

## Damodaran Pages Reference

| Data Needed | URL |
|---|---|
| Implied ERP (US, current) | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/implprem.html |
| Industry Unlevered Betas | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/betas.html |
| Country Risk Premiums | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html |
| Marginal Tax Rates by Country | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/countrytax.html |
| Synthetic Ratings & Spreads | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ratings.html |
| Industry CapEx/Sales | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/capex.html |
| Industry NWC/Sales | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wcdata.html |

---

## US Treasury Reference

| Data Needed | URL |
|---|---|
| 10-Year Yield (Risk-Free Rate) | https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve |

> Always use the **current** 10-yr yield on the date of your valuation, not a historical average.

---

*Last updated: May 2026*
