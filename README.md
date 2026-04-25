# Lending Risk Intelligence

Programmatic credit risk analysis and portfolio segmentation system. Produces executive summaries, segment drill-downs, and dollar exposure figures for lending portfolios.

## Data

Source: Lending Club loan dataset (890k records, 2007–2015)

**Important:** Raw data is gitignored. Place the dataset as `data/raw/lending_club.csv` before running the pipeline.

## Pipeline

The analysis runs in three phases:

### Phase 1: Clean (`pipeline/clean.py`)

Ingests raw loan data, engineers binary default outcome, drops >50% null columns, removes noise columns, and outputs cleaned CSV plus data quality report.

**Output:**
- `data/processed/lending_risk_cleaned.csv` — Dataset for analysis
- `data/processed/data_quality_report.json` — Decisions and counts

**Run:**
```bash
python pipeline/clean.py
```

### Phase 2: Segment (`pipeline/segment.py`)

Cuts cleaned data by loan grade, term, purpose, home ownership, and employment length. Calculates default rates and business context for each segment.

**Output:**
- `data/processed/segment_summary.csv` — Aggregate by segment
- `data/processed/{grade,term,purpose, etc.}_breakdown.json` — Drill-down tables

**Run:**
```bash
python pipeline/segment.py
```

### Phase 3: Exposure (`pipeline/exposure.py`)

Translates default rates into dollar risk figures at portfolio and segment level. Calculates expected loss and produces numbers for board and CFO use.

**Output:**
- `data/processed/exposure_summary.csv` — Segment-level exposure
- `data/processed/portfolio_headline.json` — Top-line at-risk dollars
- `data/processed/{exposure breakdown JSONs}` — Dashboard data layer

**Run:**
```bash
python pipeline/exposure.py
```

### Phase 4: Predict (`pipeline/pd_model.py`)

Builds a dual-model system to validate the company's grading accuracy and identify portfolio gaps:

**Model 1: Grade Replicator** — Multiclass classifier that predicts loan grade (A–G) using only origination-time features (loan amount, DTI, income, employment, purpose, home ownership). Tests whether the company's grading is consistent and rational.

**Model 2: Default Predictor** — Logistic regression that independently predicts default probability without access to grade or interest_rate. When compared to actual grades and company-assigned interest rates, identifies mispriced segments and underwriting gaps.

**Output:**
- `data/processed/grade_model.pkl` — Serialized grade replicator
- `data/processed/pd_model.pkl` — Serialized default predictor
- `data/processed/model_comparison.json` — Grade vs. actual, default predictions, identified gaps
- `data/processed/loans_scored.csv` — Full loan file with predicted grade and default probability

**Run:**
```bash
python pipeline/pd_model.py
```

## Dashboard

Vanilla HTML and CSS. No frameworks, no templates.

- **index.html** — Executive summary; portfolio headline figures above the fold
- **segments.html** — Drill-down explorer by grade, term, purpose, etc.
- **exposure.html** — Dollar risk view; segment-level exposure

Serve locally:
```bash
python -m http.server 8000
```
Then open `http://localhost:8000/dashboard/index.html`

## Report

`report/findings.pdf` — One-page summary for stakeholders who will not view the dashboard. Findings only, no methodology.

## Notes

**Crisis Period (2008–2010):** Financial crisis distorted default rates in ways that don't reflect normal lending conditions. These cohorts are flagged in the pipeline and segmented separately in the dashboard. Baseline default rates should not be inferred from crisis-era loans alone.

**Loss Assumptions:** Expected loss model uses 70% recovery rate on defaulted loans (30% loss given default). This is historically calibrated; adjust if your data supports different assumptions.
