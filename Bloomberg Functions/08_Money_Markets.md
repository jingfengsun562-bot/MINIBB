# 08 — Money Markets

Functions for short-term rates, repos, commercial paper, certificates of deposit, and central bank policy rates.

---

## Rate Overview

### `BTMM`
**Description**: Bond & Money Markets Monitor — the go-to dashboard for benchmark rates by country. Shows government yields, swap rates, and money market rates.  
**Key sub-screens**:
- Country selector (US, UK, EU, Japan, China, etc.)
- Government benchmark yields
- Swap rates by tenor
- Money market rates (overnight, 1M, 3M, 6M)
- Central bank policy rate
- Spread to key benchmarks

### `MMCN`
**Description**: Money Market Curves — money market yield curves by instrument type and currency.

### `RFSR`
**Description**: Reference Rate Summary — dashboard for risk-free rates (SOFR, ESTR, SONIA, TONA, SARON) with historical data and term structures.

---

## Key Short-Term Rates

### `SOFRRATE`
**Description**: SOFR (Secured Overnight Financing Rate) — current rate, historical data, and forward-implied SOFR curve.

### `ESTR`
**Description**: Euro Short-Term Rate — ECB's overnight reference rate with historical data.

### `SONIA`
**Description**: Sterling Overnight Index Average — Bank of England's overnight rate.

### `FEDL01`
**Description**: Fed Funds Effective Rate — daily effective federal funds rate.

### `USGG3M / USGG6M / USGG2Y`
**Description**: US Generic Government yields by tenor — quick access to benchmark Treasury yields.

---

## Repos & Secured Funding

### `REPO`
**Description**: Repo Monitor — repo rates by collateral type, tenor, and counterparty.  
**Key sub-screens**:
- General collateral (GC) rates
- Special rates (specific security)
- Tenor breakdown (O/N, 1W, 1M, 3M)
- Triparty vs. bilateral
- Fail rates

### `RPSV`
**Description**: Repo/Reverse Repo Calculator — compute repo rates, haircuts, and proceeds for specific transactions.

---

## Commercial Paper & Certificates of Deposit

### `CPRL`
**Description**: Commercial Paper Rate Monitor — CP rates by issuer rating, tenor, and program.

### `CDRL`
**Description**: Certificate of Deposit Rate Monitor — CD rates by bank, tenor, and currency.

---

## Central Bank Policy

### `WIRP`
**Description**: World Interest Rate Probability — market-implied probability of central bank rate moves at upcoming meetings.  
**Key sub-screens**:
- Meeting-by-meeting probability table
- Implied rate path chart
- Comparison of market vs. dot plot (Fed)
- History of actual vs. market expectations
- Multi-country comparison

### `CENT`
**Description**: Central Bank Monitor — global central bank policy rates, last action, next meeting, and forward guidance summary.

### `FOMC`
**Description**: Federal Reserve Monitor — FOMC meeting dates, statements, minutes, dot plot, and press conference transcripts.

### `ECBM`
**Description**: ECB Monitor — European Central Bank meeting schedule, decisions, press conferences, and staff projections.

---

## T-Bills & Government Short-Term

### `BTT`
**Description**: Treasury Bill Table — US T-Bill pricing, yields, and auction results.

### `AUCT`
**Description**: Auction Monitor — upcoming and recent government debt auctions globally with results (bid-to-cover, tail, etc.).  
**Key sub-screens**:
- Calendar of upcoming auctions
- Recent results (high yield, bid-to-cover, allotment)
- Dealer takedown
- Indirect/direct bidder breakdown
- Historical auction trends
