# Listed Company Fundamentals Schema — Reference

**Version:** 1.0  
**Spec file:** `listed_company.schema.json` (JSON Schema Draft 2020-12)  
**Sample file:** `pfizer_sample.json`

A universal schema for public listed companies in the global stock market. Designed as the **logical** model for a Bloomberg-style fundamentals store. The physical layer materializes this into a flat `(company_id, period_id, basis, metric_id)` fact table plus a `dim_metric` registry.

---

## 1. Design principles

| Principle | Decision |
|---|---|
| Use case | Static analytical DB (Bloomberg-style fundamentals store) |
| Estimates model | Three layers per period: **reported** + **consensus** + **single house view** |
| Reporting bases | All bases stored in parallel under each period (US-GAAP, Non-GAAP, IFRS, J-GAAP, etc.). `BasisFinancials` is keyed by basis. |
| Industry KPIs | Flexible JSON `industry_kpis{}` — sector-agnostic, no validation. Convention key in `classification.internal_sector_tag`. |
| Provenance | Medium-grain. One `Provenance` record per major statement block (IS / BS / CF / segments / industry_kpis). |
| Granularity | Optional drill-down. Required: `Period.{reported, consensus}.<basis>.income_statement.revenue`. Everything below segment-level is optional. |
| Time-series | Logical: one `Period[]` array per company. Physical: flatten to fact table on materialization. |
| Multi-listing | Primary listing is canonical; ADRs/H-shares/dual-listings tracked in `identifiers.other_listings[]`. Same `company_id`. |

---

## 2. Top-level structure

```
ListedCompany
├── company_id                    Stable internal ID, e.g. PFE.XNYS
├── identifiers                   Tickers + ISIN/CUSIP/LEI/CIK/FIGI/SEDOL/RIC + other_listings[]
├── legal_name, former_names
├── domicile_country, headquarters_country
├── reporting_currency, trading_currency
├── fiscal_year_end_month
├── accounting_standard           US-GAAP | IFRS | J-GAAP | PRC-GAAP | HKFRS | ...
├── filing_regime                 SEC-10K-10Q | SEC-20F | HK-Annual | PRC-A-Share | ...
├── classification                GICS + ICB + NAICS + SIC + internal_sector_tag
├── share_capital                 Share classes, outstanding, treasury, free float, buyback authorization
├── ownership                     Top holders, institutional/insider %        (OPTIONAL)
├── esg                           Sustainability snapshot                      (OPTIONAL)
├── periods[]                     Time series — the financial heart
├── house_view                    Single broker view: rating, target, DCF, multiples, SOTP, thesis
├── debt_schedule[]               Per-instrument debt list                     (OPTIONAL)
└── metadata                      schema_version, last_updated, completeness
```

---

## 3. The `Period` object — heart of the time series

Each period bundles **reported**, **consensus**, and **house_view_estimates** for the same fiscal interval.

```
Period
├── period_id                     {company_id}__{period_label}, globally unique
├── period_type                   Q | S | A | TTM | YTD | STUB
├── period_label                  "1Q24A", "2025E", "FY2023A"
├── fiscal_period_end / start
├── is_estimate, is_restated
├── reported           : MultibasisFinancials      — as filed
├── consensus          : ConsensusBlock            — street snapshot
├── house_view_estimates: MultibasisFinancials     — house forecast (forward periods)
└── guidance_in_effect : GuidanceBlock             — management outlook
```

### `MultibasisFinancials` — the reporting-basis switch

A dictionary keyed by reporting basis. Each value is a full `BasisFinancials` block.

```
{
  "US_GAAP":          BasisFinancials,
  "NON_GAAP_ADJUSTED": BasisFinancials,
  "IFRS":             BasisFinancials   // dual-reporters only
}
```

This is how Pfizer's "Adjusted Diluted EPS $3.25–$3.45" lives next to GAAP net income. Reconciliation deltas live inside `BasisFinancials.reconciliations[]`.

### `BasisFinancials`

```
BasisFinancials
├── income_statement              Standard line items, fully populated
├── balance_sheet                 Standard line items
├── cash_flow                     Standard CFO/CFI/CFF + FCF
├── per_share                     EPS, BVPS, TBVPS, DPS, payout
├── ratios                        Margins, returns, leverage, liquidity, working capital
├── operating_segments[]          As reported, with optional industry_kpis per segment
├── geographic_breakdown[]        Revenue by region
├── industry_kpis{}               Top-level sector KPIs (flexible JSON)
├── reconciliations[]             GAAP↔Non-GAAP bridge (only if non-GAAP basis)
└── provenance                    One per block: IS, BS, CF, segments, industry_kpis
```

