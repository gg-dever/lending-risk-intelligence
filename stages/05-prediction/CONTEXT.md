# Stage 05: Dual-Model Validation and Prediction

**Phase:** 4 of 4 (Clean → Segment → Exposure → Prediction)
**Purpose:** Build two complementary models using origination-time features (known at loan application):
1. **Grade Replicator** (Multiclass) — Validates the company's grade assignment logic by replicating grade A–G from applicant characteristics alone
2. **Default Predictor** (Logistic Regression) — Predicts loan-level probability of default independently to identify portfolio gaps where the company may be mispricing risk

Together, these models provide portfolio context: confirming grading consistency and flagging segments where defaults exceed expectations for their assigned grade.

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Cleaned data | `../02-clean/output/lending_risk_cleaned.csv` | Full file | Loan-level origination-time features and outcome for training both models |
| Actual grades | `cleaned data: grade column` | All records | Target for Grade Replicator; also used to validate whether predictions match actual |
| Segment summary | `../03-segment/output/segment_summary.csv` | Full file | Baseline empirical default rates; used for calibration comparison |
| Business rules | `references/business-rules.md` | "Default Outcome Definition" | Outcome definition for both models |
| Pipeline script | `pipeline/pd_model.py` | Full file | Execution logic for both models |

**Do not load:**
- Raw data (use cleaned version only)
- Interest rates (this is a post-decision feature that Grade Replicator should not use)
- Exposure outputs (these stages run independently; validation happens during dashboard merge, not here)

---

## Process

### Features

Build both models using origination-time features only (known at application before company assigns grade or price):

**Categorical:** `term`, `purpose`, `home_ownership`
**Numeric:** `loan_amnt`, `dti`, `annual_inc`
**Bucketed:** `emp_length_bucket`, `dti_bucket`, `loan_amnt_bucket`

One-hot encode categoricals, standardize numerics. Train/test split 80/20, stratified by outcome.

### Model 1: Grade Replicator

**Task:** Multiclass classification to predict grade A–G from origination-time features.

**Why:** Tests whether the company's grading is:
- Consistent (can we replicate it?)
- Rational (do feature coefficients make business sense?)
- Exploitable (where do model predictions diverge from actual grades?)

**Build:**
1. Train multiclass logistic regression
2. Evaluate: F1-score by class, overall accuracy, confusion matrix
3. Extract coefficients: which features push loans toward higher/lower grades?
4. Document misclassification patterns (e.g. loans we predict C but company grades B)

### Model 2: Default Predictor

**Task:** Binary classification to predict `is_default` using the same origination-time features.

**Why:** Builds an independent PD estimate that can be compared against:
- Company's actual default outcome (validates model calibration)
- Company's grade assignments (finds segments where grades don't match defaults)
- Company's interest_rate pricing (identifies mispricing opportunities)

**Build:**
1. Train logistic regression for interpretability
2. Evaluate: AUC-ROC, precision/recall, Gini coefficient
3. Extract coefficients: feature direction and magnitude for PD
4. Score full loan file: assign predicted PD to every loan

### Model Comparison and Validation

1. **Grade Model Quality**
   - F1-score by class should be > 0.70 (not perfectly consistent, but structured)
   - If F1 > 0.90, company may be over-determined by a few strong features
   - If F1 < 0.50, grading may be arbitrary or influenced by post-origination data

2. **Default Model Quality**
   - AUC should be 0.65–0.80 (consumer credit typical range)
   - AUC > 0.90 suggests data leakage (post-default fields in features)
   - AUC < 0.60 suggests features have no predictive signal

3. **Gap Analysis**
   - For each grade, compare: company's empirical default rate vs. our model's mean PD score
   - If grade A has 5% empirical default but our model predicts 8% for grade A borrowers: either (a) company is selecting A-applicants well, or (b) A-prices are too low
   - Flag segments where: PD prediction > 1.5× empirical default (potential underpricing)

---

## Outputs

