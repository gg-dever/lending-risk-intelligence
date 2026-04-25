# Business Rules — Lending Risk Intelligence

**Canonical source for domain logic.** All stages reference these rules.

---

## Default Outcome Definition

**Default** = Loan status is `Charged Off` OR `Default`  
**Non-Default** = Loan status is `Fully Paid`

**Excluded States** (unresolved, do not include in terminal outcome analysis):
- Current
- Late (16-30 days)
- Late (31-120 days)
- In Grace Period
- Grace Period

**Rationale:** Including unresolved loans adds noise; they have not yet reached terminal state. Default rates calculated from terminal loans only.

---

## Crisis Period Handling

**Crisis Period:** 2008–2010 (financial crisis years)

**Treatment:**
1. Do NOT exclude crisis-era loans from the dataset
2. Flag them with binary `crisis_period` column (1 = crisis, 0 = normal)
3. Segment and visualize crisis cohorts separately in dashboard
4. Label all crisis-era figures explicitly in reports and charts
5. Calculate baseline default rates from normal-period loans when inferring portfolio norms

**Rationale:** Crisis-era default rates (often 2–3× normal) do not reflect typical lending conditions. Excluding them loses valuable data; flagging them preserves transparency while preventing distortion of baseline metrics.

---

## Loss Modeling Assumptions

### Expected Loss Formula
```
Expected Loss = Loan Amount × Default Rate × Loss Given Default
```

### Recovery Rate
**Default assumption:** 70% recovery on defaulted loans  
**Loss Given Default (LGD):** 30% (1 - recovery_rate)

**Source:** Industry historical average for unsecured consumer credit (2000–2020). Adjust if client has proprietary recovery data.

### When to Override
- Client has actual recovery performance data
- Portfolio includes secured loans (auto, mortgage) with higher recovery
- Collection practices differ materially from industry norm

Document any override in `stages/04-exposure/output/exposure_assumptions.json`

---

## Required Columns

The following columns are non-negotiable for the analysis. Drop rows with nulls in any of these:

| Column | Purpose |
|--------|---------|
| `loan_amnt` | Portfolio value, exposure calculation |
| `int_rate` | Pricing analysis, risk-return relationship |
| `term` | Duration segmentation (36 vs 60 months) |
| `grade` | Primary credit risk tier |
| `purpose` | Use-case segmentation, marketing insights |
| `home_ownership` | Collateral proxy, underwriting criteria validation |

**Exceptions:** If a column is missing for <1% of records, impute if domain-appropriate (e.g., median int_rate for same grade). Document all imputation decisions in `data/processed/data_quality_report.json`.

---

## Noise Columns

These columns are excluded from analysis (no signal for default prediction or business segmentation):

- `emp_title` — 150k+ unique values; not actionable
- `url` — Administrative field
- `id`, `member_id` — Identifiers only, no predictive value
- `desc` — Freeform text, requires NLP processing outside scope

Add to this list during Phase 1 (clean.py) if you identify other noise columns.

---

## Column Null Threshold

**Rule:** Drop columns with >50% null values unless explicitly justified.

**Exceptions (must document):**
- Sparse column maps to a specific segment (e.g., co-applicant fields only relevant for multi-borrower loans)
- Null itself is informative (e.g., missing employment length may signal self-employment or gig work)

Document all exceptions in `data/processed/data_quality_report.json` with rationale.

---

## Segmentation Priority Order

When building dashboard and reports, present segments in this priority:

1. **Grade** (A–G) — Primary credit risk tier, drives all downstream decisions
2. **Term** (36 vs 60 months) — Duration risk, origination strategy
3. **Purpose** (debt_consolidation, credit_card, home_improvement, etc.) — Marketing and risk appetite
4. **Home Ownership** (OWN, RENT, MORTGAGE) — Collateral proxy
5. **Employment Length** (<1 yr, 1-3 yr, 3-5 yr, 5-10 yr, 10+ yr) — Income stability proxy

**Cross-Segments:** Identify highest-risk combinations (e.g., Grade F + 60-month + debt_consolidation) for dashboard highlighting.

---

## Percentage Formatting

All percentages in outputs:
- Stored as decimals (0.15 = 15%)
- Displayed with 2 decimal places unless <0.01% (then 3)
- Dashboard: `15.2%`
- JSON exports: store as decimal, include `_pct` suffix in field name for clarity

---

## Dollar Formatting

All currency figures:
- No decimals (round to nearest dollar)
- Comma separators: `$123,456,789`
- Dashboard: use K/M/B suffixes for large figures (e.g., `$45.3M`)
- JSON exports: store as integer, field name includes `_usd` suffix

---

## Source Traceability

Every calculated figure must trace back to:
1. Source data file (`data/raw/lending_club.csv`)
2. Transformation logic (which phase, which script)
3. Business rule applied (this file, specific section)

Document chain of custody in:
- `data/processed/data_quality_report.json` (Phase 1)
- `data/processed/segment_summary.csv` (Phase 2)
- `data/processed/exposure_summary.csv` (Phase 3)
