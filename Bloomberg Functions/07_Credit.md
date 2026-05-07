# 07 — Credit Analysis

Functions for credit risk assessment, default probability, CDS markets, and credit-specific screening.

---

## Credit Risk Assessment

### `CRPR`
**Description**: Credit Risk Profile — comprehensive credit risk summary for an issuer including ratings, default probability, and credit score.  
**Key sub-screens**:
- Bloomberg default risk score (DRSK)
- Implied default probability (from CDS or bonds)
- Rating history (Moody's, S&P, Fitch)
- Peer comparison
- Z-score / Altman model

### `RATD`
**Description**: Rating Detail — current and historical credit ratings from all three agencies with outlook and watch status.  
**Key sub-screens**:
- Current ratings (LT, ST, issuer, issue-level)
- Outlook and CreditWatch
- Rating history timeline
- Split-rating indicator
- Sector rating distribution

### `DRSK`
**Description**: Default Risk — Bloomberg's proprietary default risk model output with 1-year default probability and credit score.

### `WCDX`
**Description**: World CDS Monitor — global CDS spread monitor by geography and sector.

---

## Credit Screening & Monitoring

### `CSDR`
**Description**: Credit Spread Dashboard — real-time monitoring of credit spreads by rating bucket, sector, maturity, and geography.  
**Key sub-screens**:
- IG vs. HY spread comparison
- Sector spread breakdown
- Spread percentile ranking
- Historical spread chart
- Spread-per-turn of leverage

### `CSCR`
**Description**: Credit Screening — screen bonds and issuers by credit criteria (rating, spread, leverage, coverage ratios).

### `RATC`
**Description**: Rating Changes — real-time feed of rating upgrades, downgrades, and outlook changes across agencies.

### `DTRP`
**Description**: Distressed & Restructuring — monitor distressed credits, bankruptcies, and restructuring events.

---

## Credit Analytics

### `CRDT`
**Description**: Credit Analysis — deep-dive credit analytics for an issuer including leverage, coverage, liquidity, and maturity wall.  
**Key sub-screens**:
- Leverage trends (Debt/EBITDA, Net Debt/EBITDA)
- Coverage ratios (Interest Coverage, DSCR)
- Liquidity analysis (cash, revolver, maturities)
- Maturity wall visualization
- Free cash flow analysis
- Peer benchmarking

### `CRVD`
**Description**: Credit Curve — issuer-specific credit curve plotting yields or spreads across its outstanding bonds by maturity.

### `LSTA`
**Description**: Leveraged Loan Monitor — leveraged loan market data (LSTA/LPC) with pricing, new issue pipeline, and CLO data.

### `CLO`
**Description**: CLO Monitor — Collateralized Loan Obligation analysis with deal structure, performance tests, and manager rankings.
