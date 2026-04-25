# Stage 04: Dollar Exposure Modeling

**Phase:** 3 of 3 (Clean → Segment → Exposure)  
**Purpose:** Translate default rates into dollar risk figures; calculate expected loss at portfolio and segment level

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Cleaned data | `../02-clean/output/lending_risk_cleaned.csv` | Full file | Loan-level data for portfolio aggregation |
| Segment summary | `../03-segment/output/segment_summary.csv` | Full file | Default rates and portfolio values by segment |
| Business rules | `references/business-rules.md` | "Loss Modeling Assumptions" | Recovery rate, loss given default formula |
| Pipeline script | `pipeline/exposure.py` | Full file | Execution logic (instructional template) |

**Do not load:**
- Raw data (use cleaned version only)
- Dashboard files (visualization layer, not analytical input)
- Individual drill-down JSONs (use master `segment_summary.csv` instead)

---

## Process

1. **Load data**
   - Read `../02-clean/output/lending_risk_cleaned.csv`
   - Read `../03-segment/output/segment_summary.csv`
   - Verify columns: `loan_amnt`, `is_default`, `grade`, `term`, `purpose`, etc.
   - Print: total loans, total portfolio value

2. **Define loss assumptions**
   - Reference `business-rules.md` "Loss Modeling Assumptions"
   - Set constants:
     - `RECOVERY_RATE = 0.70` (70% of defaulted principal recovered)
     - `LOSS_GIVEN_DEFAULT = 0.30` (30% actual loss)
   - Print: loss assumption, rationale
   - Document assumptions in output JSON for traceability

3. **Calculate portfolio-level exposure**
   - Formula: `Expected Loss = Total Portfolio Value × Default Rate × Loss Given Default`
   - Steps:
     - `portfolio_value = df['loan_amnt'].sum()`
     - `portfolio_default_rate = df['is_default'].mean()`
     - `portfolio_expected_loss = portfolio_value × portfolio_default_rate × LOSS_GIVEN_DEFAULT`
     - `portfolio_loss_rate = portfolio_expected_loss / portfolio_value`
   - Print headline figures:
     - Total Portfolio Value
     - Portfolio Default Rate
     - Expected Loss (dollars at risk)
     - Loss Rate (expected loss as % of portfolio)

4. **Calculate segment-level exposure by grade**
   - For each grade (A–G):
     - `segment_value = sum(loan_amnt)` for loans in grade
     - `segment_default_rate = mean(is_default)` for loans in grade
     - `segment_expected_loss = segment_value × segment_default_rate × LOSS_GIVEN_DEFAULT`
     - `segment_loss_rate = segment_expected_loss / segment_value`
     - `pct_of_portfolio_exposure = segment_expected_loss / portfolio_expected_loss`
   - Rank segments by `segment_expected_loss` descending
   - Print: top 5 segments by dollar exposure

5. **Calculate segment-level exposure by term**
   - Repeat step 4 logic for `term` (36 vs 60 months)
   - Compare exposure between terms
   - Print: term comparison (36-month vs. 60-month exposure)

6. **Calculate segment-level exposure by purpose**
   - Repeat step 4 logic for `purpose`
   - Identify highest-exposure purposes (both dollar amount AND default rate)
   - Print: top 3 purposes by exposure

7. **Calculate segment-level exposure by home ownership**
   - Repeat step 4 logic for `home_ownership`
   - Compare homeowner vs. renter exposure
   - Print: ownership comparison

8. **Calculate segment-level exposure by employment length**
   - Repeat step 4 logic for employment length buckets
   - Identify if short-tenure employees carry disproportionate exposure
   - Print: tenure-based exposure distribution

9. **Identify at-risk cohorts**
   - Filter to currently-performing loans (`is_default = 0`)
   - Group by high-risk segments (e.g., Grade D+, 60-month, purpose=small_business)
   - Calculate dollar value of at-risk performing loans
   - Print: top 5 at-risk cohorts (performing loans in high-risk segments)

10. **Output portfolio headline**
    - Create JSON with:
      - `portfolio_value_usd`: total portfolio value
      - `portfolio_default_rate_pct`: default rate as percentage
      - `expected_loss_usd`: total expected loss
      - `loss_rate_pct`: loss rate as percentage
      - `metadata`: generated timestamp, source files, assumptions (recovery rate, LGD)
    - Save to `stages/04-exposure/output/portfolio_headline.json`

