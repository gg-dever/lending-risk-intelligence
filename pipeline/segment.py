"""
PHASE 2: Cohort and Segmentation Analysis
Lending Risk Intelligence Pipeline

Segments cleaned loan data by key risk dimensions and outputs summary tables
for dashboard consumption and Phase 3 exposure modeling.

Execute Phase 1 (clean.py) first.
"""

import os
import json
import logging
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(message)s',
    datefmt='%H:%M:%S',
)

INPUT_PATH = 'stages/02-clean/output/lending_risk_cleaned.csv'
OUTPUT_DIR = 'stages/03-segment/output'


# ============================================================================
# HELPERS
# ============================================================================

def _seg(df, group_col):
    """Return default rate, count, and loan amount stats for a single grouping."""
    return (
        df.groupby(group_col, observed=True)['is_default']
        .agg(loan_count='count', default_count='sum', default_rate='mean')
        .join(df.groupby(group_col, observed=True)['loan_amnt'].agg(avg_loan_amount='mean', total_portfolio_value='sum'))
        .join(df.groupby(group_col, observed=True)['int_rate'].agg(avg_int_rate='mean'))
        .reset_index()
        .rename(columns={group_col: 'segment_value'})
        .assign(segment_type=group_col)
    )


def _add_buckets(df):
    """Add bucketed columns used across multiple segments."""
    df['int_rate_bucket'] = pd.cut(
        df['int_rate'],
        bins=[0, 0.10, 0.15, 0.20, 1.0],
        labels=['0-10%', '10-15%', '15-20%', '20%+'],
    )
    df['dti_bucket'] = pd.cut(
        df['dti'],
        bins=[0, 10, 20, 30, 40, 50, np.inf],
        labels=['0-10', '10-20', '20-30', '30-40', '40-50', '50+'],
    )
    df['loan_amnt_bucket'] = pd.cut(
        df['loan_amnt'],
        bins=[0, 5000, 10000, 15000, 20000, np.inf],
        labels=['0-5k', '5k-10k', '10k-15k', '15k-20k', '20k+'],
    )
    emp_length_num = df['emp_length'].str.extract(r'(\d+)')[0].astype(float)
    emp_length_num = emp_length_num.mask(df['emp_length'].eq('< 1 year'), 0.5)
    df['emp_length_bucket'] = pd.cut(
        emp_length_num,
        bins=[0, 1, 3, 5, 10, np.inf],
        labels=['0-1', '1-3', '3-5', '5-10', '10+'],
        include_lowest=True,
    )
    return df


# ============================================================================
# SEGMENTS
# ============================================================================

def segment_grade(df):
    """Default rate by loan grade (A-G)."""
    result = _seg(df, 'grade').sort_values('segment_value')
    logging.info(f"Grade segment: {len(result)} buckets")
    return result


def segment_term(df):
    """Default rate by loan term (36 vs 60 month)."""
    result = _seg(df, 'term')
    logging.info(f"Term segment: {len(result)} buckets")
    return result


def segment_purpose(df):
    """Default rate by loan purpose, ranked by default rate."""
    result = _seg(df, 'purpose').sort_values('default_rate', ascending=False)
    logging.info(f"Purpose segment: {len(result)} buckets")
    return result


def segment_home_ownership(df):
    """Default rate by home ownership status."""
    result = _seg(df, 'home_ownership').sort_values('default_rate', ascending=False)
    logging.info(f"Home ownership segment: {len(result)} buckets")
    return result


def segment_emp_length(df):
    """Default rate by employment length bucket."""
    result = _seg(df, 'emp_length_bucket')
    logging.info(f"Employment length segment: {len(result)} buckets")
    return result


def segment_dti(df):
    """Default rate by DTI bucket."""
    result = _seg(df, 'dti_bucket')
    logging.info(f"DTI segment: {len(result)} buckets")
    return result


def segment_loan_amount(df):
    """Default rate by loan amount bucket."""
    result = _seg(df, 'loan_amnt_bucket')
    logging.info(f"Loan amount segment: {len(result)} buckets")
    return result


def segment_crisis(df):
    """Default rate by grade cross-tabbed with crisis period flag."""
    result = (
        df.groupby(['grade', 'crisis_period'])['is_default']
        .agg(loan_count='count', default_count='sum', default_rate='mean')
        .reset_index()
    )
    logging.info(f"Crisis period cross-tab: {len(result)} rows")
    return result


# ============================================================================
# OUTPUT
# ============================================================================

def build_master_summary(segments):
    """Stack all single-dimension segments into one summary table."""
    return pd.concat(
        [s[['segment_type', 'segment_value', 'loan_count', 'default_count',
            'default_rate', 'avg_loan_amount', 'total_portfolio_value', 'avg_int_rate']]
         for s in segments],
        ignore_index=True,
    )


def save_outputs(summary, crisis, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    summary_path = os.path.join(output_dir, 'segment_summary.csv')
    summary.to_csv(summary_path, index=False)
    logging.info(f"Saved segment summary: {summary_path}")

    crisis_path = os.path.join(output_dir, 'crisis_crosstab.csv')
    crisis.to_csv(crisis_path, index=False)
    logging.info(f"Saved crisis cross-tab: {crisis_path}")

    for seg_type, group in summary.groupby('segment_type'):
        records = group[['segment_value', 'loan_count', 'default_count', 'default_rate',
                          'avg_loan_amount', 'total_portfolio_value', 'avg_int_rate']].to_dict(orient='records')
        path = os.path.join(output_dir, f'{seg_type}_breakdown.json')
        with open(path, 'w') as f:
            json.dump(records, f, indent=2, default=str)
    logging.info(f"Saved individual breakdown JSONs to {output_dir}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    df = pd.read_csv(INPUT_PATH)
    logging.info(f"Loaded {len(df):,} records, {len(df.columns)} columns")
    logging.info(f"Baseline default rate: {df['is_default'].mean():.2%}")

    df = _add_buckets(df)

    grade = segment_grade(df)
    term = segment_term(df)
    purpose = segment_purpose(df)
    home_ownership = segment_home_ownership(df)
    emp_length = segment_emp_length(df)
    dti = segment_dti(df)
    loan_amount = segment_loan_amount(df)
    crisis = segment_crisis(df)

    summary = build_master_summary([grade, term, purpose, home_ownership, emp_length, dti, loan_amount])
    logging.info(f"Master summary: {len(summary)} rows across {summary['segment_type'].nunique()} segment types")

    save_outputs(summary, crisis, OUTPUT_DIR)
    logging.info("Phase 2 complete.")


if __name__ == '__main__':
    main()
