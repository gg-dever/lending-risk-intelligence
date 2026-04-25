# Stage 07: Executive Report Generation

**Purpose:** Produce one-page executive summary (PDF) for stakeholders who will not view the dashboard

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Portfolio headline | `../04-exposure/output/portfolio_headline.json` | Full file | Top-line figures for report |
| Exposure summary | `../04-exposure/output/exposure_summary.csv` | Full file | Segment highlights |
| Segment breakdowns | `../03-segment/output/*_breakdown.json` | Metadata only | Timestamp, segment counts |
| Business rules | `references/business-rules.md` | "Loss Modeling Assumptions", "Crisis Period Handling" | Methodology appendix |
| Naming conventions | `references/naming-conventions.md` | "Report Standards" | Structure, length, formatting |

**Do not load:**
- Raw or cleaned data (use aggregated outputs only)
- Dashboard files (report is text-based, not interactive)

---

## Process

1. **Verify upstream outputs exist**
   - Check that `portfolio_headline.json` and `exposure_summary.csv` exist
   - If missing, prompt user to run previous stages

2. **Extract headline figures**
   - From `portfolio_headline.json`:
     - Portfolio Value (format: `$X.X billion`)
     - Default Rate (format: `XX.X%`)
     - Expected Loss (format: `$XXX million`)
     - Loss Rate (format: `X.X%`)

3. **Identify key findings**
   - From `exposure_summary.csv`:
     - Top 3 segments by expected loss (dollar amount)
     - Top 3 segments by default rate (percentage)
     - Highest-risk combination (if cross-segment analysis exists)
   - For each finding, write one-sentence business implication

4. **Generate recommendations**
   - Based on findings, propose 2–3 actionable next steps:
     - Example: "Reduce origination volume for Grade F loans by 20% to lower portfolio risk."
     - Example: "Increase monitoring frequency for 60-month loans in debt_consolidation segment."
     - Example: "Set aside $XX million in reserves to cover expected losses."

5. **Write executive summary**
   - Structure (reference `naming-conventions.md` "Report Standards"):
     1. **Title:** "Lending Risk Intelligence — Executive Summary"
     2. **Headline Figures:** Portfolio value, default rate, expected loss, loss rate (above the fold)
     3. **Key Findings:** 3–5 bullet points (each <2 sentences)
     4. **Segment Highlights:** Top 3 highest-risk segments (table format: segment, portfolio value, default rate, expected loss)
     5. **Recommendations:** 2–3 actionable next steps
     6. **Appendix:** Methodology note (crisis period handling, recovery rate assumption)
   - Length: One page (two pages maximum if appendix is detailed)

6. **Convert to PDF**
   - Write summary as Markdown: `stages/07-report/output/executive_summary.md`
   - Convert to PDF using pandoc or similar:
     ```bash
     pandoc executive_summary.md -o executive_summary.pdf --pdf-engine=xelatex
     ```
   - Save to `stages/07-report/output/executive_summary.pdf`
   - Also copy to `report/findings.pdf` (project-level location for easy access)

7. **Generate metadata**
   - Create `stages/06-report/output/report_metadata.json`:
     - `generated`: timestamp
     - `source_files`: list of upstream JSON/CSV files used
     - `headline_figures`: portfolio value, default rate, expected loss, loss rate
     - `top_segments`: top 3 by exposure
     - `recommendations`: list of recommendations
   - This JSON allows dashboard or future tools to display report summary

---

## Outputs

| Artifact | Location | Format | Purpose |
|----------|----------|--------|---------|
| Executive summary (Markdown) | `stages/07-report/output/executive_summary.md` | Markdown | Source document for PDF |
| Executive summary (PDF) | `stages/07-report/output/executive_summary.pdf` | PDF | Deliverable for stakeholders |
| Report copy | `report/findings.pdf` | PDF | Project-level location (easy access) |
| Report metadata | `stages/07-report/output/report_metadata.json` | JSON | Machine-readable summary of findings |

**Downstream usage:**
- `executive_summary.pdf` → Emailed to CFO, risk officers, board members
- `report_metadata.json` → Could be integrated into dashboard as "Executive Summary" tab

---

## Audit

Run these checks before finalizing report:

1. **Headline figures match source**
   - Portfolio value in report = `portfolio_headline.json` value
   - Default rate in report = `portfolio_headline.json` value
   - If mismatch, re-extract from source JSON

2. **Length constraint**
   - Report should be one page (two pages max with appendix)
   - If longer, cut details and move to appendix or dashboard

3. **Business-focused language**
   - Findings should be written in business terms, not technical jargon
   - Example: "Grade F loans carry $45M exposure at 15% default rate" (good)
   - Example: "Grade F has 0.15 mean is_default in cleaned dataset" (bad)

4. **Recommendations are actionable**
   - Each recommendation should specify WHO does WHAT
   - Example: "Risk team to increase monitoring frequency" (good)
   - Example: "Consider monitoring" (bad; vague, no owner)

5. **Appendix completeness**
   - Methodology note must include:
     - Default definition (Charged-Off + Default = 1)
     - Recovery rate assumption (70%)
     - Crisis period handling (2008–2010 flagged separately)
   - If any of these missing, add to appendix

If any audit fails, revise report before finalizing.

---

## Notes

- **Audience:** CFO, risk officers, board members who want headline numbers and action items, not analytical details. Dashboard is for analysts; report is for decision-makers.

- **No methodology on page 1:** Executives care about "what" and "so what", not "how". Move all methodology to appendix on page 2.

- **Visuals (optional):** If report needs a chart (e.g., default rate by grade), embed as image. Keep it simple (one chart max).

- **Update frequency:** Report should be regenerated whenever pipeline runs. Include generation timestamp in footer so readers know how current the figures are.

- **Distribution:** PDF can be emailed, printed, or uploaded to shared drive. No dependencies, no interactive elements—just a static document.