---

## 4. Industry KPIs — flexible JSON convention

`industry_kpis` is `additionalProperties: true`. To keep things queryable later, the convention is: **`classification.internal_sector_tag`** tells consumers what shape to expect.

Recommended tag → expected shape mapping (used by code that consumes the schema):

### `PHARMA`
```json
{
  "industry_kpis": {
    "product_revenue": [
      {"product": "Eliquis", "indication": "Anticoagulant", "revenue": 1714.2, "yoy_growth": 0.371, "patent_loe_year": 2026}
    ],
    "pipeline": [
      {"asset": "Danuglipron", "indication": "Obesity", "phase": "Ph2b", "pdufa_date": null, "peak_sales_estimate": 10000, "probability_of_success": 0.35}
    ],
    "covid_franchise_split": {"covid_revenue": 56000, "ex_covid_revenue": 44331},
    "rd_intensity_pct": 0.187
  }
}
```

### `BANK_IB`
```json
{
  "industry_kpis": {
    "business_line_revenue": [
      {"line": "InvestmentBanking", "revenue": 1620},
      {"line": "FICC", "revenue": 4180},
      {"line": "Equities", "revenue": 3010},
      {"line": "AssetWealthManagement", "revenue": 3550},
      {"line": "PlatformSolutions", "revenue": 700}
    ],
    "capital_ratios": {
      "tier1_common_ratio": 0.143, "tier1_capital_ratio": 0.155, "total_capital_ratio": 0.179, "slr": 0.058, "tlac_ratio": 0.241
    },
    "rwa_billions": {"advanced": 615, "standardized": 590},
    "var_total": 105,
    "var_components": {"interest_rate": 60, "equity": 42, "fx": 18, "commodity": 22, "diversification": -37},
    "productivity": {"revenue_per_employee_thousands": 1320, "comp_per_employee_thousands": 380, "comp_ratio": 0.32}
  }
}
```

### `SEMI`
```json
{
  "industry_kpis": {
    "segment_unit_economics": [
      {"segment": "CCG-Desktop", "units_thousands": 12500, "asp_usd": 145, "tam_units_thousands": 28000, "intc_unit_share": 0.446},
      {"segment": "DCAI-Server", "units_thousands": 6200, "asp_usd": 1880, "tam_units_thousands": 11000, "intc_unit_share": 0.564}
    ],
    "competitor_share": [
      {"competitor": "AMD", "category": "DesktopMPU", "unit_share": 0.306, "revenue_share": 0.253}
    ],
    "capex_intensity_pct": 0.245,
    "depreciation_intensity_pct": 0.127
  }
}
```

For other sectors (`BANK_COMMERCIAL`, `INSURANCE_PC`, `INSURANCE_LIFE`, `REIT`, `ENERGY_EP`, `UTILITY`, `RETAIL`, `TELECOM`, `AIRLINE`, `ASSET_MANAGER`, `AUTO`, `MINING`), conventions can be added incrementally as you onboard them. Until then, `industry_kpis: {}` is valid as empty.

---

## 5. House view (single-broker analyst block)

```
HouseView
├── broker, analyst_name, publication_date
├── rating                        Buy | Overweight | Hold | Neutral | Sell | ...
├── target_price                  {value, currency, horizon_months, implied_upside_pct}
├── valuation_methodology_primary DCF | Multiples | SOTP | DDM | EVA | AssetBased | Hybrid
├── dcf                           Full forecast horizon + WACC derivation + EV/equity bridge
├── multiples_valuation           Primary multiple + peer comps
├── sotp[]                        For conglomerates / mixed-business cases
├── thesis_bull / base / bear
├── key_risks[]
└── catalysts[]                   Forward dated events
```

Per-period house forecasts live inside each `Period.house_view_estimates`, not here. The `house_view` block is the *summary*; the per-period array is the *spreadsheet*.

---

## 6. Provenance — what's tracked and what isn't

The schema tracks source attribution at **medium grain**: one `Provenance` record per statement block.

```
BasisFinancials.provenance:
  income_statement     -> Provenance
  balance_sheet        -> Provenance
  cash_flow            -> Provenance
  operating_segments   -> Provenance
  industry_kpis        -> Provenance
```

