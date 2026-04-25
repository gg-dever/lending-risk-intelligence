"""
Interest Rate Prediction Model
Lending Risk Intelligence Pipeline

Predicts loan interest rates using origination-time borrower and loan features.
Produces a fitted sklearn Pipeline, feature importances, and evaluation metrics.

Model: HistGradientBoostingRegressor with 15 features (13 numeric/binary + purpose
and home_ownership label-encoded). This is the best model found after a 20-iteration
RandomizedSearchCV in the notebook (Test R2 = 0.5069, MAE = 0.0254 pp), outperforming
the OLS baseline by +9.4pp R2. Purpose and home_ownership were excluded from the
linear model due to structural VIF inflation (50-59 range) from dominant categories.
That constraint does not apply to tree models, which split on raw values and are
immune to multicollinearity.

Run after clean.py.
"""

import json
import logging
import os
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(message)s',
    datefmt='%H:%M:%S'
)

log = logging.getLogger(__name__)

# ============================================================================
# PATHS
# ============================================================================

INPUT_PATH = 'stages/02-clean/output/lending_risk_cleaned.csv'

# ============================================================================
# CONSTANTS
# ============================================================================

# Features excluded because they are unavailable at origination time or are
# mathematically derived from the target variable (installment = f(int_rate)).
LEAKERS = [
    'is_default',
    'grade',        # assigned by LendingClub based on int_rate
    'sub_grade',    # same
    'installment',  # computed directly from int_rate, loan_amnt, and term
    'segment_type',
    'segment_value',
]

# 12 numeric origination features. HGB handles NaN natively so no imputer needed.
NUMERIC_FEATURES = [
    'loan_amnt',
    'annual_inc',
    'dti',
    'fico_score',
    'fico_score_sq',   # centered quadratic FICO: (fico - mean)^2 — keeps VIF < 2.5
    'inq_last_6mths',
    'open_acc',
    'pub_rec',
    'revol_bal',
    'revol_util',
    'total_acc',
    'delinq_2yrs',
]

# Binary flag — 60-month loans carry higher rates than 36-month loans.
BINARY_FEATURES = ['is_60mo']

# Categorical features excluded from the linear model due to structural VIF
# inflation (50-59). Tree models are immune to multicollinearity so they are
# included here via OrdinalEncoder.
CATEGORICAL_FEATURES = ['purpose', 'home_ownership']

FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES

# Best hyperparameters from 20-iteration RandomizedSearchCV in the notebook.
HGB_PARAMS = {
    'max_iter':          300,
    'max_depth':         5,
    'learning_rate':     0.05,
    'l2_regularization': 0.1,
    'min_samples_leaf':  20,
    'random_state':      42,
}
TARGET   = 'int_rate'

CRISIS_CUTOFF = 2009   # exclude pre-crisis originations
TEST_SIZE     = 0.10
RANDOM_STATE  = 42

# ============================================================================
# FUNCTIONS
# ============================================================================


