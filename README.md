# Lending Risk Intelligence

Programmatic credit risk analysis, portfolio segmentation, and interest rate prediction on LendingClub loan data. Produces executive summaries, segment drill-downs, dollar exposure figures, and a tuned interest rate model.

## Data

Source: LendingClub accepted loans dataset (2007–2018 Q4)

**Important:** Raw data is gitignored due to size. Place the dataset at:
```
lending-risk-data/accepted_2007_to_2018q4.csv/accepted_2007_to_2018Q4.csv
```
The dataset is available on [Kaggle](https://www.kaggle.com/datasets/wordsforthewise/lending-club).

## Pipeline

Stages run in order. Each script reads from the previous stage's output.

### Phase 1: Clean (`pipeline/clean.py`)

Ingests raw loan data, engineers binary default outcome, drops >50% null columns, removes noise columns, and outputs cleaned CSV plus data quality report.

**Output:** `stages/02-clean/output/`
- `lending_risk_cleaned.csv` — dataset for all downstream stages
- `data_quality_report.json` — column decisions and row counts

**Run:**
```bash
python pipeline/clean.py
```

### Phase 2: Segment (`pipeline/segment.py`)

Cuts cleaned data by loan grade, term, purpose, home ownership, and employment length. Calculates default rates and flags crisis-era cohorts.

**Output:** `stages/03-segment/output/`
- `segment_summary.csv` — aggregate default rates by segment
- `crisis_crosstab.csv` — 2008–2010 cohort breakdown
- `{grade,term,purpose,...}_breakdown.json` — drill-down tables

**Run:**
```bash
python pipeline/segment.py
```

### Phase 3: Exposure (`pipeline/exposure.py`)

Translates default rates into dollar risk figures at portfolio and segment level. Calculates expected loss for board and CFO use.

**Output:** `stages/04-exposure/output/`
- `exposure_summary.csv` — segment-level expected loss
- `at_risk_cohorts.csv` — highest-risk cohorts
- `portfolio_headline.json` — top-line at-risk dollars
- Segment-level exposure breakdown JSONs (dashboard data layer)

**Run:**
```bash
python pipeline/exposure.py
```

### Phase 4: Model (`pipeline/model.py`)

Trains a HistGradientBoosting regressor to predict loan interest rate from origination features. Uses permutation importance to rank feature contributions.

**Performance:** Test R² = 0.517, MAE = 0.0252 pp

**Features:** FICO score, loan amount, DTI, annual income, term, revolving utilization, delinquency history, inquiry count, open accounts, public records, employment length, purpose, home ownership

**Output:** Prints model performance and feature importance table to stdout.

**Run:**
```bash
python pipeline/model.py
```

## Notebooks

Exploratory and analytical work underlying the pipeline.

- `notebooks/exploration.ipynb` — initial data profiling and variable survey
- `notebooks/segmentation.ipynb` — segment analysis and default rate deep-dives
- `notebooks/exposure.ipynb` — expected loss calculations and cohort analysis
- `notebooks/interest_rate_model.ipynb` — full modelling walkthrough: OLS baseline, VIF analysis, log transform evaluation, tree model grid search, and HGB tuning to Test R² = 0.507

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

## Notes

**Crisis Period (2008–2010):** Financial crisis distorted default rates in ways that don't reflect normal lending conditions. These cohorts are flagged in the pipeline and segmented separately in the dashboard. Baseline default rates should not be inferred from crisis-era loans alone.

**Loss Assumptions:** Expected loss model uses 70% recovery rate on defaulted loans (30% loss given default). This is historically calibrated; adjust if your data supports different assumptions.