| Artifact | Location | Format | Purpose |
|----------|----------|--------|---------|
| Grade Replicator Model | `stages/05-prediction/output/grade_model.pkl` | Pickle | Serialized multiclass classifier (grade prediction) |
| Default Predictor Model | `stages/05-prediction/output/pd_model.pkl` | Pickle | Serialized logistic regression (PD prediction) |
| Grade Model Report | `stages/05-prediction/output/grade_model_performance.json` | JSON | F1-score by class, accuracy, confusion matrix, feature coefficients |
| Default Model Report | `stages/05-prediction/output/model_performance.json` | JSON | AUC-ROC, precision/recall, Gini, feature coefficients, calibration check |
| Gap Analysis | `stages/05-prediction/output/gap_analysis.json` | JSON | Grade vs. empirical default vs. predicted PD; flagged mispricing segments |
| Scored Loans | `stages/05-prediction/output/loans_scored.csv` | CSV | Full loan file with `predicted_grade`, `predicted_pd`, and validation flags |

**Downstream usage:**
- Grade Replicator → Dashboard model explainability (grade logic validation)
- Default Predictor → Dashboard predictive layer (PD distribution, risk stratification)
- Gap Analysis → Board/Risk Officer review (where is pricing not matching reality?)
- Scored Loans → Portfolio management tools (segment by predicted PD, compare to actual grade)

---

## Audit

### Grade Replicator Audits

1. **Per-class F1-score**
   - All classes F1 > 0.70 (model captures grading structure)
   - If any class F1 < 0.50, that grade is either rare or inconsistently assigned

2. **Confusion matrix pattern**
   - Diagonal dominance (correct grade on diagonal > off-diagonal)
   - No systematic bias (e.g. always predicting C instead of B)
   - Adjacency errors (predicting B for C borrowers is okay; A for G would be suspicious)

3. **Feature coefficient sanity**
   - DTI, dti_bucket: positive coefficient (higher DTI → higher grade) INVALID (lower grade = B is good)
   - Loan_amnt: may vary (larger loans could be A-rated or riskier)
   - Annual_inc: negative coefficient (higher income → lower grade) INVALID

### Default Predictor Audits

1. **AUC reasonableness**
   - Consumer credit models typically achieve AUC 0.65–0.80
   - If AUC > 0.90, likely data leakage (post-default columns in features)
   - If AUC < 0.60, model has no signal (check feature encoding, outcome definition)

2. **Score distribution**
   - `predicted_pd` should range 0–1 with no clipping at boundaries
   - Mean `predicted_pd` should be close to overall `is_default` mean (~0.20)
   - Kurtosis/skewness normal (not all scores clustered at 0.1 or 0.9)

3. **Grade ordering**
   - Mean `predicted_pd` by grade must be monotonically increasing A → G
   - If not (e.g. C defaults more than D), model is underfitting or grades are inverse-coded

4. **No data leakage**
   - Features must be origination-time only (known when loan is issued)
   - Explicitly exclude: `recoveries`, `collection_recovery_fee`, `out_prncp`, `total_rec_late_fee`
   - Explicitly exclude: `int_rate` (set after grading)

5. **Calibration check**
   - For each grade: compare mean `predicted_pd` to empirical default rate
   - Deviation > 5pp warrants investigation (e.g. grade A: empirical 5%, predicted 11%)
   - Deviations > 10pp indicate potential data bias or feature encoding errors

---

## Notes

**Model Purposefulness:** Grade Replicator and Default Predictor serve distinct business goals:
- Grade Replicator validates company grading logic (consistency/rationality). If F1 scores are low, grading may be influenced by post-origination data (which leaks into credit assessments).
- Default Predictor identifies portfolio gaps (mispricing). Segments where predicted PD >> empirical default are candidates for price increases or origination limits.

**Feature Scope — Origination-Time Only:** Both models exclude interest_rate and grade because these are post-decision features. This ensures the models represent independent assessment of applicant creditworthiness, not reproductions of company decisions. That separation is essential for gap analysis to be meaningful.

**Interpretability — Logistic Regression:** Both models use logistic regression (vs. gradient boosting) to maintain interpretability. Coefficients directly translate to log-odds changes, which risk officers and regulators can reason about.

**Validation Cadence:** Re-train both models quarterly:
- Grade Replicator: Check for feature drift (has income predictiveness changed?)
- Default Predictor: Check for portfolio drift (are new originations defaulting differently?)
