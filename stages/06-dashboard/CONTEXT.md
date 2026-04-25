# Stage 06: Dashboard Visualization

**Purpose:** Render analytical outputs as interactive HTML dashboard with headline figures and segment drill-downs

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Portfolio headline | `../04-exposure/output/portfolio_headline.json` | Full file | Top-line metrics for index.html |
| Exposure summary | `../04-exposure/output/exposure_summary.csv` | Full file | Segment-level dollar exposure for exposure.html |
| Segment breakdowns | `../03-segment/output/{grade,term,purpose,home_ownership,employment_length}_breakdown.json` | Full files | Drill-down data for segments.html |
| Exposure breakdowns | `../04-exposure/output/{grade,term,purpose,home_ownership,employment_length}_exposure.json` | Full files | Drill-down data for exposure.html |
| Dashboard templates | `dashboard/{index,segments,exposure}.html` | Full files | HTML structure and JS rendering logic |
| Styles | `dashboard/styles/{main,charts}.css` | Full files | Visual presentation |
| Naming conventions | `references/naming-conventions.md` | "Dashboard Conventions" | Element IDs, CSS classes, formatting standards |

**Do not load:**
- Raw or cleaned data (use JSON/CSV outputs only)
- Pipeline scripts (not relevant to visualization)

---

## Process

1. **Verify upstream outputs exist**
   - Check that all required JSON and CSV files exist in `../03-segment/output/` and `../04-exposure/output/`
   - If missing, prompt user to run previous stages

2. **Update index.html (Executive Summary)**
   - Load `portfolio_headline.json`
   - Populate headline metrics:
     - Portfolio Value (format: `$X.XB`)
     - Default Rate (format: `XX.X%`)
     - Expected Loss (format: `$X.XB`)
     - Loss Rate (format: `X.X%`)
   - Load `grade_breakdown.json`
   - Render "Default Rate by Grade" chart (bar chart, grades A–G on x-axis, default rate on y-axis)
   - Add crisis-period note at bottom

3. **Update segments.html (Drill-Down Explorer)**
   - Load all `*_breakdown.json` files
   - For each segmentation type (grade, term, purpose, ownership, employment):
     - Render section with table
     - Columns: Segment, Count, Default Rate, Avg Loan Amount, Total Portfolio Value
     - Crisis vs. normal period toggle (show both side-by-side or allow user to switch views)
   - Sort tables by default rate descending (show riskiest first)

4. **Update exposure.html (Dollar Risk View)**
   - Load `exposure_summary.csv`
   - Render segment-level exposure table
   - Columns: Segment Type, Segment, Portfolio Value, Default Rate, Expected Loss, Loss Rate, % of Portfolio Exposure
   - Highlight segments with:
     - Expected loss >$100M AND default rate >10%
   - Show crisis vs. normal period exposure comparison

5. **Add timestamps**
   - Extract `generated` timestamp from JSON metadata
   - Display in footer of each HTML page: "Last updated: YYYY-MM-DD HH:MM"

6. **Test dashboard locally**
   - Run `python -m http.server 8000` in project root
   - Open `http://localhost:8000/dashboard/index.html`
   - Verify:
     - All headline figures render correctly
     - Charts display (no JS errors in console)
     - Navigation works (index → segments → exposure)
     - Crisis-period labels appear where expected
   - If errors, debug and re-render

7. **Copy dashboard to output folder**
   - Copy entire `dashboard/` directory to `stages/06-dashboard/output/dashboard/`
   - This preserves a snapshot of the dashboard with current data
   - Future pipeline runs will overwrite data files but preserve dashboard structure

---

## Outputs

| Artifact | Location | Format | Purpose |
|----------|----------|--------|---------|
| Dashboard snapshot | `stages/06-dashboard/output/dashboard/` | HTML/CSS/JS | Rendered dashboard with current data |
| Rendering log | `stages/06-dashboard/output/render_log.txt` | Text | Data files loaded, charts rendered, errors encountered |

**Downstream usage:**
- Dashboard snapshot → Served locally or deployed to web server
- Rendering log → Debugging if charts don't display correctly

---

## Audit

Run these checks before finalizing dashboard:

1. **Headline figures match source**
   - Portfolio value on index.html = `portfolio_headline.json` value
   - Default rate on index.html = `portfolio_headline.json` value
   - If mismatch, check JS data loading logic

2. **Segment counts add up**
   - On segments.html, sum of counts within a segmentation type should equal total portfolio loan count
   - If not, some segments are missing from display

3. **Chart rendering**
   - All charts should display (no blank spaces or JS errors)
   - If chart fails to render, check:
     - JSON structure matches expected format
     - Element IDs in HTML match JS selectors

4. **Crisis labeling**
   - Every page should have crisis-period note or toggle
   - Crisis default rates should be labeled "Crisis (2008–2010)"
   - Normal default rates should be labeled "Normal Period"

5. **Navigation works**
   - All nav links functional (index ↔ segments ↔ exposure)
   - Active page highlighted in nav bar

If any audit fails, fix before proceeding to Stage 07 (Report).

---

## Notes

- **Vanilla HTML/CSS:** No frameworks (React, Vue, etc.). Dashboard uses plain JavaScript for rendering. This reduces dependencies and makes deployment trivial (just copy files to web server).

- **Data loading:** Dashboard JavaScript loads JSON files at runtime. If deploying to static hosting (S3, GitHub Pages), ensure JSON files are included in deployment.

- **Chart library:** Dashboard uses vanilla JS for simple bar charts. For more complex visualizations (line charts, scatter plots), consider adding Chart.js or D3.js. Document any library additions in `stages/06-dashboard/output/render_log.txt`.

- **Responsive design:** CSS includes basic mobile responsiveness. Test on mobile viewport to ensure tables don't overflow.
