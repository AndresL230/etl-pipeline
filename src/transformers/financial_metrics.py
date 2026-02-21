import pandas as pd
import numpy as np
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


def add_ema(df: pd.DataFrame, window: int = 12, price_col: str = 'close', metrics_collector=None) -> pd.DataFrame:
	"""Add an exponential moving average column `ema_{window}` per symbol."""
	if df.empty:
		return df

	col_name = f'ema_{window}'
	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)
	df[col_name] = df.groupby('symbol')[price_col].transform(lambda s: s.ewm(span=window, adjust=False).mean())

	if metrics_collector:
		metrics_collector.record_transformation(f'ema_{window}')

	return df


def compute_rsi(df: pd.DataFrame, window: int = 14, price_col: str = 'close', metrics_collector=None) -> pd.DataFrame:
	"""Add RSI (Relative Strength Index) column per symbol.

	RSI is a momentum oscillator that measures the speed and magnitude of price changes.
	Values range from 0 to 100, with >70 indicating overbought and <30 indicating oversold.
	"""
	if df.empty:
		return df

	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)

	def calculate_rsi(series):
		delta = series.diff()
		gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
		loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

		rs = gain / loss
		rsi = 100 - (100 / (1 + rs))
		return rsi

	df['rsi'] = df.groupby('symbol')[price_col].transform(calculate_rsi)

	if metrics_collector:
		metrics_collector.record_transformation('rsi')

	return df


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0, price_col: str = 'close', metrics_collector=None) -> pd.DataFrame:
	"""Add Bollinger Bands (upper, middle, lower) per symbol.

	Bollinger Bands are volatility bands placed above and below a moving average.
	They widen during increased volatility and contract during decreased volatility.
	"""
	if df.empty:
		return df

	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)

	def calculate_bollinger(series):
		sma = series.rolling(window=window, min_periods=1).mean()
		std = series.rolling(window=window, min_periods=1).std()
		upper = sma + (std * num_std)
		lower = sma - (std * num_std)
		return pd.DataFrame({'middle': sma, 'upper': upper, 'lower': lower})

	# Apply Bollinger Bands calculation per symbol
	bollinger = df.groupby('symbol')[price_col].apply(calculate_bollinger).reset_index(level=0, drop=True)

	df['bb_middle'] = bollinger['middle'].values
	df['bb_upper'] = bollinger['upper'].values
	df['bb_lower'] = bollinger['lower'].values

	if metrics_collector:
		metrics_collector.record_transformation('bollinger_bands')

	return df


def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, price_col: str = 'close', metrics_collector=None) -> pd.DataFrame:
	"""Add MACD (Moving Average Convergence Divergence) indicators per symbol.

	MACD is a trend-following momentum indicator showing the relationship between two EMAs.
	- MACD Line: Fast EMA - Slow EMA
	- Signal Line: 9-day EMA of MACD Line
	- Histogram: MACD Line - Signal Line
	"""
	if df.empty:
		return df

	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)

	def calculate_macd(series):
		ema_fast = series.ewm(span=fast, adjust=False).mean()
		ema_slow = series.ewm(span=slow, adjust=False).mean()
		macd_line = ema_fast - ema_slow
		signal_line = macd_line.ewm(span=signal, adjust=False).mean()
		histogram = macd_line - signal_line

		return pd.DataFrame({
			'macd': macd_line,
			'macd_signal': signal_line,
			'macd_histogram': histogram
		})

	macd = df.groupby('symbol')[price_col].apply(calculate_macd).reset_index(level=0, drop=True)

	df['macd'] = macd['macd'].values
	df['macd_signal'] = macd['macd_signal'].values
	df['macd_histogram'] = macd['macd_histogram'].values

	if metrics_collector:
		metrics_collector.record_transformation('macd')

	return df


def add_volatility(df: pd.DataFrame, window: int = 20, price_col: str = 'close', metrics_collector=None) -> pd.DataFrame:
	"""Add rolling volatility (standard deviation of returns) per symbol."""
	if df.empty:
		return df

	df = df.copy()
	df.sort_values(['symbol', 'timestamp'], inplace=True)

	# Ensure daily_return exists
	if 'daily_return' not in df.columns:
		df['daily_return'] = df.groupby('symbol')[price_col].pct_change()

	df[f'volatility_{window}'] = df.groupby('symbol')['daily_return'].transform(
		lambda s: s.rolling(window=window, min_periods=1).std()
	)

	if metrics_collector:
		metrics_collector.record_transformation(f'volatility_{window}')

	return df


def apply_transformations(df: pd.DataFrame, metrics_collector=None, include_advanced: bool = False) -> pd.DataFrame:
	"""Run a set of standard transformations and return the transformed DataFrame.

	Args:
		df: Input DataFrame with stock price data
		metrics_collector: Optional metrics collector for tracking
		include_advanced: If True, include advanced indicators (RSI, MACD, Bollinger Bands)
	"""
	if df.empty:
		return df

	if metrics_collector:
		metrics_collector.start_transformation(len(df))

	# Basic transformations
	df = compute_daily_returns(df, metrics_collector=metrics_collector)
	df = add_sma(df, window=7, metrics_collector=metrics_collector)
	df = add_sma(df, window=20, metrics_collector=metrics_collector)
	df = add_sma(df, window=50, metrics_collector=metrics_collector)

	# Advanced transformations
	if include_advanced:
		df = add_ema(df, window=12, metrics_collector=metrics_collector)
		df = add_ema(df, window=26, metrics_collector=metrics_collector)
		df = compute_rsi(df, window=14, metrics_collector=metrics_collector)
		df = add_bollinger_bands(df, window=20, metrics_collector=metrics_collector)
		df = compute_macd(df, metrics_collector=metrics_collector)
		df = add_volatility(df, window=20, metrics_collector=metrics_collector)

	if metrics_collector:
		null_count = df['daily_return'].isna().sum()
		metrics_collector.end_transformation(len(df), null_values=null_count)

	return df


__all__ = [
	"compute_daily_returns",
	"add_sma",
	"add_ema",
	"compute_rsi",
	"add_bollinger_bands",
	"compute_macd",
	"add_volatility",
	"apply_transformations"
]
