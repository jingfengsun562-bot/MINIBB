# 06 — Derivatives & Options

Functions for options pricing, volatility analysis, strategy building, and structured products.

---

## Options Overview

### `OMON`
**Description**: Options Monitor — real-time options chain with bid/ask, volume, open interest, and Greeks for any underlying.  
**Key sub-screens**:
- Call/put chains by expiry
- Greeks (delta, gamma, theta, vega, rho)
- Implied volatility per strike
- Volume and open interest columns
- Custom column builder
- Unusual activity highlighting

### `OSA`
**Description**: Options Scenario Analysis — model P&L of an options position under user-defined scenarios (spot move, vol change, time decay).  
**Key sub-screens**:
- Position builder (multi-leg)
- Scenario grid (spot × vol matrix)
- P&L chart (2D and 3D)
- Greeks sensitivity
- Break-even analysis

### `OV`
**Description**: Option Valuation — single option pricer using Black-Scholes, Binomial, or Monte Carlo models.  
**Key sub-screens**:
- Model selection (BS, Binomial, Local Vol, Stochastic Vol)
- Input parameters (spot, strike, vol, rate, dividend)
- Greeks output
- What-if analysis (change any input)

---

## Volatility Analysis

### `SKEW`
**Description**: Volatility Skew — implied volatility by strike (moneyness) for a given expiry. Shows put skew, call skew, and smile shape.  
**Key sub-screens**:
- Skew by expiry
- Historical skew comparison
- Skew percentile
- Delta-space vs. strike-space display

### `VOLC`
**Description**: Volatility Cone — realized volatility distribution across time windows. Shows current realized vol in percentile context.

### `GV`
**Description**: Implied Volatility Graph — chart implied vol (ATM or specific strike) over time for any underlying.

### `HIVG`
**Description**: Historical Implied Volatility Graph — overlay realized vs. implied vol to analyze the volatility risk premium.

### `OVDV`
**Description**: Options Volatility Surface — full implied vol surface (strike × expiry) as a 3D surface or heatmap.  
**Key sub-screens**:
- Surface display (3D, heatmap, table)
- Historical surface comparison
- Term structure (ATM vol across expiries)
- Smile/skew analysis by tenor

---

## Strategy Building

### `OVME`
**Description**: Options Valuation Multi-Leg — build and analyze multi-leg options strategies (spreads, straddles, strangles, condors, etc.).  
**Key sub-screens**:
- Strategy templates (vertical, calendar, butterfly, iron condor, collar)
- Custom leg builder
- Combined Greeks
- P&L at expiry chart
- Margin requirement estimate
- Break-even analysis

### `COST`
**Description**: Cost of Carry — calculate theoretical futures price from spot price, interest rate, and carry.

### `DLIB`
**Description**: Derivatives Library — browse and price structured products and exotic options.  
**Key sub-screens**:
- Product templates (autocallables, accumulators, range accruals)
- Custom payoff builder
- Monte Carlo pricing
- Sensitivity analysis

---

## Interest Rate Derivatives

### `SWPM`
**Description**: Swap Manager — the central function for interest rate swap pricing and risk analysis.  
**Key sub-screens**:
- Swap pricer (IRS, basis swap, cross-currency swap, OIS)
- Custom schedule builder
- Mark-to-market valuation
- DV01 / PV01
- Cash flow schedule
- CVA/DVA adjustment
- Swaption pricer

### `VCUB`
**Description**: Swaption Volatility Cube — implied vol for swaptions by expiry and swap tenor.  
**Key sub-screens**:
- ATM vol matrix (option expiry × swap tenor)
- Skew by strike
- Historical comparison
- Normal vs. lognormal vol

### `IRDD`
**Description**: Interest Rate Derivatives Dashboard — monitor swap spreads, swaption vols, and cap/floor pricing across currencies.

---

## Credit Derivatives

### `CDSW`
**Description**: Credit Default Swap Pricer — price single-name CDS with spread, upfront, duration, and default probability.  
**Key sub-screens**:
- CDS spread (running and upfront)
- Hazard rates / default probability curve
- Recovery rate assumption
- Mark-to-market P&L
- DV01 (CR01)
- Roll-down analysis

### `CDSD`
**Description**: CDS Dashboard — monitor CDS spreads across a portfolio or sector.

### `ITRX` / `CDX`
**Description**: Credit Index Monitor — iTraxx (Europe/Asia) and CDX (North America) index families with spread, roll, and basis data.

---

## Futures & Listed Derivatives

### `CTM`
**Description**: Contract Table Monitor — real-time futures and listed options monitor by exchange.

### `EXC`
**Description**: Exchange Data — exchange-level data including volume, open interest, and contract specifications.

### `SECF` (Derivatives)
**Description**: Use Security Finder filtered to derivatives to locate futures, options, and listed contracts by underlying.