def load_data(path: str = INPUT_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """Load cleaned CSV, filter to post-crisis originations, engineer features,
    and return (X, y) on raw (unstandardized) values.

    The Pipeline's ColumnTransformer handles standardization internally so the
    scaler is fit only on training data which means no leakage from the test set.
    """
    log.info('Loading %s', path)
    df = pd.read_csv(path)

    if 'issue_d' in df.columns:
        df['year'] = pd.to_datetime(df['issue_d'], errors='coerce').dt.year
        df = df[df['year'] >= CRISIS_CUTOFF].copy()

    log.info('Rows after crisis filter: %s', f'{len(df):,}')

    # — Feature engineering —
    df['fico_score'] = (df['fico_range_low'] + df['fico_range_high']) / 2

    # Center before squaring so fico_score and fico_score_sq stay nearly
    # orthogonal (raw squaring of ~700 would push VIF to ~1057).
    fico_mean = df['fico_score'].mean()
    df['fico_score_sq'] = (df['fico_score'] - fico_mean) ** 2

    df['is_60mo'] = (
        df['term'].astype(str).str.strip().str.startswith('60').astype(int)
    )

    y = df[TARGET].copy()
    drop_cols = [c for c in LEAKERS if c in df.columns] + [TARGET]
    X = df.drop(columns=drop_cols, errors='ignore')[FEATURES].copy()

    # Drop rows where the target is missing — can't impute the label.
    # Numeric feature NaNs are handled natively by HGB.
    # Categorical NaNs are filled with a sentinel so OrdinalEncoder sees a
    # consistent vocabulary at fit and predict time.
    X['purpose']        = X['purpose'].fillna('other')
    X['home_ownership'] = X['home_ownership'].fillna('OTHER')

    mask = y.notna()
    X, y = X[mask], y[mask]

    log.info('Features: %s', FEATURES)
    return X, y


def build_pipeline() -> Pipeline:
    """Return an unfitted sklearn Pipeline:
      1. ColumnTransformer:
           - numeric + binary features: passthrough (HGB handles NaN natively,
             no scaling needed for tree models)
           - categorical features: OrdinalEncoder (converts string categories to
             integers; unknown categories at predict time map to -1)
      2. HistGradientBoostingRegressor with params from notebook grid search
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ('numeric',      'passthrough', NUMERIC_FEATURES),
            ('binary',       'passthrough', BINARY_FEATURES),
            ('categorical',  OrdinalEncoder(
                handle_unknown='use_encoded_value',
                unknown_value=-1,
            ), CATEGORICAL_FEATURES),
        ],
        remainder='drop',
    )

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor',    HistGradientBoostingRegressor(**HGB_PARAMS)),
    ])

    return pipeline


def evaluate(pipeline: Pipeline, X_train, X_test, y_train, y_test) -> dict:
    """Return a dict of train/test R², MAE, and RMSE."""
    y_pred_train = pipeline.predict(X_train)
    y_pred_test  = pipeline.predict(X_test)

    return {
        'train_r2':   r2_score(y_train, y_pred_train),
        'test_r2':    r2_score(y_test,  y_pred_test),
        'train_mae':  mean_absolute_error(y_train, y_pred_train),
        'test_mae':   mean_absolute_error(y_test,  y_pred_test),
        'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
        'test_rmse':  np.sqrt(mean_squared_error(y_test,  y_pred_test)),
    }


def feature_importance_table(pipeline: Pipeline, X_test, y_test,
                              n_repeats: int = 5, sample_n: int = 10_000) -> pd.DataFrame:
    """Return a DataFrame of permutation importances (mean decrease in R² when
    a feature is randomly shuffled), computed on a sample of the test set.
    Sorted descending by mean importance.
    """
    rng = np.random.RandomState(42)
    idx = rng.choice(len(X_test), size=min(sample_n, len(X_test)), replace=False)
    X_sample = X_test.iloc[idx]
    y_sample = y_test.iloc[idx]

    result = permutation_importance(
        pipeline, X_sample, y_sample,
        n_repeats=n_repeats, random_state=42, scoring='r2',
    )
    imp_df = pd.DataFrame({
        'feature':   FEATURES,
        'importance_mean': result.importances_mean,
        'importance_std':  result.importances_std,
    })
    imp_df = imp_df.sort_values('importance_mean', ascending=False).reset_index(drop=True)
    return imp_df


# ============================================================================
# MAIN
# ============================================================================


def serialize_tree(tree) -> list[dict]:
    """Convert a sklearn TreePredictor into a compact JSON-friendly structure."""
    nodes = []
    for node in tree.nodes:
        nodes.append({
            'f': int(node['feature_idx']),
            't': None if bool(node['is_leaf']) else float(node['num_threshold']),
            'l': int(node['left']),
            'r': int(node['right']),
            'm': bool(node['missing_go_to_left']),
            'leaf': bool(node['is_leaf']),
            'v': float(node['value']),
        })
    return nodes


def export_dashboard_model(pipeline: Pipeline, X_reference: pd.DataFrame,
                           metrics: dict, out_path: str) -> None:
    """Export the fitted HGB model so the dashboard can score inputs in-browser."""
    preprocessor = pipeline.named_steps['preprocessor']
    regressor = pipeline.named_steps['regressor']
    encoder = preprocessor.named_transformers_['categorical']

    defaults = {
        'loan_amnt': float(X_reference['loan_amnt'].median()),
        'annual_inc': float(X_reference['annual_inc'].median()),
        'dti': float(X_reference['dti'].median()),
        'fico_score': float(X_reference['fico_score'].median()),
        'inq_last_6mths': float(X_reference['inq_last_6mths'].median()),
        'open_acc': float(X_reference['open_acc'].median()),
        'pub_rec': float(X_reference['pub_rec'].median()),
        'revol_bal': float(X_reference['revol_bal'].median()),
        'revol_util': float(X_reference['revol_util'].median()),
        'total_acc': float(X_reference['total_acc'].median()),
        'delinq_2yrs': float(X_reference['delinq_2yrs'].median()),
        'is_60mo': int(round(X_reference['is_60mo'].median())),
        'purpose': str(X_reference['purpose'].mode().iloc[0]),
        'home_ownership': str(X_reference['home_ownership'].mode().iloc[0]),
    }

    feature_bounds = {}
    for feature in NUMERIC_FEATURES:
        series = X_reference[feature].astype(float)
        feature_bounds[feature] = {
            'low': float(series.quantile(0.01)),
            'high': float(series.quantile(0.99)),
            'min': float(series.min()),
            'max': float(series.max()),
        }

    feature_bounds['is_60mo'] = {
        'low': 0.0,
        'high': 1.0,
        'min': 0.0,
        'max': 1.0,
    }

    payload = {
        'baseline_prediction': float(np.ravel(regressor._baseline_prediction)[0]),
        'features': NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES,
        'numeric_features': NUMERIC_FEATURES,
        'binary_features': BINARY_FEATURES,
        'categorical_features': CATEGORICAL_FEATURES,
        'categorical_levels': {
            'purpose': [str(v) for v in encoder.categories_[0]],
            'home_ownership': [str(v) for v in encoder.categories_[1]],
        },
        'defaults': defaults,
        'feature_bounds': feature_bounds,
        'fico_center': float(X_reference['fico_score'].mean()),
        'metrics': {
            'test_rmse': float(metrics['test_rmse']),
            'test_mae': float(metrics['test_mae']),
            'test_r2': float(metrics['test_r2']),
        },
        'manual_options': {
            'purpose': [
                {'label': 'Credit Card', 'value': 'credit_card'},
                {'label': 'Debt Consolidation', 'value': 'debt_consolidation'},
                {'label': 'Home Improvement', 'value': 'home_improvement'},
                {'label': 'Major Purchase', 'value': 'major_purchase'},
                {'label': 'Small Business', 'value': 'small_business'},
            ],
            'home_ownership': [
                {'label': 'Rent', 'value': 'RENT'},
                {'label': 'Mortgage', 'value': 'MORTGAGE'},
                {'label': 'Own', 'value': 'OWN'},
            ],
        },
        'trees': [serialize_tree(predictors[0]) for predictors in regressor._predictors],
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as file_handle:
        json.dump(payload, file_handle, separators=(',', ':'))


def main():
    X, y = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    log.info('Train: %s rows  |  Test: %s rows', f'{len(X_train):,}', f'{len(X_test):,}')

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    log.info('Pipeline fitted')

    metrics = evaluate(pipeline, X_train, X_test, y_train, y_test)
    log.info('Computing permutation importances (10K sample, 5 repeats)...')
    importances = feature_importance_table(pipeline, X_test, y_test)

    shrinkage_bps = (metrics['train_r2'] - metrics['test_r2']) * 10_000

    print('\nModel Performance')
    print(f"  Train R2:    {metrics['train_r2']:.4f}")
    print(f"  Test  R2:    {metrics['test_r2']:.4f}  (shrinkage: {shrinkage_bps:.1f} bps)")
    print(f"  Train MAE:   {metrics['train_mae']:.4f} pp")
    print(f"  Test  MAE:   {metrics['test_mae']:.4f} pp")
    print(f"  Train RMSE:  {metrics['train_rmse']:.4f} pp")
    print(f"  Test  RMSE:  {metrics['test_rmse']:.4f} pp")

    print('\nFeature Importances (permutation, R2 decrease)')
    print(importances.to_string(index=False))

    out_dir = 'stages/05-model/output'
    os.makedirs(out_dir, exist_ok=True)

    perf_out = {
        'train_r2': round(metrics['train_r2'], 4),
        'test_r2': round(metrics['test_r2'], 4),
        'train_mae': round(metrics['train_mae'], 4),
        'test_mae': round(metrics['test_mae'], 4),
        'train_rmse': round(metrics['train_rmse'], 4),
        'test_rmse': round(metrics['test_rmse'], 4),
        'shrinkage_bps': round(shrinkage_bps, 2),
        'sample_size': len(X_train) + len(X_test),
        'feature_count': len(FEATURES),
    }
    with open(f'{out_dir}/model_performance.json', 'w') as file_handle:
        json.dump(perf_out, file_handle, indent=2)

    imp_out = importances[['feature', 'importance_mean', 'importance_std']].to_dict(orient='records')
    with open(f'{out_dir}/feature_importance.json', 'w') as file_handle:
        json.dump(imp_out, file_handle, indent=2)

    export_dashboard_model(
        pipeline,
        X,
        metrics,
        'dashboard/data/hgb_rate_model.json',
    )

    log.info('Outputs written to %s and dashboard/data', out_dir)
    return pipeline, metrics, importances


if __name__ == '__main__':
    main()
