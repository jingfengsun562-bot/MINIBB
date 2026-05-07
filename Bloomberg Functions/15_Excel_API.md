# 15 — Bloomberg Excel API & Data Tools

Functions for extracting Bloomberg data into Excel, programmatic access, and data scripting.

---

## Bloomberg Excel Add-In (BQL & Classic)

### `BDP` — Bloomberg Data Point
**Description**: Pull a single current data point for a security.  
**Syntax**: `=BDP("AAPL US Equity", "PX_LAST")`  
**Key details**:
- Returns real-time or most recent value
- Supports overrides (e.g., currency, date, period)
- One field per cell (use multiple BDP for multiple fields)
- Override syntax: `=BDP("AAPL US Equity","BEST_EPS",{"BEST_FPERIOD_OVERRIDE","1BF"})`

### `BDH` — Bloomberg Data History
**Description**: Pull historical time series data for a security.  
**Syntax**: `=BDH("AAPL US Equity","PX_LAST","1/1/2023","12/31/2023")`  
**Key details**:
- Returns date + value columns
- Supports multiple fields in one call
- Periodicity override: Daily, Weekly, Monthly, Quarterly, Yearly
- Fill options: previous value, nil, zero
- Calendar override: actual trading days, all calendar days
- Currency override for cross-currency history

### `BDS` — Bloomberg Data Set
**Description**: Pull multi-row data sets (e.g., index members, option chain, dividend history).  
**Syntax**: `=BDS("SPX Index","INDX_MWEIGHT")`  
**Key details**:
- Returns tables (multiple rows and columns)
- Used for: index members, holders, peers, earnings calendar, option chains, yield curve points
- Override parameters vary by data set
- Can return very large data sets — use overrides to filter

### `BEQS` — Bloomberg Equity Screening
**Description**: Run a saved EQS screen in Excel and return results as a table.  
**Syntax**: `=BEQS("My Saved Screen")`  
**Key details**:
- References screens saved in EQS on the terminal
- Returns security list matching criteria
- Can be used as input universe for BDP/BDH

---

## Bloomberg Query Language (BQL)

### `BQL`
**Description**: Bloomberg's SQL-like query language for bulk data retrieval, screening, and analytics directly in Excel or Python.  
**Key features**:
- **Universe definition**: `members('SPX Index')`, `filter()`, `screen()`
- **Data retrieval**: `get(px_last)`, `get(pe_ratio)`
- **Time series**: `get(px_last) for dates(-30d, 0d)`
- **Calculations**: `get(px_last / avg(px_last, 200))` — moving averages, z-scores, custom metrics
- **Grouping**: `group().avg()`, `group().sum()` — aggregate by sector, country, etc.
- **Ranking**: `rank()`, `percentile()` — cross-sectional ranking

**Example queries**:
```
// Get PE ratio for all S&P 500 members
get(pe_ratio) for members('SPX Index')

// Screen for high-dividend, low-PE stocks
get(px_last, pe_ratio, dividend_yield)
for filter(members('SPX Index'), dividend_yield > 3 and pe_ratio < 15)

// 6-month momentum ranking
get(rank(return(px_last, -126d))) for members('SPX Index')
```

**Excel integration**: `=BQL("get(pe_ratio) for members('SPX Index')")`

---

## Data Discovery Tools

### `FLDS`
**Description**: Field Search — look up Bloomberg field mnemonics by keyword. Essential for building BDP/BDH/BDS formulas.  
**Key details**:
- Search by keyword (e.g., "earnings per share" → BEST_EPS, IS_EPS, TRAIL_12M_EPS)
- Shows field definition, data type, applicable asset classes
- Lists override parameters
- Copy mnemonic directly to Excel

### `WAPI`
**Description**: API Function Builder — interactive tool to construct Excel formulas.  
**Key details**:
- Select function type (BDP, BDH, BDS)
- Browse and select fields
- Configure overrides visually
- Preview output
- Copy completed formula to clipboard

### `DAPI`
**Description**: Data API documentation — overview of all Bloomberg data access methods (Desktop API, Server API, B-PIPE).

---

## Python & Programmatic Access

### `BQNT`
**Description**: Bloomberg Quant (BQuant) — Python-based research environment hosted on Bloomberg.  
**Key features**:
- Jupyter notebook environment on the terminal
- Access to Bloomberg data via `bql` Python library
- Pre-installed quant libraries (pandas, numpy, scipy, sklearn)
- Charting and visualization
- Backtest framework

### `bqlx` / `blpapi`
**Description**: Bloomberg Python SDK — programmatic access to Bloomberg data via Python.  
**Key details**:
- `blpapi`: Low-level Bloomberg API (requires B-PIPE or Desktop API)
- `bql`: BQL library for Python (works in BQuant or with Desktop API)
- `xbbg`: Open-source Python wrapper for Bloomberg Desktop API
- Supports real-time streaming, historical data, and reference data

---

## Data Export & Connectivity

### `DAPI`
**Description**: Data API overview — documentation hub for:
- **Desktop API**: Access from local Excel/Python on the terminal PC
- **Server API (SAPI)**: Server-side data access for applications
- **B-PIPE**: Enterprise-grade real-time and reference data feed
- **Data License**: Bulk data delivery (end-of-day files)
- **Enterprise Access Point**: Cloud-based API access

### `BSRCH`
**Description**: Bloomberg Search — structured data search with exportable results. Useful for building security universes for Excel analysis.

### Clipboard & Copy
**Description**: Most Bloomberg screens support `Ctrl+C` to copy data tables, which paste cleanly into Excel with headers.

---

## Practical Tips

| Task | Recommended Approach |
|------|---------------------|
| One data point, one security | `BDP` |
| Time series for one security | `BDH` |
| List data (members, holders, etc.) | `BDS` |
| Bulk data for many securities | `BQL` in Excel or Python |
| Screening in Excel | `BEQS` (saved screen) or `BQL` with `filter()` |
| Real-time streaming in Excel | `BDP` with auto-refresh enabled |
| Large-scale backtesting | `BQNT` (Python) or `BQL` |
| Custom analytics & models | `BQL` for data pull → Excel/Python for computation |
