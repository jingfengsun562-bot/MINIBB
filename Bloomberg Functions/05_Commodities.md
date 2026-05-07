# 05 — Commodities

Functions for energy, metals, agriculture, and commodity futures analysis.

---

## Commodity Market Overview

### `GLCO`
**Description**: Global Commodity Prices — real-time dashboard of benchmark commodity prices across energy, metals, and agriculture.  
**Key sub-screens**:
- Energy (WTI, Brent, Natural Gas, Gasoline, Heating Oil)
- Precious Metals (Gold, Silver, Platinum, Palladium)
- Base Metals (Copper, Aluminum, Nickel, Zinc, Lead, Tin)
- Agriculture (Corn, Wheat, Soybeans, Cotton, Sugar, Coffee, Cocoa)
- Livestock (Live Cattle, Lean Hogs)

### `CMBX`
**Description**: Commodity Index Monitor — track commodity index performance (BCOM, GSCI, CRB) with sector attribution.

### `SECF` (Commodity)
**Description**: Use Security Finder filtered to Commodity asset class to locate futures contracts, ETFs, and indices.

---

## Futures Analysis

### `CT`
**Description**: Commodity Futures Price Table — all listed contracts for a commodity with price, change, volume, open interest.  
**Key sub-screens**:
- Active months display
- Settlement prices
- Volume and open interest by contract
- Spread between contracts (calendar spread)

### `GIP`
**Description**: Generic Price — continuous price chart for a commodity using the generic (front-month rolling) ticker.

### `FCA`
**Description**: Forward Curve Analysis — commodity forward curve with contango/backwardation visualization.  
**Key sub-screens**:
- Current forward curve
- Historical overlay (compare curves over time)
- Roll yield calculation
- Contango vs. backwardation indicator
- Seasonal patterns

### `CCRV`
**Description**: Commodity Curve — detailed forward curve builder with custom roll conventions.

### `COTR` / `COT`
**Description**: Commitment of Traders Report — CFTC positioning data showing commercial, non-commercial, and speculative positions.  
**Key sub-screens**:
- Net long/short by category
- Historical positioning trends
- Extreme positioning signals
- Managed money positions

---

## Energy

### `BMAP`
**Description**: Bloomberg Map — geospatial visualization of energy infrastructure (pipelines, refineries, LNG terminals, rigs).

### `OILX`
**Description**: Oil Market Fundamentals — supply/demand balance, inventory data (DOE, API), refinery runs, and trade flows.

### `LNGP`
**Description**: LNG Pricing — global LNG spot and contract pricing with shipping route economics.

### `RIGC`
**Description**: Rig Count — Baker Hughes and international rig count data with historical trends by region and basin.

---

## Metals

### `MPCM`
**Description**: Metal Prices & Charts Monitor — real-time precious and base metal prices with exchange data.

### `LME`
**Description**: London Metal Exchange data — official LME prices, warehouse stocks, and forward curves for base metals.

### `XAUUSD`
**Description**: Gold spot price — load gold as a security for full analytics (GP, TRA, etc.).

---

## Agriculture

### `AGRI`
**Description**: Agriculture Commodity Monitor — prices, weather, and fundamental data for grains, softs, and livestock.

### `WETR`
**Description**: Weather — global weather data with relevance to agriculture (rainfall, temperature anomalies, drought indices).  
**Key sub-screens**:
- Current conditions map
- Forecast (7-day, 14-day)
- Anomaly maps (vs. historical average)
- Crop condition overlay
- El Niño/La Niña tracker

### `CROP`
**Description**: Crop Monitor — USDA and global crop data including production, yields, acreage, and trade flows.

---

## Commodity Supply & Demand

### `BSUP`
**Description**: Bloomberg Supply — commodity supply data and forecasts by country and company.

### `BDEM`
**Description**: Bloomberg Demand — commodity demand data by end-use sector and geography.

### `TANK`
**Description**: Tanker Tracker — real-time tracking of oil tankers globally with cargo estimates and route data.

### `OPEC`
**Description**: OPEC Monitor — OPEC production quotas, compliance, and meeting calendar.
