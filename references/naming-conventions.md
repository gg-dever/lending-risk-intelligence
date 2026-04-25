# Naming Conventions — File, Column, and Output Standards

**Consistency reduces cognitive load.** Follow these conventions across all stages.

---

## File Naming

### Data Files
```
{descriptor}_{detail}.{ext}

Examples:
✓ lending_risk_cleaned.csv
✓ segment_summary.csv
✓ grade_breakdown.json
✓ exposure_summary.csv
✓ portfolio_headline.json

✗ cleaned_data.csv (ambiguous)
✗ segments.csv (what kind of summary?)
✗ grade.json (breakdown? summary? raw?)
```

**Rules:**
- Lowercase, underscore-separated
- Descriptor comes first (what kind of data: segment, exposure, grade, term, etc.)
- Detail comes second (what aspect: summary, breakdown, headline, etc.)
- No dates in filenames (use `generated` timestamp in JSON metadata)

### Python Scripts
```
{phase}.py

Examples:
✓ clean.py
✓ segment.py
✓ exposure.py

✗ phase_1_cleaning.py (redundant)
✗ run_segmentation.py (verbose)
```

**Rules:**
- One word, verb form
- Maps directly to phase name
- No version numbers (use git)

### HTML Files
```
{view}.html

Examples:
✓ index.html (executive summary)
✓ segments.html (drill-down by segment)
✓ exposure.html (dollar risk view)

✗ dashboard.html (ambiguous; which view?)
✗ summary.html (use index.html for main page)
```

### Reports
```
{audience}_{type}.{ext}

Examples:
✓ executive_summary.pdf
✓ findings.pdf

✗ report.pdf (ambiguous)
✗ lending_risk_report_2026-04-18.pdf (no dates in filename; use metadata)
```

---

## Column Naming

### Python/CSV Columns
```
{descriptor}_{unit}

Examples:
✓ loan_amnt (amount in dollars)
✓ int_rate (interest rate as decimal, 0.15 = 15%)
✓ is_default (binary, 1 = default)
✓ default_rate_pct (percentage, stored as decimal)
✓ total_portfolio_value_usd (dollar amount)
✓ crisis_period (binary, 1 = 2008-2010)

✗ amount (ambiguous; loan? payment? exposure?)
✗ rate (which rate? interest? default?)
✗ default (noun or binary flag?)
```

**Rules:**
- Lowercase, underscore-separated
- Include unit suffix when ambiguous:
  - `_pct` for percentages (stored as decimal, 0.15 = 15%)
  - `_usd` for dollar amounts
  - `_count` for counts
  - `_rate` for rates (when not percentage)
- Binary flags use `is_` prefix: `is_default`, `is_terminal`
- Date columns use `_date` or `_d` suffix: `issue_date`, `issue_d`

### JSON Field Naming
```
{descriptor}_{unit}

Examples:
✓ "default_rate_pct": 12.5
✓ "total_portfolio_value_usd": 8500000000
✓ "count": 150000
✓ "generated": "2026-04-18T12:00:00Z"

✗ "defaultRate": 12.5 (use snake_case, not camelCase)
✗ "total_value": 8500000000 (ambiguous; include _usd)
```

**Rules:**
- Match Python/CSV conventions (snake_case, include units)
- ISO 8601 for timestamps: `YYYY-MM-DDTHH:MM:SSZ`
- Metadata block always includes `generated` timestamp

---

## Directory Structure

### Stage Folders
```
stages/{NN-name}/
├── CONTEXT.md       ← Stage contract (Inputs/Process/Outputs)
├── input/           ← References to upstream outputs (symlinks or relative paths)
├── output/          ← This stage's artifacts (CSV, JSON, reports)
└── audit.md         ← Optional: audit checks to run before writing to output/

Examples:
✓ stages/02-clean/output/lending_risk_cleaned.csv
✓ stages/03-segment/output/segment_summary.csv
✓ stages/04-exposure/output/exposure_summary.csv

✗ stages/clean/output/data.csv (use NN- prefix, explicit name)
✗ stages/02-clean/lending_risk_cleaned.csv (output goes in output/ subfolder)
```

