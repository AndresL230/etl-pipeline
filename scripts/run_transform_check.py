import sys
import os
import pandas as pd

# Ensure the repository root is on sys.path so `src` can be imported when run as a script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.transformers.financial_metrics import apply_transformations


def main():
    sample_csv = "data/extracted_data_test.csv"

    try:
        df = pd.read_csv(sample_csv, parse_dates=["timestamp"])
    except Exception as e:
        print(f"Failed to read sample CSV: {e}")
        return 2

    try:
        transformed = apply_transformations(df)
    except Exception as e:
        print(f"Transformation failed: {e}")
        return 3

    # Basic checks
    if 'daily_return' not in transformed.columns:
        print("daily_return column missing")
        return 4
    if 'sma_7' not in transformed.columns:
        print("sma_7 column missing")
        return 5

    # Basic dtype checks
    if not pd.api.types.is_numeric_dtype(transformed['daily_return']):
        print("daily_return is not numeric")
        return 6
    if not pd.api.types.is_numeric_dtype(transformed['sma_7']):
        print("sma_7 is not numeric")
        return 7

    print("Transform checks passed")
    return 0


if __name__ == '__main__':
    code = main()
    sys.exit(code)
