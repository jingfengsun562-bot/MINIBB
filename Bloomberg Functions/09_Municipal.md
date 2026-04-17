# 09 — Municipal Finance

Functions for US municipal bond analysis, screening, credit, and tax-equivalent yield calculations.

---

## Muni Search & Screening

### `MUNI`
**Description**: Municipal Bond Search — screen the muni universe by state, issuer, sector (GO, revenue), rating, maturity, coupon, and tax status.  
**Key sub-screens**:
- Criteria builder (state, sector, use of proceeds, rating, AMT status)
- Results with YTM, YTC, OAS, price
- New issue calendar
- Export to Excel or PORT

### `SMUN`
**Description**: State Municipal Overview — state-level muni dashboard with outstanding debt, credit metrics, and economic indicators.

---

## Muni Analytics

### `YAS` (Muni)
**Description**: Yield & Spread Analysis for munis — includes tax-equivalent yield (TEY), after-tax yield, AMT considerations.  
**Key sub-screens**:
- TEY calculator (input federal/state/local tax rates)
- Muni vs. Treasury spread
- Call analysis (YTC, YTW)
- De minimis tax impact
- Cash flow projections

### `MMAP` (Muni)
**Description**: Muni Market Map — heat map of muni market performance by state and sector.

### `RATD` (Muni)
**Description**: Muni issuer rating detail — ratings from Moody's, S&P, Fitch, and Kroll for muni issuers.

---

## Muni Market Data

### `MMD`
**Description**: Municipal Market Data — AAA benchmark muni yield curve (the standard muni curve) with historical comparison.  
**Key sub-screens**:
- AAA curve by maturity
- Muni/Treasury ratio by maturity
- Historical curve overlay
- Spread to Treasuries and swaps

### `BVAL` (Muni)
**Description**: Bloomberg Valuation — fair value pricing for thinly traded muni bonds using Bloomberg's evaluated pricing model.

### `NIM` (Muni)
**Description**: New Issue Monitor for munis — pipeline of upcoming muni deals with pricing details and underwriter info.

---

## Muni Issuer Analysis

### `MIFA`
**Description**: Municipal Issuer Financial Analysis — financial data for state and local government issuers (revenue, expenditure, fund balance, pension obligations).

### `PENSION`
**Description**: Public Pension Monitor — funded status, asset allocation, and return assumptions for state and local pension plans.

### `ISSD`
**Description**: Issuer Description — issuer-level overview with outstanding debt, governance, and economic base.
