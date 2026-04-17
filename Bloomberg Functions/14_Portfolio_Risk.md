# 14 — Portfolio & Risk Analytics

Functions for portfolio construction, performance attribution, risk management, and compliance.

---

## Portfolio Management

### `PORT`
**Description**: Portfolio Analytics — the central portfolio management tool. Upload or link a portfolio to access attribution, risk, exposure, and what-if analysis.  
**Key sub-screens**:
- **Holdings**: Full position list with market value, weight, and P&L
- **Performance**: Time-weighted and money-weighted returns vs. benchmark
- **Attribution**: Return attribution by sector, country, security, factor
  - Brinson-Fachler (allocation, selection, interaction)
  - Fixed income attribution (carry, curve, spread, FX)
- **Risk**: Tracking error, beta, VaR, volatility, drawdown
- **Characteristics**: Aggregate portfolio statistics (P/E, yield, duration, credit quality)
- **Exposure**: Sector, country, currency, market cap, credit rating breakdowns
- **What-if**: Model trades to see impact on risk and exposure before execution
- **Compliance**: Rule-based compliance checks against investment guidelines
- **Historical**: Performance and risk over custom date ranges

### `PRTU`
**Description**: Portfolio Upload — import portfolio holdings from Excel, CSV, or OMS connection into PORT.

### `BBU`
**Description**: Bloomberg Portfolio Upload — alternative upload path with template-based import.

---

## Risk Analytics

### `MARS`
**Description**: Multi-Asset Risk System — enterprise-level risk analytics with VaR, stress testing, and scenario analysis.  
**Key sub-screens**:
- VaR (parametric, historical, Monte Carlo)
- Component VaR / marginal VaR
- Stress testing (historical scenarios, custom shocks)
- Factor risk decomposition
- Liquidity risk analysis
- Counterparty risk
- P&L explanation

### `RSKF`
**Description**: Risk Factor Analysis — decompose portfolio risk into systematic factors (equity, rates, credit, FX, commodity).

### `GRE`
**Description**: Greeks — aggregate option Greeks for a portfolio with what-if scenarios.

---

## Performance Analysis

### `TRA`
**Description**: Total Return Analysis — total return of a security or portfolio with risk-adjusted metrics.  
**Key sub-screens**:
- Cumulative and annualized returns
- Risk metrics (vol, Sharpe, Sortino, Treynor, Information Ratio)
- Drawdown analysis (max drawdown, recovery period)
- Rolling return windows
- Calendar year performance table

### `COMP` (Portfolio)
**Description**: Compare portfolio performance against benchmarks and peer portfolios.

### `ATTR`
**Description**: Attribution Report — detailed return attribution (Brinson model for equity; carry/curve/spread for fixed income).

---

## Factor & Style Analysis

### `FACA`
**Description**: Factor Analysis — expose portfolio factor tilts (value, growth, momentum, quality, size, volatility) relative to benchmark.  
**Key sub-screens**:
- Active factor exposures
- Factor contribution to tracking error
- Factor return decomposition
- Historical factor tilt evolution

### `PORT` → Characteristics
**Description**: Portfolio characteristics tab shows aggregate style metrics (P/E, P/B, ROE, dividend yield, earnings growth) vs. benchmark.

---

## Scenario & Stress Testing

### `SHOC`
**Description**: Shock Analysis — apply user-defined shocks to rates, spreads, FX, equity levels, and see P&L impact.

### `STST`
**Description**: Stress Testing — apply historical stress scenarios (2008 GFC, COVID-19, Taper Tantrum, etc.) to the portfolio.

### `SGEN`
**Description**: Scenario Generator — build custom multi-factor scenarios and apply to portfolio.

---

## Compliance & Reporting

### `CMPL`
**Description**: Compliance — rule-based compliance monitoring for portfolios against investment guidelines and regulations.  
**Key sub-screens**:
- Pre-trade compliance (check before executing)
- Post-trade compliance monitoring
- Rule library (concentration limits, rating constraints, duration bands)
- Breach alerts
- Audit trail

### `PRTL`
**Description**: Portfolio Reporting — generate formatted portfolio reports (performance, attribution, risk, holdings).

### `PCRD`
**Description**: Portfolio Credit — credit-specific risk analytics for fixed income portfolios (spread duration, DTS, default risk).

---

## Trading Tools (Portfolio-Level)

### `EMSX`
**Description**: Execution Management System — order routing, algorithmic trading, and execution analytics integrated with PORT.  
**Key sub-screens**:
- Order blotter
- Algorithmic trading strategies
- Broker routing
- Transaction cost analysis (TCA)
- Basket trading

### `AIM`
**Description**: Asset & Investment Manager — OMS (Order Management System) for asset managers with compliance, allocation, and execution workflow.
