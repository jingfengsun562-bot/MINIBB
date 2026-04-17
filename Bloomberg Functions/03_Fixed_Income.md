# 03 — Fixed Income

Functions for bond search, analytics, yield curves, spread analysis, and credit markets.

---

## Bond Search & Discovery

### `SRCH` (Fixed Income)
**Description**: Bond Search — screen the global bond universe by issuer, maturity, coupon, rating, currency, structure, and more.  
**Key sub-screens**:
- Criteria builder (issuer, rating, currency, coupon type, maturity range)
- Pre-built templates (Investment Grade, High Yield, Sovereigns, EM)
- Results table with YTM, spread, price, rating
- Export to Excel or PORT

### `FIT`
**Description**: Fixed Income Trading — real-time composite pricing for bonds with bid/ask, yield, spread, and contributed quotes.

### `ALLQ`
**Description**: All Quotes — aggregated dealer quotes for a specific bond (BVAL, BGN, contributed prices).  
**Key sub-screens**:
- Executable quotes vs. indicative
- Historical price/yield
- Source breakdown (dealer, electronic platform)

---

## Bond Analytics (Security-Level)

### `DES` (Bond)
**Description**: Bond Description — key terms (coupon, maturity, call schedule, seniority, covenants), identifiers, and issuer info.  
**Key sub-screens**:
- Terms & conditions
- Call/put schedule
- Sinking fund
- Covenants summary
- Identifiers (ISIN, CUSIP, FIGI)

### `YAS`
**Description**: Yield & Spread Analysis — the central bond analytics function. Calculates yield, spread, duration, convexity, and scenario analysis.  
**Key sub-screens**:
- Yield calculations (YTM, YTC, YTW, current yield)
- Spread measures (G-spread, Z-spread, OAS, ASW, I-spread)
- Duration & convexity (modified, effective, Macaulay, key rate)
- Scenario analysis (shift yield curve, change spread)
- Cash flow table
- Risk measures (DV01, CR01)

### `CSHF`
**Description**: Cash Flow — projected cash flows for a bond, including principal, coupon, and amortization schedule.

### `NIM`
**Description**: New Issue Monitor — real-time feed of new bond issues across the primary market (IG, HY, EM, Sovereign).  
**Key sub-screens**:
- Pipeline (mandated / announced / priced)
- Filter by currency, rating, region, sector
- Deal terms and pricing
- Book runner / lead manager info

---

## Yield Curves

### `GC`
**Description**: Government Curve — sovereign yield curves for any country with historical comparison and butterfly/slope analysis.  
**Key sub-screens**:
- Curve display (spot, par, forward, zero)
- Historical overlay (compare to any past date)
- Butterfly spreads (2s5s10s)
- Slope analysis (2s10s, 2s30s)
- Curve flattening/steepening monitor

### `FWCV`
**Description**: Forward Curve — implied forward rates from the current yield curve. Useful for break-even and rate expectation analysis.

### `SWCV`
**Description**: Swap Curve — interest rate swap curves by currency with spread to government bonds.

### `IYC`
**Description**: Interactive Yield Curve — animated yield curve over time. Drag the timeline to see how the curve evolved.

### `CRVF`
**Description**: Curve Finder — search and compare yield curves across countries, sectors, and curve types.

---

## Spread & Relative Value

### `CSDR`
**Description**: Credit Spread Dashboard — monitor credit spreads by rating, sector, and maturity bucket.

### `RATD`
**Description**: Ratings Detail — credit ratings from Moody's, S&P, and Fitch with outlook and historical changes.

### `AGGD`
**Description**: Bloomberg Aggregate Dashboard — monitor the Bloomberg Aggregate bond indices with spread, yield, and duration.

### `CAST`
**Description**: Credit Analysis Spread Tool — decompose bond spreads into components (liquidity, credit, sector).

---

## Structured Products

### `MTGE`
**Description**: Mortgage-Backed Securities screen — MBS analytics including prepayment speeds, WAL, OAS, and scenario analysis.  
**Key sub-screens**:
- Pool-level detail (factor, WAC, WAM, WALA)
- Prepayment model (CPR, PSA, Bloomberg model)
- OAS analysis
- Cash flow waterfall
- Scenario matrix (rate shift × prepayment speed)

### `ABS`
**Description**: Asset-Backed Securities — ABS deal structure, tranche detail, and performance data.

### `CMBS`
**Description**: Commercial MBS — CMBS deal analysis with loan-level data, DSCR, LTV, and delinquency.

### `CMO`
**Description**: Collateralized Mortgage Obligation — CMO tranche analytics, cash flow waterfall, and support/companion tranche behavior.

---

## Government & Sovereign

### `BTMM`
**Description**: Bond & Money Markets Monitor — real-time dashboard of government bond yields, swap rates, and money market rates by country.  
**Key sub-screens**:
- Country selection
- Benchmark yields (2Y, 5Y, 10Y, 30Y)
- Swap rates
- Money market rates (SOFR, ESTR, SONIA, etc.)
- Spread to Germany / US

### `WGBI`
**Description**: World Government Bond Index monitor — track global sovereign bond performance.

### `DDIS` (Sovereign)
**Description**: Sovereign debt distribution — outstanding government debt by maturity, currency, and holder type.
