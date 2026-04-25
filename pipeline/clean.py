"""
PHASE 1: Data Cleaning and Outcome Engineering
Lending Risk Intelligence Pipeline

This script:
1. Loads the raw Lending Club dataset
2. Defines binary default outcome (Charged-Off + Default = 1, Fully Paid = 0)
3. Filters to terminal loan states only
4. Drops columns with >50% null values
5. Removes noise columns (emp_title, etc.)
6. Outputs cleaned CSV and data quality report
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(message)s',
    datefmt='%H:%M:%S'
)

# ============================================================================
# CONSTANTS
# ============================================================================

TERMINAL_STATES = [
    'Fully Paid',
    'Charged Off',
    'Default',
    'Does not meet the credit policy. Status:Fully Paid',
    'Does not meet the credit policy. Status:Charged Off',
]

DEFAULT_STATES = [
    'Charged Off',
    'Default',
    'Does not meet the credit policy. Status:Charged Off',
]

NOISE_COLS = [
    'emp_title',   # 280k+ categories, not a segmentation variable
    'id',          # identifier only, no analytical value
    'member_id',   # deprecated by Lending Club, almost entirely null
    'url',         # links to loan listings, no analytical value
]

REQUIRED_COLS = [
    'loan_amnt',
    'int_rate',
    'term',
    'grade',
    'purpose',
    'home_ownership',
    'emp_length',
    'issue_d',
]

RAW_DATA_PATH = (
    '/Users/gagepiercegaubert/Desktop/career_projects/lending-risk-intelligence'
    '/lending-risk-data/accepted_2007_to_2018q4.csv/accepted_2007_to_2018Q4.csv'
)
OUTPUT_DIR = 'stages/02-clean/output'


# ============================================================================
# SECTION 1: LOAD
# ============================================================================

def load_data():
    """Load raw accepted loans dataset."""
    df = pd.read_csv(RAW_DATA_PATH, low_memory=False)
    logging.info(f"Loaded {len(df):,} records, {len(df.columns)} columns")
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    # --- Load ---
    df = load_data()
    source_records = len(df)

    # --- Section 2: Binary default outcome ---
    # Business rule: terminal states only; unresolved loans (Current, Late, Grace) excluded
    df = df[df['loan_status'].isin(TERMINAL_STATES)].copy()
    logging.info(f"After filtering to terminal states: {len(df):,} records")

    df['is_default'] = df['loan_status'].isin(DEFAULT_STATES).astype(int)
    default_rate = df['is_default'].mean()
    logging.info(f"Default rate: {default_rate:.2%}")
    logging.info(f"Defaults: {df['is_default'].sum():,}  Non-defaults: {(1 - df['is_default']).sum():,}")

    # --- Section 3: Crisis period flag ---
    # Note: Crisis period (2008-2010) shows lower aggregate default rate than expected.
    # This is survivorship bias — post-2015 current loans were filtered as non-terminal,
    # skewing the non-crisis group. Flag retained for segmentation.
    df['issue_d'] = pd.to_datetime(df['issue_d'], format='%b-%Y')
    df['issue_year'] = df['issue_d'].dt.year
    df['crisis_period'] = df['issue_year'].between(2008, 2010).astype(int)
    logging.info(f"Crisis period loans (2008–2010): {df['crisis_period'].sum():,}")
    logging.info(f"Normal period loans: {(1 - df['crisis_period']).sum():,}")

    # --- Section 4: Drop >50% null columns ---
    null_rates = (df.isnull().sum() / len(df)).sort_values(ascending=False)
    cols_to_drop = null_rates[null_rates > 0.5].index.tolist()
    logging.info(f"Dropping {len(cols_to_drop)} columns with >50% null")
    df = df.drop(columns=cols_to_drop)
    logging.info(f"After null-based drops: {len(df.columns)} columns remain")

    # --- Section 5: Drop noise columns ---
    df = df.drop(columns=[col for col in NOISE_COLS if col in df.columns])
    logging.info(f"After noise drops: {len(df.columns)} columns remain")

    # --- Section 6: Drop rows with nulls in required columns ---
    rows_before = len(df)
    df = df.dropna(subset=REQUIRED_COLS)
    rows_dropped = rows_before - len(df)
    logging.info(f"Dropped {rows_dropped:,} rows with nulls in required columns")
    logging.info(f"Retained: {len(df):,} records")

    # --- Section 7: Standardize formats ---
    # int_rate and revol_util stored as floats without % sign — convert to decimal
    df['int_rate'] = df['int_rate'].astype(float) / 100
    df['revol_util'] = df['revol_util'].astype(float) / 100
    df['earliest_cr_line'] = pd.to_datetime(df['earliest_cr_line'], format='%b-%Y')
    for col in ['grade', 'purpose', 'home_ownership', 'term']:
        df[col] = df[col].str.strip()
    logging.info(f"Data cleaned. Final shape: {len(df):,} records, {len(df.columns)} columns")

    # --- Section 8: Save output ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_csv = f'{OUTPUT_DIR}/lending_risk_cleaned.csv'
    df.to_csv(output_csv, index=False)
    logging.info(f"Cleaned data saved to {output_csv}")

    # --- Section 9: Data quality report ---
    report = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "source_records": source_records,
            "final_records": len(df),
            "final_columns": len(df.columns),
        },
        "outcome_engineering": {
            "terminal_states": TERMINAL_STATES,
            "default_states": DEFAULT_STATES,
            "excluded_states": "Current, Late, In Grace Period (unresolved — outcome unknown)",
            "default_rate": f"{default_rate:.2%}",
            "default_count": int(df['is_default'].sum()),
            "non_default_count": int((1 - df['is_default']).sum()),
        },
        "filtering_decisions": {
            "crisis_period_flagged": "2008–2010 cohort flagged separately; not removed",
            "crisis_period_note": "Survivorship bias causes crisis period to show lower default rate; flag retained for segmentation",
            "rows_retained_after_terminal_filter": len(df),
        },
        "null_handling": {
            "threshold": ">50%",
            "columns_dropped": cols_to_drop,
            "exceptions_kept": "None — no sparse columns mapped to required segmentation variables",
        },
        "noise_removal": {
            "columns_dropped": NOISE_COLS,
            "rationale": {
                "emp_title": "280k+ categories; not suitable for business segmentation",
                "id": "identifier only, no analytical value",
                "member_id": "deprecated by Lending Club, almost entirely null",
                "url": "links to loan listings, no analytical value",
            }
        },
        "required_columns": {
            "columns": REQUIRED_COLS,
            "rows_dropped_for_nulls_in_required": rows_dropped,
        },
        "format_standardization": {
            "int_rate": "divided by 100 (stored as float, no % sign)",
            "revol_util": "divided by 100 (stored as float, no % sign)",
            "earliest_cr_line": "parsed to datetime format='%b-%Y'",
            "categoricals_stripped": "grade, purpose, home_ownership, term",
        },
    }

    report_path = f'{OUTPUT_DIR}/data_quality_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Data quality report saved to {report_path}")

# ============================================================================
# NEXT STEPS
# ============================================================================
# When you're ready for Phase 2 (segment.py):
# - Run this script to generate cleaned CSV
# - Review the data quality report
# - Proceed to segmentation: grade, term, purpose, home_ownership, emp_length
# - Each segment should answer a specific business question


if __name__ == '__main__':
    main()
