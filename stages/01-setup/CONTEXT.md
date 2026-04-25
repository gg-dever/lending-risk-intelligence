# Stage 01: Project Setup and Configuration

**Purpose:** Configure data paths, loss assumptions, crisis period boundaries before running analytical pipeline

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Questionnaire | `stages/01-setup/questionnaire.md` | Full file | Prompts for user configuration decisions |
| Business rules | `references/business-rules.md` | "Loss Modeling Assumptions", "Crisis Period Handling" | Default values and rationale |

**Do not load:**
- Analytical outputs (none exist yet; this is pre-pipeline setup)
- Pipeline scripts (configuration only, no execution)

---

## Process

1. **Run questionnaire**
   - Load `stages/01-setup/questionnaire.md`
   - Prompt user for each configuration item
   - Validate responses (paths exist, rates are decimal 0–1, years are 4-digit integers)

2. **Record configuration**
   - Save responses to `stages/01-setup/output/config.json`
   - Include:
     - `data_path`: Path to raw CSV
     - `recovery_rate`: Loss recovery assumption (default 0.70)
     - `crisis_start_year`: Crisis period start (default 2008)
     - `crisis_end_year`: Crisis period end (default 2010)
     - `generated`: Timestamp

3. **Replace placeholders (optional)**
   - If pipeline scripts contain placeholders:
     - `{{DATA_PATH}}` → user-specified data path
     - `{{RECOVERY_RATE}}` → user-specified recovery rate
     - `{{CRISIS_START}}` / `{{CRISIS_END}}` → user-specified crisis years
   - Update scripts in place or generate configured versions in `stages/01-setup/output/`

4. **Verify data accessibility**
   - Check that file at `data_path` exists and is readable
   - Print first 5 rows and column list (preview only, no analysis)
   - Confirm record count is in expected range (500k–2M for Lending Club datasets)

5. **Generate setup summary**
   - Print configuration summary:
     - Data path
     - Recovery rate assumption
     - Crisis period boundaries
     - Next step (run `stages/02-clean/CONTEXT.md`)

---

## Outputs

| Artifact | Location | Format | Purpose |
|----------|----------|--------|---------|
| Configuration | `stages/01-setup/output/config.json` | JSON | User-specified settings for pipeline |
| Setup summary | `stages/01-setup/output/setup_summary.txt` | Text | Human-readable configuration recap |

**Downstream usage:**
- `config.json` → Referenced by all pipeline stages (data path, assumptions)

---

## Notes

- **One-time setup:** This stage is run once at project start. Re-run only if data source changes or assumptions need updating.

- **Placeholder replacement:** If using placeholder-based configuration, keep originals in `pipeline/` and write configured versions to `stages/01-setup/output/configured_scripts/`. This preserves the templates.

- **Data preview only:** Setup does NOT perform cleaning or analysis. It verifies accessibility and prints a sample for user confirmation.
