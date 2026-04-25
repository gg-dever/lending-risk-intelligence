# Segmentation Guide — Business Question Mapping

**Every segment answers a specific business question.** This guide maps each segmentation variable to the decision it informs.

---

## 1. Loan Grade (A–G)

**Business Question:** How does default risk increase with credit tier?

**Decision Impact:**
- Pricing strategy (interest rate by grade)
- Volume allocation (how much capital to deploy at each tier)
- Reserve requirements (higher-grade loans need less capital buffer)

**Segmentation:**
- Grades: A, B, C, D, E, F, G
- Calculate: count, default_rate, avg_loan_amount, avg_int_rate, total_portfolio_value
- Expected pattern: Monotonic increase in default rate from A (lowest) to G (highest)

**Dashboard Use:**
- Show grade distribution as bar chart
- Highlight grades with >10% default rate
- Compare crisis vs. normal period by grade

**Audit Check:**
- Default rate should increase monotonically A → G
- If not, investigate data quality or label errors

---

## 2. Loan Term (36 vs 60 months)

**Business Question:** Do longer loans default more than shorter loans?

**Decision Impact:**
- Origination strategy (push 36-month for lower risk, 60-month for higher yield)
- Portfolio duration risk (60-month locks capital longer)
- Pricing differentials (justify rate premium for 60-month)

**Segmentation:**
- Terms: 36 months, 60 months
- Calculate: count, default_rate, avg_loan_amount, total_exposure
- Expected pattern: 60-month typically has higher default rate (more time for adverse events)

**Dashboard Use:**
- Side-by-side comparison table
- Default rate % difference
- Dollar exposure by term

**Audit Check:**
- If 36-month has higher default rate than 60-month, investigate (unusual pattern)

---

## 3. Loan Purpose

**Business Question:** Which loan use cases have highest default rates?

**Decision Impact:**
- Marketing spend allocation (avoid high-risk purposes, double down on low-risk)
- Risk appetite by purpose (e.g., avoid "small business" if default rate >15%)
- Product design (offer discounts for debt consolidation if it outperforms)

**Segmentation:**
- Purposes: debt_consolidation, credit_card, home_improvement, major_purchase, small_business, medical, car, moving, vacation, house, wedding, renewable_energy, educational, other
- Calculate: count, default_rate, avg_loan_amount, total_portfolio_value
- Rank by: default_rate descending (show riskiest first)

**Dashboard Use:**
- Drill-down table sorted by default rate
- Highlight: purposes with >10% default rate AND >5% of portfolio volume
- Show: debt_consolidation separately (usually largest volume)

**Audit Check:**
- debt_consolidation should be largest volume (historically 50–60% of Lending Club loans)
- small_business typically highest default rate (often 12–18%)

---

## 4. Home Ownership

**Business Question:** Does home ownership (collateral proxy) reduce default?

**Decision Impact:**
- Underwriting criteria (require home ownership for higher-risk grades?)
- Pricing adjustments (discount for homeowners?)
- Marketing targeting (prioritize homeowners for acquisition)

**Segmentation:**
- Statuses: OWN, RENT, MORTGAGE, OTHER, NONE
- Calculate: count, default_rate, avg_loan_amount
- Expected pattern: OWN < MORTGAGE < RENT < OTHER

**Dashboard Use:**
- Bar chart: default rate by ownership status
- Highlight: homeowners (OWN + MORTGAGE) vs. renters default rate delta

**Audit Check:**
- If renters have lower default rate than homeowners, investigate (counterintuitive)

---

## 5. Employment Length

**Business Question:** Do newer employees default more than established ones?

**Decision Impact:**
- Income stability validation (flag <1 year employment as higher risk)
- Underwriting criteria (require longer employment for higher loan amounts?)
- Risk pricing (charge premium for short tenure)

**Segmentation:**
- Buckets: <1 year, 1-3 years, 3-5 years, 5-10 years, 10+ years
- Calculate: count, default_rate, avg_loan_amount
- Expected pattern: Default rate decreases with longer employment (stability proxy)

