import pandas as pd
from src.transformers.financial_metrics import apply_transformations


def test_apply_transformations_adds_columns():
    df = pd.read_csv('data/extracted_data_test.csv', parse_dates=['timestamp'])
    transformed = apply_transformations(df)
    assert 'daily_return' in transformed.columns
    assert 'sma_7' in transformed.columns
    assert pd.api.types.is_numeric_dtype(transformed['daily_return'])
    assert pd.api.types.is_numeric_dtype(transformed['sma_7'])
