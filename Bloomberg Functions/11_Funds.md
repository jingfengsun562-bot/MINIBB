# 11 — Fund Analysis

Functions for mutual funds, ETFs, hedge funds, and asset management data.

---

## Fund Search & Screening

### `FSRC`
**Description**: Fund Screener — screen mutual funds and ETFs by asset class, geography, strategy, performance, expense ratio, AUM, and more.  
**Key sub-screens**:
- Criteria builder (asset class, category, region, manager, currency)
- Performance filters (1Y, 3Y, 5Y, Sharpe, alpha)
- Expense ratio and fee comparison
- Fund flow data
- Results export

### `ETFS`
**Description**: ETF Screener — dedicated ETF search with filters for structure, replication method, tracking error, and AUM.

### `FLNG`
**Description**: Fund Flow — aggregate fund flow data by fund category, geography, and time period.

---

## Fund Analytics (Security-Level)

### `DES` (Fund)
**Description**: Fund Description — summary page with strategy, benchmark, launch date, AUM, fees, and manager.

### `FSTA`
**Description**: Fund Statistics — performance, risk, and return statistics with benchmark comparison.  
**Key sub-screens**:
- Return table (1M, 3M, YTD, 1Y, 3Y, 5Y, SI)
- Risk metrics (vol, Sharpe, Sortino, max drawdown, beta, alpha)
- Rolling returns
- Calendar year returns
- Up/down capture ratio

### `FUND`
**Description**: Fund Holdings — full portfolio holdings with sector/country/market cap breakdown.  
**Key sub-screens**:
- Top holdings
- Sector allocation
- Country allocation
- Market cap distribution
- Credit quality breakdown (for fixed income funds)
- Historical holdings comparison

### `FMAP`
**Description**: Fund Map — geographic visualization of fund holdings on a world map.

### `COMP` (Fund)
**Description**: Fund Comparison — side-by-side comparison of multiple funds on performance, risk, holdings, and fees.

---

## ETF-Specific Analytics

### `ETF`
**Description**: ETF Analytics — ETF-specific data including creation/redemption, premium/discount, tracking error, and market maker data.  
**Key sub-screens**:
- Intraday NAV vs. price (premium/discount)
- Tracking error vs. benchmark
- Authorized participant activity
- Creation/redemption basket
- Implied liquidity (underlying vs. ETF)
- Competing ETFs comparison

### `ETFG`
**Description**: ETF Globe — explore the global ETF landscape by asset class, issuer, and theme.

---

## Hedge Funds

### `BFND`
**Description**: Bloomberg Fund Search (Hedge Funds) — search hedge funds by strategy, AUM, performance, and manager.

### `HFND`
**Description**: Hedge Fund Monitor — hedge fund performance, flow data, and strategy-level analytics.  
**Key sub-screens**:
- Strategy returns (L/S Equity, Event Driven, Macro, Quant, etc.)
- Fund of funds data
- AUM trends
- Investor composition
- Lockup and redemption terms

### `PCRD`
**Description**: 13F Filings — institutional holdings from SEC 13F filings, showing what hedge funds and institutional investors hold.

---

## Fund Manager Analysis

### `FMGR`
**Description**: Fund Manager — manager track record, fund history, and AUM under management.

### `PEOP` (Asset Management)
**Description**: People search filtered to asset managers — find portfolio managers and their fund assignments.