11. **Output segment exposure summary**
    - Combine all segment-level exposure calculations into single CSV
    - Columns: `segment_type`, `segment_value`, `segment_value_usd`, `segment_default_rate`, `segment_expected_loss_usd`, `segment_loss_rate_pct`, `pct_of_portfolio_exposure`
    - Save to `stages/04-exposure/output/exposure_summary.csv`

12. **Output individual exposure JSONs**
    - One JSON per segmentation type (grade, term, purpose, etc.)
    - Structure:
      - `metadata` block (generated, segment_type, total_segments, assumptions)
      - `segments` array (value, portfolio_value_usd, default_rate_pct, expected_loss_usd, loss_rate_pct, pct_of_portfolio_exposure)
    - Save to `stages/04-exposure/output/{segment_type}_exposure.json`

---

## Outputs

| Artifact | Location | Format | Purpose |
|----------|----------|--------|---------|
| Portfolio headline | `stages/04-exposure/output/portfolio_headline.json` | JSON | Top-line figures for dashboard index.html |
| Exposure summary | `stages/04-exposure/output/exposure_summary.csv` | CSV | All segments' dollar exposure in one table |
| Grade exposure | `stages/04-exposure/output/grade_exposure.json` | JSON | Dashboard drill-down for grade exposure |
| Term exposure | `stages/04-exposure/output/term_exposure.json` | JSON | Dashboard drill-down for term exposure |
| Purpose exposure | `stages/04-exposure/output/purpose_exposure.json` | JSON | Dashboard drill-down for purpose exposure |
| Home ownership exposure | `stages/04-exposure/output/home_ownership_exposure.json` | JSON | Dashboard drill-down for ownership exposure |
| Employment exposure | `stages/04-exposure/output/employment_length_exposure.json` | JSON | Dashboard drill-down for employment exposure |

**Downstream usage:**
- `portfolio_headline.json` → Dashboard `index.html` (headline metrics)
- `exposure_summary.csv` → Dashboard `exposure.html` (full exposure table)
- All JSON files → Dashboard drill-down charts and tables

---

## Audit

Run these checks before writing to `output/`:

1. **Portfolio-level math**
   - `portfolio_expected_loss < portfolio_value` (loss cannot exceed total value)
   - `portfolio_loss_rate` should be 2–8% for typical consumer lending (if outside, investigate)

2. **Segment coverage**
   - Sum of all segment exposures (within a segmentation type) should equal `portfolio_expected_loss`
   - If not, some loans are missing from segmentation (check groupby logic)

3. **Grade exposure monotonicity**
   - Higher grades (D, E, F, G) should have higher `segment_loss_rate` than lower grades (A, B, C)
   - If reversed, investigate default rate or dollar exposure calculations

4. **At-risk cohorts reasonableness**
   - At-risk performing loan value should be 60–80% of total portfolio (most loans are performing)
   - If <50%, investigate default rate (too high?) or cohort filtering logic

5. **Percentage allocations**
   - `pct_of_portfolio_exposure` across all segments (within a segmentation type) should sum to 100%
   - If not, normalization error or missing segment

6. **Assumption traceability**
   - Every output JSON must include `metadata.assumptions` block with:
     - `recovery_rate`: 0.70
     - `loss_given_default`: 0.30
     - `source`: "Industry historical average (2000–2020)"
   - If assumptions differ from defaults, document rationale

If any audit fails, do NOT proceed to outputs. Return to Process and fix the issue.

---

## Notes

- **Recovery rate sensitivity:** Default 70% recovery is industry average. If client has actual recovery data, override here and document in `portfolio_headline.json` metadata.

- **Crisis period exposure:** Consider calculating separate expected loss for crisis vs. normal periods. Crisis-era losses are historical (sunk cost), while normal-period losses inform forward-looking risk.

- **At-risk cohort use case:** CFO uses this to set reserves. Risk officer uses it to prioritize monitoring. Underwriting team uses it to adjust origination criteria. Make it actionable by sorting by dollar exposure, not just default rate.

- **Dashboard handoff:** All JSON outputs follow consistent structure (metadata + segments array). Dashboard JavaScript can render them with a single template, reducing maintenance burden.
