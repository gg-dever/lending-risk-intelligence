# Stages Overview — Lending Risk Intelligence Pipeline

**Purpose:** Quick reference for stage navigation and dependencies

---

## Pipeline Flow

```
01-setup → 02-clean → 03-segment → 04-exposure → 05-prediction → 06-dashboard
                                                                        ↓
                                                                    07-report
```

**Dependencies:**
- **02-clean** requires: raw data at configured path
- **03-segment** requires: `02-clean/output/lending_risk_cleaned.csv`
- **04-exposure** requires: `02-clean/output/lending_risk_cleaned.csv`, `03-segment/output/segment_summary.csv`
- **05-prediction** requires: `02-clean/output/lending_risk_cleaned.csv`, `03-segment/output/segment_summary.csv`
- **06-dashboard** requires: all `03-segment/output/*.json`, `04-exposure/output/*.json`, and `05-prediction/output/loans_scored.csv`
- **07-report** requires: `04-exposure/output/portfolio_headline.json`, `04-exposure/output/exposure_summary.csv`, `05-prediction/output/model_performance.json`

**Parallelization:**
- Stages 02–05 are sequential (each depends on previous)
- Stage 06 and 07 can run in parallel after Stage 05 completes

---

## Stage Quick Reference

| Stage | Purpose | Key Inputs | Key Outputs |
|-------|---------|------------|-------------|
| **01-setup** | Configure paths and assumptions | Questionnaire, business rules | `config.json`, `setup_summary.txt` |
| **02-clean** | Data cleaning, outcome engineering | Raw CSV, business rules | `lending_risk_cleaned.csv`, `data_quality_report.json` |
| **03-segment** | Cohort analysis, default rates | Cleaned CSV, segmentation guide | `segment_summary.csv`, `*_breakdown.json` |
| **04-exposure** | Dollar loss modeling | Cleaned CSV, segment summary, business rules | `portfolio_headline.json`, `exposure_summary.csv`, `*_exposure.json` |
| **05-prediction** | PD model, loan scoring | Cleaned CSV, segment summary | `loans_scored.csv`, `pd_model.pkl`, `model_performance.json` |
| **06-dashboard** | HTML visualization | All segment, exposure, and prediction outputs | Dashboard snapshot (HTML/CSS/JS) |
| **07-report** | Executive summary PDF | Portfolio headline, exposure summary, model performance | `executive_summary.pdf`, `report_metadata.json` |

---

## Entry Points

**Starting from scratch:**
1. Run `setup` trigger (user answers questionnaire)
2. Go to `02-clean/CONTEXT.md`

**Resuming after interruption:**
1. Run `status` trigger to see what's complete
2. Navigate to the first incomplete stage's CONTEXT.md

**Rerunning a specific stage:**
1. Go directly to `{NN-stage}/CONTEXT.md`
2. Follow Inputs/Process/Outputs contract
3. Note: Downstream stages may need rerunning if inputs change

---

## Audit-First Workflow

Every analytical stage (02, 03, 04) includes an Audit section in its CONTEXT.md. Run audits BEFORE writing to `output/`:

- **02-clean:** Verify default outcome validity, crisis flag, no required-column nulls
- **03-segment:** Check grade monotonicity, term pattern, purpose volume, crisis elevation
- **04-exposure:** Verify portfolio-level math, segment coverage, grade exposure monotonicity
- **05-prediction:** Verify AUC reasonableness, no data leakage, grade PD monotonicity

If audit fails, fix and re-run before proceeding to next stage.

---

---

## File Locations by Stage

### Stage 02 (Clean)
```
output/
├── lending_risk_cleaned.csv
└── data_quality_report.json
```

### Stage 03 (Segment)
```
output/
├── segment_summary.csv
├── grade_breakdown.json
├── term_breakdown.json
├── purpose_breakdown.json
├── home_ownership_breakdown.json
└── employment_length_breakdown.json
```

### Stage 04 (Exposure)
```
output/
├── portfolio_headline.json
├── exposure_summary.csv
├── grade_exposure.json
├── term_exposure.json
├── purpose_exposure.json
├── home_ownership_exposure.json
└── employment_length_exposure.json
```

### Stage 05 (Prediction)
```
output/
├── loans_scored.csv
├── pd_model.pkl
└── model_performance.json
```

### Stage 06 (Dashboard)
```
output/
├── dashboard/              (full dashboard snapshot)
└── render_log.txt
```

### Stage 07 (Report)
```
output/
├── executive_summary.md
├── executive_summary.pdf
└── report_metadata.json
```

---

## Common Issues

**Issue:** Stage fails to find upstream file
**Fix:** Check that previous stage completed successfully and wrote to `output/`

**Issue:** Audit fails (e.g., grade default rates not monotonic)
**Fix:** Return to Process section, investigate groupby logic or data quality

**Issue:** Dashboard charts don't render
**Fix:** Verify JSON structure matches expected format (see `segmentation-guide.md`)

**Issue:** Report generation fails (pandoc error)
**Fix:** Ensure pandoc is installed: `brew install pandoc` (macOS) or `apt install pandoc` (Linux)

---

## Customization

**Adding a new segmentation:**
1. Update `references/segmentation-guide.md` (add business question, expected pattern)
2. Update `pipeline/segment.py` (add groupby logic)
3. Update `stages/03-segment/CONTEXT.md` (add to Process steps, Outputs, Audit)
4. Update `stages/06-dashboard/CONTEXT.md` (add rendering logic for new segment)
5. Re-run Stages 03–05

**Changing loss assumptions:**
1. Update `references/business-rules.md` "Loss Modeling Assumptions"
2. Update `stages/04-exposure/CONTEXT.md` Process step 2 (constants)
3. Re-run Stage 04 (and 05, 06 if already complete)

**Adding a new stage:**
1. Create `stages/{NN-name}/` with `input/` and `output/` subdirs
2. Write `stages/{NN-name}/CONTEXT.md` (follow Inputs/Process/Outputs contract)
3. Update this file (stages/CONTEXT.md) with new stage in pipeline flow
4. Update `FEYNMAN.md` routing table

---

## Usage Notes

- **Human editing:** You can edit any `output/` file between stages. Next stage will use edited version.
- **Idempotency:** Each stage can be re-run independently (outputs will be overwritten).
- **State:** No shared state or caching. Each stage reads from `output/` folders, writes to its own `output/` folder.
- **Traceability:** Every output includes metadata (timestamp, source files, assumptions).
