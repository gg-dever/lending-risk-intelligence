# Stage 03: Cohort and Segmentation Analysis

**Phase:** 2 of 3 (Clean → Segment → Exposure)
**Purpose:** Segment cleaned data by business-relevant dimensions, calculate default rates, answer specific business questions

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Cleaned data | `../02-clean/output/lending_risk_cleaned.csv` | Full file | Analysis-ready dataset from Phase 1 |
| Business rules | `references/business-rules.md` | "Segmentation Priority Order" | Defines which segments to calculate and in what order |
| Segmentation guide | `references/segmentation-guide.md` | Full file | Maps each segment to business question, expected patterns, audit checks |
| Pipeline script | `pipeline/segment.py` | Full file | Execution logic (instructional template) |

**Do not load:**
- Raw data (use cleaned version only)
- Exposure outputs (Phase 3, downstream from this stage)
- Dashboard files (visualization layer, not analytical input)

---

## Process

1. **Load cleaned data**
   - Read `../02-clean/output/lending_risk_cleaned.csv`
   - Verify `is_default` and `crisis_period` columns exist
   - Print: record count, baseline default rate

2. **Segment by loan grade (A–G)**
   - Reference `segmentation-guide.md` Section 1
   - Business question: How does default risk increase with credit tier?
   - Group by `grade`, calculate:
     - `count` (number of loans)
     - `default_rate` (mean of is_default)
     - `avg_loan_amount_usd` (mean of loan_amnt)
     - `avg_int_rate` (mean of int_rate)
     - `total_portfolio_value_usd` (sum of loan_amnt)
   - Split by `crisis_period` (show normal vs. crisis default rates)
   - **Audit:** Default rate should increase monotonically A → G

3. **Segment by loan term (36 vs 60 months)**
   - Reference `segmentation-guide.md` Section 2
   - Business question: Do longer loans default more?
   - Group by `term`, calculate same metrics as grade
   - **Audit:** 60-month typically has higher default rate than 36-month

4. **Segment by loan purpose**
   - Reference `segmentation-guide.md` Section 3
   - Business question: Which loan uses are riskiest?
   - Group by `purpose`, calculate same metrics
   - Rank by `default_rate` descending
   - **Audit:** `debt_consolidation` should be largest volume (50–60% of loans)

5. **Segment by home ownership**
   - Reference `segmentation-guide.md` Section 4
   - Business question: Does home ownership reduce default?
   - Group by `home_ownership`, calculate same metrics
   - **Audit:** OWN < MORTGAGE < RENT expected pattern

6. **Segment by employment length**
   - Reference `segmentation-guide.md` Section 5
   - Business question: Do newer employees default more?
   - Parse `emp_length` (e.g., "2 years", "<1 year", "10+ years")
   - Bucket into: `<1 yr`, `1-3 yr`, `3-5 yr`, `5-10 yr`, `10+ yr`
   - Group by bucket, calculate same metrics
   - **Audit:** Default rate should decrease with longer tenure

7. **Crisis period comparison**
   - Reference `segmentation-guide.md` Section 6
   - Business question: How much do 2008–2010 cohorts distort baseline?
   - For each segmentation above, split by `crisis_period`
   - Calculate normal-period default rate separately
   - **Audit:** Crisis default rates should be 2–3× normal

8. **Cross-segment analysis (optional)**
   - Identify high-risk clusters (e.g., Grade F + 60-month + small_business)
   - Identify low-risk clusters (e.g., Grade A + debt_consolidation + homeowner)
   - Calculate default rates for top 5 highest-risk and top 5 lowest-risk combinations
   - **Audit:** Highest-risk cluster should be >20% default rate, lowest-risk <3%

9. **Output master segment summary**
   - Combine all segmentations into single CSV
   - Columns: `segment_type`, `segment_value`, `count`, `default_rate`, `avg_loan_amount_usd`, `total_portfolio_value_usd`, `crisis_period`
   - Save to `stages/03-segment/output/segment_summary.csv`

10. **Output individual drill-down JSONs**
    - One JSON per segmentation type:
      - `grade_breakdown.json`
      - `term_breakdown.json`
      - `purpose_breakdown.json`
      - `home_ownership_breakdown.json`
      - `employment_length_breakdown.json`
    - Each JSON structure (see `segmentation-guide.md` "Output Format by Segmentation"):
      - `metadata` block (generated timestamp, segment_type, total_segments)
      - `segments` array (value, count, default_rate_pct, avg_loan_amount_usd, total_portfolio_value_usd)
      - Crisis vs. normal split within each segment
    - Save all to `stages/03-segment/output/`

---

## Outputs

| Artifact | Location | Format | Purpose |
|----------|----------|--------|---------|
| Master segment summary | `stages/03-segment/output/segment_summary.csv` | CSV | All segmentations in one table (for exposure calculations) |
| Grade breakdown | `stages/03-segment/output/grade_breakdown.json` | JSON | Dashboard drill-down for grade segmentation |
| Term breakdown | `stages/03-segment/output/term_breakdown.json` | JSON | Dashboard drill-down for term segmentation |
| Purpose breakdown | `stages/03-segment/output/purpose_breakdown.json` | JSON | Dashboard drill-down for purpose segmentation |
| Home ownership breakdown | `stages/03-segment/output/home_ownership_breakdown.json` | JSON | Dashboard drill-down for home ownership segmentation |
| Employment length breakdown | `stages/03-segment/output/employment_length_breakdown.json` | JSON | Dashboard drill-down for employment segmentation |

**Downstream usage:**
- `segment_summary.csv` → Input for `stages/04-exposure/CONTEXT.md`
- All JSON files → Input for `stages/06-dashboard/CONTEXT.md`

---

## Audit

Run these checks before writing to `output/`:

1. **Grade monotonicity**
   - Default rate must increase (or stay flat) from A → G
   - If Grade B has higher default rate than Grade C, investigate labeling or data quality

2. **Term pattern**
   - 60-month default rate should be ≥ 36-month default rate
   - If reversed, investigate (unusual but possible if portfolio skews low-grade to 36-month)

3. **Purpose volume**
   - `debt_consolidation` should be largest volume segment (typically 50–60% of loans)
   - If not, verify `purpose` column parsing and standardization

4. **Crisis period elevation**
   - Crisis-period default rates should be 1.5–3× normal-period rates
   - If crisis rates are NOT elevated, check `crisis_period` flag logic in Phase 1

5. **Segment coverage**
   - Sum of all segment counts (within a segmentation type) must equal total record count
   - If not, some loans are missing from segmentation (investigate groupby logic)

6. **No null segments**
   - No segment should have `segment_value` = null or NaN
   - If present, handle missing values in Phase 1 or exclude from segmentation with documentation

If any audit fails, do NOT proceed to outputs. Return to Process and fix the issue.

---

## Notes

- **Segment priority:** Follow `business-rules.md` "Segmentation Priority Order" when presenting results. Grade comes first (primary risk tier), then term, purpose, etc.

- **Crisis labeling:** Every output artifact must clearly label crisis vs. normal period figures. Do NOT blend them into a single default rate without context.

- **Cross-segment depth:** Cross-segment analysis (Process step 8) is optional but valuable for identifying risk clusters. If dataset is large enough (>100k records), include it. If too small, skip to avoid overfitting noise.

- **JSON structure consistency:** All drill-down JSONs follow the same structure (see `segmentation-guide.md`). This allows dashboard code to render them with a single template.