Not tracked: per-line-item lineage. If you later need cell-level lineage for LLM extraction QA, the schema can be extended with a parallel `provenance_detail{}` map without breaking changes.

---

## 7. Multi-listing & cross-listing handling

A single `ListedCompany` record represents the **economic entity**, not a single listing. The primary listing is canonical; secondaries are tracked in `identifiers.other_listings[]`.

| Case | Modeling |
|---|---|
| Apple (single primary) | One record, AAPL on XNAS, `other_listings[]` empty |
| Tencent (HK + ADR OTC) | One record, 0700 on XHKG, ADR in `other_listings` (TCEHY on OTC) |
| BHP Group (post-DLC unification) | One record, BHP on XASX, secondaries on XLON / XJSE / XNYS-ADR |
| Alibaba (NYSE + HKG dual primary) | One record, BABA on XNYS as primary OR 9988 on XHKG depending on choice; the other is `DualPrimary` in `other_listings` |
| Alphabet GOOG vs GOOGL | One record, two `share_classes[]` entries, both listed |

Currency: `reporting_currency` is the company's books. `trading_currency` may differ per listing. Conversions live outside this schema (in a separate FX rates table).

---

## 8. Restatements and revisions

When prior figures are restated:

```
Period.is_restated = true
Period.restated_from_period_id = "PFE.XNYS__2022Q3A__v1"
```

Convention: append `__v{n}` to `period_id` for revised versions. The original is kept; downstream queries can pick `latest` or `as_of_date`-bounded.

---

## 9. Mapping the three UBS files into this schema

| UBS file artifact | Schema location |
|---|---|
| Pfizer "Income Statement (non-GAAP)" rows 5-49 | `Period.reported.NON_GAAP_ADJUSTED.income_statement` |
| Pfizer "MARGIN ANALYSIS" rows 124-130 | `Period.reported.NON_GAAP_ADJUSTED.ratios` |
| Pfizer "Revs" sheet, drug-by-drug | `Period.reported.NON_GAAP_ADJUSTED.industry_kpis.product_revenue[]` |
| Pfizer "Ex-COVID calcs" | `Period.reported.NON_GAAP_ADJUSTED.industry_kpis.covid_franchise_split` |
| Pfizer "Consensus Total Revenue" | `Period.consensus.revenue` |
| Pfizer "Guidance" sheet | `Period.guidance_in_effect.items[]` |
| Pfizer "Valuation" DCF + WACC + SOTP | `house_view.dcf`, `house_view.dcf.wacc`, `house_view.sotp[]` |
| Pfizer "Debt Schedule" rows 132-180 | `debt_schedule[]` |
| Intel "Revenue Model — CCG Desktop Units / TAM / Share / ASP" | `Period.reported.US_GAAP.operating_segments[].industry_kpis` |
| Intel "Revenue by Geography" | `Period.reported.US_GAAP.geographic_breakdown[]` |
| Intel "Capital Structure" per-bond list | `debt_schedule[]` |
| GS "Business Line Revenues" rows 9-42 | `Period.reported.US_GAAP.industry_kpis.business_line_revenue[]` |
| GS "Tier 1 / Basel III / SLR / TLAC" | `Period.reported.US_GAAP.industry_kpis.capital_ratios` |
| GS "Value at Risk" | `Period.reported.US_GAAP.industry_kpis.var_components` |
| GS "Employees / Revenue per Employee / Comp Ratio" | `Period.reported.US_GAAP.industry_kpis.productivity` |

---

## 10. What's intentionally NOT in this schema

- Per-bond debt schedule details below `instrument_name + principal + coupon + maturity` (e.g. exact covenants, indenture references)
- Earnings call transcripts (full text)
- Short interest, options-implied vol
- Corporate actions history (M&A, spinoffs, splits) — would be a separate `corporate_events[]` table
- Multiple broker views simultaneously — only one `house_view`
- Cell-level provenance — medium grain only
- Strict typed industry KPIs — flexible JSON only

These are deliberate scope cuts based on the design choices made. Any of them can be added in a v1.1 with no breaking changes; just add new optional top-level properties.

---

## 11. Validation

```bash
pip install jsonschema
python -c "
import json
from jsonschema import Draft202012Validator
schema = json.load(open('listed_company.schema.json'))
record = json.load(open('pfizer_sample.json'))
Draft202012Validator(schema).validate(record)
print('OK')
"
```
