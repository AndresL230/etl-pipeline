import pandas as pd

def compute_daily_returns(df: pd.DataFrame, price_col: str = 'close') -> pd.DataFrame:
	"""Add a `daily_return` column computed from the `price_col` per symbol.

	Expects: df contains `symbol` and `timestamp` columns and a numeric price column.
	"""
	if df.empty:
		return df

	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)
	df['daily_return'] = df.groupby('symbol')[price_col].pct_change()
	return df


def add_sma(df: pd.DataFrame, window: int = 7, price_col: str = 'close') -> pd.DataFrame:
	"""Add a simple moving average column `sma_{window}` per symbol."""
	if df.empty:
		return df

	col_name = f'sma_{window}'
	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)
	df[col_name] = df.groupby('symbol')[price_col].transform(lambda s: s.rolling(window, min_periods=1).mean())
	return df


def apply_transformations(df: pd.DataFrame) -> pd.DataFrame:
	"""Run a set of standard transformations and return the transformed DataFrame."""
	if df.empty:
		return df

	df = compute_daily_returns(df)
	df = add_sma(df, window=7)
	return df

__all__ = ["compute_daily_returns", "add_sma", "apply_transformations"]