**Rules:**
- Two-digit prefix for ordering: `01-`, `02-`, `03-`
- `input/` folder may be empty (stages often reference `../NN-prev-stage/output/` directly)
- `output/` folder is the canonical location for stage artifacts
- No intermediate files outside `output/` (everything is either input or output)

---

## Output File Standards

### CSV Files
- Header row required
- No index column (set `index=False` in pandas)
- UTF-8 encoding
- Unix line endings (`\n`)
- Comma delimiter (no tabs, pipes, or custom delimiters)

**Example:**
```csv
grade,count,default_rate,avg_loan_amount_usd
A,150000,0.045,12500
B,200000,0.082,13000
```

### JSON Files
- Pretty-printed (indent=2)
- UTF-8 encoding
- Always include `metadata` block with:
  - `generated`: ISO 8601 timestamp
  - `source`: upstream file or stage
  - Any other relevant context

**Example:**
```json
{
  "metadata": {
    "generated": "2026-04-18T12:00:00Z",
    "source": "stages/03-segment/output/segment_summary.csv",
    "segment_type": "grade"
  },
  "segments": [
    {
      "value": "A",
      "count": 150000,
      "default_rate_pct": 4.5
    }
  ]
}
```

---

## Dashboard Conventions

### Element IDs (HTML)
```
{component}-{descriptor}

Examples:
✓ portfolio-value
✓ default-rate
✓ expected-loss
✓ grade-chart
✓ segment-table

✗ value1 (meaningless)
✗ portfolioValue (use kebab-case, not camelCase)
```

### CSS Classes
```
.{component-type}

Examples:
✓ .card
✓ .metric
✓ .headline
✓ .chart-container
✓ .crisis-flag

✗ .red-box (describe purpose, not appearance)
✗ .section1 (meaningless)
```

---

## Python Variable Naming

### DataFrames
```
df           ← Main dataframe
{desc}_df    ← Specific dataframe

Examples:
✓ df (primary dataset)
✓ segments_df (segment summary)
✓ exposure_df (exposure summary)
✓ grade_df (grade breakdown)
```

### Aggregations
```
{segment}_{metric}

Examples:
✓ grade_summary (aggregated by grade)
✓ term_summary (aggregated by term)
✓ portfolio_total (portfolio-level aggregate)
```

### Constants
```
UPPER_CASE_WITH_UNDERSCORES

Examples:
✓ RECOVERY_RATE = 0.70
✓ CRISIS_START_YEAR = 2008
✓ CRISIS_END_YEAR = 2010
✓ REQUIRED_COLUMNS = ['loan_amnt', 'int_rate', 'term', 'grade']
```

---

## Report Standards

### PDF Structure
1. **Title** — Project name, date generated
2. **Headline Figures** — Portfolio value, default rate, expected loss (above the fold)
3. **Key Findings** — 3–5 bullet points, business-focused
4. **Segment Highlights** — Top 3 highest-risk segments
5. **Recommendations** — 2–3 actionable next steps
6. **Appendix** — Methodology note (crisis period handling, recovery rate assumption)

### Length
- One page for executive audience
- Two pages maximum for stakeholder audience
- No methodology details on page 1 (move to appendix)

---

## Versioning

### Code and Configuration
- Use git for version control
- No version numbers in filenames
- Tag releases: `v1.0.0`, `v1.1.0`, etc.

### Data Files
- No version numbers in filenames
- Use `generated` timestamp in JSON metadata
- If multiple versions needed, use subdirectories:
  ```
  data/processed/2026-04-18/segment_summary.csv
  data/processed/2026-04-20/segment_summary.csv
  ```

### Reports
- Include generation date in PDF metadata, not filename
- Filename: `executive_summary.pdf` (always overwrites)
- If archiving needed, copy to `report/archive/executive_summary_2026-04-18.pdf`

---

## When to Break These Rules

**Valid exceptions:**
- Client has existing naming convention (document in `stages/01-setup/output/naming_overrides.md`)
- Upstream data source uses different conventions (standardize during Phase 1 clean)
- Legal or compliance requirement mandates specific naming

**Invalid exceptions:**
- "It's easier this way" (consistency matters more than convenience)
- "I prefer camelCase" (project uses snake_case; follow it)
- "The old version did it differently" (update the old version)