**Dashboard Use:**
- Line chart: default rate vs. employment tenure
- Highlight: <1 year bucket if default rate >12%

**Audit Check:**
- If 10+ years has higher default than <1 year, investigate (counterintuitive unless layoffs in dataset period)

---

## 6. Crisis Period

**Business Question:** How much do 2008–2010 cohorts distort portfolio baseline?

**Decision Impact:**
- Baseline default rate calculation (exclude crisis period for normal-time baseline)
- Historical reporting (label crisis-era figures separately)
- Reserve adequacy (don't over-reserve based on crisis-era rates)

**Segmentation:**
- Periods: Crisis (2008–2010), Normal (all other years)
- Calculate: default_rate by period, by grade within period
- Expected pattern: Crisis default rates 2–3× normal

**Dashboard Use:**
- Split every segmentation into crisis vs. normal
- Show both, label clearly
- Baseline metrics use normal period only

**Audit Check:**
- If crisis period does NOT have elevated default rates, check flag logic

---

## Cross-Segment Analysis

**Business Question:** Which combinations of factors produce highest risk?

**Decision Impact:**
- Underwriting rules (auto-decline certain combinations?)
- Pricing tiers (premium for multi-risk factors?)
- Portfolio limits (cap exposure to high-risk clusters)

**Example Combinations to Calculate:**
- Grade F + 60-month → Expected: very high default rate
- Grade D + small_business + <1 year employment → Risk cluster
- Grade A + debt_consolidation + homeowner → Low-risk cluster

**Dashboard Use:**
- "Risk Clusters" section
- Show top 5 highest-risk combinations
- Show top 5 lowest-risk combinations

**Audit Check:**
- Highest-risk cluster should have default rate >20%
- Lowest-risk cluster should have default rate <3%

---

## Output Format by Segmentation

### segment_summary.csv
Master table with all segments:
```
segment_type, segment_value, count, default_rate, avg_loan_amount, total_portfolio_value_usd, crisis_period
grade, A, 150000, 0.045, 12500, 1875000000, 0
grade, B, 200000, 0.082, 13000, 2600000000, 0
...
term, 36, 450000, 0.075, 11000, 4950000000, 0
term, 60, 200000, 0.135, 18000, 3600000000, 0
...
```

### Individual Drill-Down JSONs
One file per segmentation type:
- `grade_breakdown.json`
- `term_breakdown.json`
- `purpose_breakdown.json`
- `home_ownership_breakdown.json`
- `employment_length_breakdown.json`

Each contains:
```json
{
  "metadata": {
    "segment_type": "grade",
    "total_segments": 7,
    "generated": "2026-04-18T12:00:00Z"
  },
  "segments": [
    {
      "value": "A",
      "count": 150000,
      "default_rate_pct": 4.5,
      "avg_loan_amount_usd": 12500,
      "total_portfolio_value_usd": 1875000000,
      "crisis_period": {
        "count": 30000,
        "default_rate_pct": 8.2
      },
      "normal_period": {
        "count": 120000,
        "default_rate_pct": 3.8
      }
    }
  ]
}
```

---

## Usage in Dashboard

**index.html:**
- Load `grade_breakdown.json`
- Show headline default rate by grade (chart)
- Show portfolio composition by grade (table)

**segments.html:**
- Load all drill-down JSONs
- Render one section per segmentation type
- Each section: table with count, default_rate, avg_loan_amount
- Crisis vs. normal period toggle

**exposure.html:**
- Load `exposure_summary.csv` (from Phase 3)
- Show dollar exposure by segment
- Highlight segments with >$100M exposure AND >10% default rate

---

## Maintenance

When adding new segmentations:
1. Add business question to this guide
2. Add decision impact
3. Define expected pattern (for audit checks)
4. Update `pipeline/segment.py` with new calculation
5. Update dashboard to render new segment
