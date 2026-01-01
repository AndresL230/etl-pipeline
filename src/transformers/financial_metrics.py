import pandas as pd
from typing import Optional

def compute_daily_returns(df: pd.DataFrame, price_col: str = 'close', metrics_collector=None) -> pd.DataFrame:
	"""Add a `daily_return` column computed from the `price_col` per symbol.

	Expects: df contains `symbol` and `timestamp` columns and a numeric price column.
	"""
	if df.empty:
		return df

	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)
	df['daily_return'] = df.groupby('symbol')[price_col].pct_change()

	if metrics_collector:
		metrics_collector.record_transformation('daily_returns')

	return df


def add_sma(df: pd.DataFrame, window: int = 7, price_col: str = 'close', metrics_collector=None) -> pd.DataFrame:
	"""Add a simple moving average column `sma_{window}` per symbol."""
	if df.empty:
		return df

	col_name = f'sma_{window}'
	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)
	df[col_name] = df.groupby('symbol')[price_col].transform(lambda s: s.rolling(window, min_periods=1).mean())

	if metrics_collector:
		metrics_collector.record_transformation(f'sma_{window}')

	return df


def apply_transformations(df: pd.DataFrame, metrics_collector=None) -> pd.DataFrame:
	"""Run a set of standard transformations and return the transformed DataFrame."""
	if df.empty:
		return df

	if metrics_collector:
		metrics_collector.start_transformation(len(df))

	df = compute_daily_returns(df, metrics_collector=metrics_collector)
	df = add_sma(df, window=7, metrics_collector=metrics_collector)

	if metrics_collector:
		null_count = df['daily_return'].isna().sum()
		metrics_collector.end_transformation(len(df), null_values=null_count)

	return df

__all__ = ["compute_daily_returns", "add_sma", "apply_transformations"]
