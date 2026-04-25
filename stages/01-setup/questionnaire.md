# Setup Questionnaire — Lending Risk Intelligence

Answer these questions to configure the pipeline. Press Enter to accept defaults (shown in brackets).

---

## 1. Data Source

**Where is your raw lending data located?**

Expected format: CSV or CSV.gz with columns including `loan_amnt`, `int_rate`, `term`, `grade`, `loan_status`, `purpose`, `home_ownership`, `issue_d`, etc.

```
Data path: [data/raw/lending_club.csv]
```

**Notes:**
- Path can be relative (to project root) or absolute
- File should be ~890k records for Lending Club 2007–2015 dataset
- Larger datasets (2007–2018) are also supported

---

## 2. Loss Modeling Assumptions

**What recovery rate should we assume for defaulted loans?**

Industry average for unsecured consumer credit: 70% (i.e., 30% loss given default)

```
Recovery rate (0.00 to 1.00): [0.70]
```

**When to override:**
- You have actual recovery performance data for this portfolio
- Portfolio includes secured loans (auto, mortgage) with higher recovery
- Collection practices differ materially from industry norm

**Effect:** Recovery rate directly impacts expected loss calculations in Phase 3 (Exposure). Lower recovery = higher expected loss = larger reserves needed.

---

## 3. Crisis Period Definition

**What years should be flagged as "crisis period"?**

Default: 2008–2010 (financial crisis). These cohorts have elevated default rates (often 2–3× normal) that don't reflect typical lending conditions.

```
Crisis start year: [2008]
Crisis end year: [2010]
```

**Notes:**
- Crisis loans are NOT excluded, just flagged for separate analysis
- Dashboard will show crisis vs. normal period default rates side-by-side
- Baseline metrics use normal-period loans only

---

## 4. Output Preferences

**Generate PDF report at end of pipeline?**

```
Generate report (yes/no): [yes]
```

**Include crisis-period loans in executive summary default rate?**

(Not recommended; crisis rates distort baseline)

```
Include crisis in summary (yes/no): [no]
```

---

## Summary

Review your configuration:

```
Data path:           [value from Q1]
Recovery rate:       [value from Q2] ([X]% loss given default)
Crisis period:       [start year]–[end year]
Generate report:     [yes/no]
Use normal-period baseline: [yes if crisis excluded, no otherwise]
```

Proceed with this configuration? (yes/no): [yes]

---

## Next Steps After Setup

1. Verify data file exists at specified path
2. Run `stages/02-clean/CONTEXT.md` to begin Phase 1 (Data Cleaning)
3. Pipeline will use these settings for all calculations
4. To change settings later, re-run `setup` trigger

---

## Configuration Storage

Your responses are saved to:
- `stages/01-setup/output/config.json` (machine-readable)
- `stages/01-setup/output/setup_summary.txt` (human-readable)

All pipeline stages reference `config.json` for data path and assumptions.
