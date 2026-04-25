"""
PHASE 3: Dollar Exposure Modeling
Lending Risk Intelligence Pipeline

Translates default probabilities into dollar risk figures.
Produces portfolio-level and segment-level expected loss for dashboard consumption.

Run after clean.py and segment.py.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)

# ============================================================================
# PATHS
# ============================================================================

INPUT_LOANS = 'stages/02-clean/output/lending_risk_cleaned.csv'
INPUT_SEGMENTS = 'stages/03-segment/output/segment_summary.csv'
OUTPUT_DIR = 'stages/04-exposure/output'

# ============================================================================
# CONSTANTS
# ============================================================================

RECOVERY_RATE = 0.70        # Industry historical average, unsecured consumer credit (2000-2020)
LOSS_GIVEN_DEFAULT = 1 - RECOVERY_RATE

ASSUMPTIONS = {
    'recovery_rate': RECOVERY_RATE,
    'loss_given_default': LOSS_GIVEN_DEFAULT,
    'source': 'Industry historical average for unsecured consumer credit (2000-2020)',
}

# Ordered bucket values for segments where sort order matters
BUCKET_ORDER = {
    'emp_length_bucket': ['0-1', '1-3', '3-5', '5-10'],
    'dti_bucket': ['0-10', '10-20', '20-30', '30-40', '40-50', '50+'],
    'loan_amnt_bucket': ['0-5k', '5k-10k', '10k-15k', '15k-20k', '20k+'],
}

# Segment types to export as individual JSON files
SEGMENT_JSON_EXPORTS = {
    'grade': 'grade_exposure.json',
    'term': 'term_exposure.json',
    'purpose': 'purpose_exposure.json',
    'home_ownership': 'home_ownership_exposure.json',
    'emp_length_bucket': 'employment_length_exposure.json',
    'dti_bucket': 'dti_exposure.json',
    'loan_amnt_bucket': 'loan_amount_exposure.json',
}


# ============================================================================
# LOAD
# ============================================================================

def load_data():
    df = pd.read_csv(INPUT_LOANS)
    segments = pd.read_csv(INPUT_SEGMENTS)
    logging.info(f"Loans loaded: {len(df):,}")
    logging.info(f"Portfolio value: ${df['loan_amnt'].sum():,.0f}")
    logging.info(f"Segment types: {sorted(segments['segment_type'].unique().tolist())}")
    return df, segments


# ============================================================================
# PORTFOLIO-LEVEL EXPOSURE
# ============================================================================

def compute_portfolio(df):
    portfolio_value = df['loan_amnt'].sum()
    portfolio_default_rate = df['is_default'].mean()
    portfolio_expected_loss = portfolio_value * portfolio_default_rate * LOSS_GIVEN_DEFAULT
    portfolio_loss_rate = portfolio_expected_loss / portfolio_value

    return {
        'portfolio_value': portfolio_value,
        'portfolio_default_rate': portfolio_default_rate,
        'portfolio_expected_loss': portfolio_expected_loss,
        'portfolio_loss_rate': portfolio_loss_rate,
    }


# ============================================================================
# SEGMENT-LEVEL EXPOSURE
# ============================================================================

def compute_segment_exposure(segments, segment_type, portfolio_expected_loss):
    sub = segments[segments['segment_type'] == segment_type].copy()
    sub['segment_expected_loss'] = sub['total_portfolio_value'] * sub['default_rate'] * LOSS_GIVEN_DEFAULT
    sub['loss_rate'] = sub['segment_expected_loss'] / sub['total_portfolio_value']
    sub['pct_of_portfolio_exposure'] = sub['segment_expected_loss'] / portfolio_expected_loss

    if segment_type in BUCKET_ORDER:
        order = BUCKET_ORDER[segment_type]
        sub['_sort'] = sub['segment_value'].map({v: i for i, v in enumerate(order)})
        sub = sub.sort_values('_sort').drop(columns='_sort')
    else:
        sub = sub.sort_values('segment_expected_loss', ascending=False)

    return sub.reset_index(drop=True)


def compute_all_segments(segments, portfolio_expected_loss):
    segment_types = segments['segment_type'].unique().tolist()
    return {
        stype: compute_segment_exposure(segments, stype, portfolio_expected_loss)
        for stype in segment_types
    }


# ============================================================================
# AT-RISK COHORTS
# ============================================================================

def compute_at_risk_cohorts(df, segments):
    performing = df[df['is_default'] == 0].copy()

    grade_rates = (
        segments[segments['segment_type'] == 'grade'][['segment_value', 'default_rate']]
        .rename(columns={'segment_value': 'grade', 'default_rate': 'grade_default_rate'})
    )
    performing = performing.merge(grade_rates, on='grade', how='left')
    performing['at_risk_exposure'] = performing['loan_amnt'] * performing['grade_default_rate'] * LOSS_GIVEN_DEFAULT

    cohorts = (
        performing.groupby(['grade', 'term'])
        .agg(
            loan_count=('loan_amnt', 'count'),
            total_value=('loan_amnt', 'sum'),
            at_risk_exposure=('at_risk_exposure', 'sum'),
        )
        .reset_index()
    )
    cohorts['loss_rate'] = cohorts['at_risk_exposure'] / cohorts['total_value']
    cohorts = cohorts.sort_values('at_risk_exposure', ascending=False).reset_index(drop=True)

    logging.info(f"Performing loans: {len(performing):,} ({len(performing)/len(df):.1%} of portfolio)")
    logging.info(f"Total at-risk exposure: ${cohorts['at_risk_exposure'].sum():,.0f}")

    return cohorts


# ============================================================================
# AUDIT
# ============================================================================

def run_audit(portfolio, segment_frames):
    grade = segment_frames['grade']
    term = segment_frames['term']

    checks = {
        'portfolio_el_lt_portfolio_value': (
            portfolio['portfolio_expected_loss'] < portfolio['portfolio_value']
        ),
        'portfolio_loss_rate_2_to_8pct': (
            0.02 <= portfolio['portfolio_loss_rate'] <= 0.08
        ),
        'grade_loss_rate_monotonic': (
            bool(grade.sort_values('segment_value')['loss_rate'].is_monotonic_increasing)
        ),
        'grade_pct_sums_to_approx_100': (
            abs(grade['pct_of_portfolio_exposure'].sum() - 1.0) < 0.10
        ),
        'term_pct_sums_to_approx_100': (
            abs(term['pct_of_portfolio_exposure'].sum() - 1.0) < 0.10
        ),
    }

    for name, passed in checks.items():
        status = 'PASS' if passed else 'FAIL'
        logging.info(f"Audit {status}: {name}")

    failures = [k for k, v in checks.items() if not v]
    if failures:
        raise ValueError(f"Audit failed: {failures}")


# ============================================================================
# OUTPUT
# ============================================================================

def _segment_frame_to_records(df):
    cols = [
        'segment_value', 'loan_count', 'total_portfolio_value',
        'default_rate', 'segment_expected_loss', 'loss_rate', 'pct_of_portfolio_exposure',
    ]
    return df[cols].to_dict(orient='records')


def write_portfolio_headline(portfolio):
    payload = {
        'portfolio_value_usd': portfolio['portfolio_value'],
        'portfolio_default_rate_pct': portfolio['portfolio_default_rate'],
        'expected_loss_usd': portfolio['portfolio_expected_loss'],
        'loss_rate_pct': portfolio['portfolio_loss_rate'],
        'metadata': {
            'generated': datetime.now().isoformat(),
            'sources': [INPUT_LOANS, INPUT_SEGMENTS],
            'assumptions': ASSUMPTIONS,
        },
    }
    path = os.path.join(OUTPUT_DIR, 'portfolio_headline.json')
    with open(path, 'w') as f:
        json.dump(payload, f, indent=2)
    logging.info(f"Written: {path}")


def write_segment_jsons(segment_frames):
    for segment_type, filename in SEGMENT_JSON_EXPORTS.items():
        if segment_type not in segment_frames:
            continue
        df = segment_frames[segment_type]
        payload = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'segment_type': segment_type,
                'total_segments': len(df),
                'assumptions': ASSUMPTIONS,
            },
            'segments': _segment_frame_to_records(df),
        }
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, 'w') as f:
            json.dump(payload, f, indent=2)
        logging.info(f"Written: {path}")


def write_exposure_summary(segment_frames):
    frames = []
    for segment_type, df in segment_frames.items():
        sub = df[['segment_value', 'loan_count', 'total_portfolio_value',
                  'default_rate', 'segment_expected_loss', 'loss_rate',
                  'pct_of_portfolio_exposure']].copy()
        sub.insert(0, 'segment_type', segment_type)
        frames.append(sub)

    summary = pd.concat(frames, ignore_index=True)
    path = os.path.join(OUTPUT_DIR, 'exposure_summary.csv')
    summary.to_csv(path, index=False)
    logging.info(f"Written: {path} ({len(summary)} rows)")


def write_at_risk_cohorts(cohorts):
    path = os.path.join(OUTPUT_DIR, 'at_risk_cohorts.csv')
    cohorts.to_csv(path, index=False)
    logging.info(f"Written: {path} ({len(cohorts)} cohorts)")


# ============================================================================
# MAIN
# ============================================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df, segments = load_data()

    portfolio = compute_portfolio(df)
    logging.info(
        f"Portfolio: ${portfolio['portfolio_value']:,.0f} value, "
        f"{portfolio['portfolio_default_rate']:.2%} default rate, "
        f"${portfolio['portfolio_expected_loss']:,.0f} expected loss, "
        f"{portfolio['portfolio_loss_rate']:.2%} loss rate"
    )

    segment_frames = compute_all_segments(segments, portfolio['portfolio_expected_loss'])

    run_audit(portfolio, segment_frames)

    cohorts = compute_at_risk_cohorts(df, segments)

    write_portfolio_headline(portfolio)
    write_segment_jsons(segment_frames)
    write_exposure_summary(segment_frames)
    write_at_risk_cohorts(cohorts)

    logging.info("Phase 3 complete.")


if __name__ == '__main__':
    main()
