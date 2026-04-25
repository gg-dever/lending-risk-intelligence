# Stage 02: Data Cleaning and Outcome Engineering

**Phase:** 1 of 3 (Clean → Segment → Exposure)  
**Purpose:** Transform raw lending data into analysis-ready dataset with binary default outcome

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Raw data | `data/raw/lending_club.csv` | Full file | Source dataset (890k loans, 2007–2015) |
| Business rules | `references/business-rules.md` | "Default Outcome Definition", "Crisis Period Handling", "Required Columns", "Noise Columns" | Canonical definitions for terminal states, crisis flagging, column decisions |
| Pipeline script | `pipeline/clean.py` | Full file | Execution logic (instructional template with TODOs) |

**Do not load:**
- Other stages' outputs (none exist yet; this is entry point)
- Dashboard files (visualization layer, not data layer)
- Segment or exposure references (not relevant to cleaning phase)

---

## Process

1. **Verify raw data exists**
   - Check `data/raw/lending_club.csv` exists
   - Confirm record count (~890k expected)
   - If missing, prompt user to run `setup` trigger or place file manually

2. **Load and inspect**
   - Read CSV with pandas
   - Print: record count, column count, date range (issue_d)
   - Identify loan_status values (exact strings vary by dataset version)

3. **Engineer binary default outcome**
   - Filter to terminal states only: `Fully Paid`, `Charged Off` (match exact strings in data)
   - Create `is_default` column: 1 if `Charged Off` or `Default`, else 0
   - Calculate and print baseline default rate
   - Print default count vs. non-default count

4. **Flag crisis period**
   - Parse `issue_d` to datetime
   - Create `crisis_period` binary column: 1 if 2008 ≤ year ≤ 2010, else 0
   - Print crisis-period loan count vs. normal-period count
   - DO NOT exclude crisis loans; flag them for segmentation

5. **Drop high-null columns**
   - Calculate null rate per column: `null_count / total_rows`
   - Identify columns with >50% null
   - Review sparse columns for segmentation relevance (e.g., co-applicant fields)
   - Drop columns with >50% null unless explicitly justified
   - Print: columns dropped, null rates, rationale

6. **Drop noise columns**
   - Reference `business-rules.md` "Noise Columns" section
   - Drop: `emp_title`, `url`, `id`, `member_id`, `desc` (if present)
   - Print: noise columns dropped

7. **Handle required column nulls**
   - Reference `business-rules.md` "Required Columns" section
   - Identify rows with nulls in: `loan_amnt`, `int_rate`, `term`, `grade`, `purpose`, `home_ownership`
   - Drop rows with any required column null
   - Print: rows dropped, rows retained

8. **Standardize formats**
   - Parse `int_rate` (remove `%`, convert to decimal: `12.5%` → `0.125`)
   - Parse other percentage columns if present (e.g., `revol_util`)
   - Strip leading/trailing spaces from categorical columns
   - Print: transformations applied

9. **Output cleaned data**
   - Save to `stages/02-clean/output/lending_risk_cleaned.csv`
   - Print: final shape (rows, columns), output path

10. **Generate data quality report**
    - Create JSON with:
      - Metadata: source_records, final_records, generated timestamp
      - Outcome engineering: default definition, default rate, counts
      - Filtering decisions: terminal states, crisis period handling
      - Null handling: threshold, columns dropped, exceptions kept
      - Noise removal: columns dropped, rationale per column
      - Required columns: list, rows dropped for nulls
    - Save to `stages/02-clean/output/data_quality_report.json`
    - Print: report path

---

## Outputs

| Artifact | Location | Format | Purpose |
|----------|----------|--------|---------|
| Cleaned dataset | `stages/02-clean/output/lending_risk_cleaned.csv` | CSV (no index, UTF-8) | Analysis-ready data for Phase 2 segmentation |
| Data quality report | `stages/02-clean/output/data_quality_report.json` | JSON (indent=2) | Audit trail: every decision, count, rationale |

**Downstream usage:**
- `lending_risk_cleaned.csv` → Input for `stages/03-segment/CONTEXT.md`
- `data_quality_report.json` → Referenced in final report appendix

---

## Audit

Run these checks before writing to `output/`:

1. **Default outcome validity**
   - `is_default` column exists and is binary (0 or 1 only)
   - Default rate is between 5% and 25% (typical range for Lending Club; if outside, investigate)
   - Default count + non-default count = total rows

2. **Crisis period flag validity**
   - `crisis_period` column exists and is binary
   - Crisis-period loans are 10–30% of total (if outside, check date parsing)

3. **No required-column nulls**
   - Zero nulls in: `loan_amnt`, `int_rate`, `term`, `grade`, `purpose`, `home_ownership`
   - If any nulls remain, fail audit and re-run Process step 7

4. **Column count reduction**
   - Final column count should be 30–50 (started with ~75)
   - If >50 columns remain, review null threshold and noise column logic

5. **No duplicate rows**
   - Check for duplicate loan IDs (if `id` column still present)
   - If duplicates found, deduplicate or investigate source data issue

If any audit fails, do NOT proceed to outputs. Fix the issue and re-run from Process step 1.

---

## Notes

- **TODO preservation:** `pipeline/clean.py` contains instructional TODOs. Do NOT remove them during execution. They map to domain decisions (e.g., "which status values to exclude") that vary by dataset version and client requirements.

- **Crisis period rationale:** 2008–2010 default rates are 2–3× normal due to financial crisis. Excluding them loses valuable data; flagging them preserves both transparency and analytical value.

- **Null threshold justification:** 50% is the standard cutoff. Columns with >50% null rarely have enough signal to anchor a business decision. Exceptions exist (e.g., co-applicant fields), but must be explicitly justified in the data quality report.
