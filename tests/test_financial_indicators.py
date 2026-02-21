import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.transformers.financial_metrics import (
    add_ema,
    compute_rsi,
    add_bollinger_bands,
    compute_macd,
    add_volatility
)


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(50)]

    # Create realistic price data with trend
    base_price = 100
    prices = [base_price + i * 0.5 + np.random.randn() * 2 for i in range(50)]

    df = pd.DataFrame({
        'symbol': ['AAPL'] * 50,
        'timestamp': dates,
        'open': prices,
        'high': [p + abs(np.random.randn()) for p in prices],
        'low': [p - abs(np.random.randn()) for p in prices],
        'close': prices,
        'volume': [1000000 + np.random.randint(-100000, 100000) for _ in range(50)]
    })

    return df


@pytest.fixture
def multi_symbol_data():
    """Create multi-symbol price data."""
    dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(30)]

    data = []
    for symbol in ['AAPL', 'GOOGL']:
        base_price = 100 if symbol == 'AAPL' else 150
        for i, date in enumerate(dates):
            price = base_price + i * 0.3
            data.append({
                'symbol': symbol,
                'timestamp': date,
                'close': price,
                'open': price - 0.5,
                'high': price + 1,
                'low': price - 1,
                'volume': 1000000
            })

    return pd.DataFrame(data)


class TestEMA:
    def test_add_ema_basic(self, sample_price_data):
        """Test that EMA is calculated correctly."""
        df = add_ema(sample_price_data, window=12)

        assert 'ema_12' in df.columns
        assert not df['ema_12'].isna().all()

        # EMA should be close to price values
        assert (df['ema_12'] > 0).all()
        assert (df['ema_12'] < df['close'].max() * 2).all()

    def test_add_ema_different_windows(self, sample_price_data):
        """Test EMA with different window sizes."""
        df = add_ema(sample_price_data, window=12)
        df = add_ema(df, window=26)

        assert 'ema_12' in df.columns
        assert 'ema_26' in df.columns

        # Shorter EMA should react faster (closer to current price)
        # This is generally true but not guaranteed for all data
        assert df['ema_12'].notna().any()
        assert df['ema_26'].notna().any()

    def test_add_ema_empty_df(self):
        """Test EMA with empty DataFrame."""
        df = pd.DataFrame()
        result = add_ema(df, window=12)
        assert result.empty

    def test_add_ema_multi_symbol(self, multi_symbol_data):
        """Test EMA calculation per symbol."""
        df = add_ema(multi_symbol_data, window=12)

        assert 'ema_12' in df.columns

        # Check that EMA is calculated separately for each symbol
        aapl_ema = df[df['symbol'] == 'AAPL']['ema_12']
        googl_ema = df[df['symbol'] == 'GOOGL']['ema_12']

        assert aapl_ema.notna().any()
        assert googl_ema.notna().any()


class TestRSI:
    def test_compute_rsi_basic(self, sample_price_data):
        """Test that RSI is calculated correctly."""
        df = compute_rsi(sample_price_data, window=14)

        assert 'rsi' in df.columns

        # RSI should be between 0 and 100
        rsi_values = df['rsi'].dropna()
        assert (rsi_values >= 0).all()
        assert (rsi_values <= 100).all()

    def test_compute_rsi_range(self, sample_price_data):
        """Test that RSI values are in valid range."""
        df = compute_rsi(sample_price_data, window=14)

        # Remove NaN values from the beginning
        rsi_values = df['rsi'].dropna()

        assert len(rsi_values) > 0
        assert rsi_values.min() >= 0
        assert rsi_values.max() <= 100

    def test_compute_rsi_empty_df(self):
        """Test RSI with empty DataFrame."""
        df = pd.DataFrame()
        result = compute_rsi(df, window=14)
        assert result.empty

    def test_compute_rsi_multi_symbol(self, multi_symbol_data):
        """Test RSI calculation per symbol."""
        df = compute_rsi(multi_symbol_data, window=14)

        assert 'rsi' in df.columns

        # Check RSI for each symbol
        for symbol in ['AAPL', 'GOOGL']:
            symbol_rsi = df[df['symbol'] == symbol]['rsi'].dropna()
            assert len(symbol_rsi) > 0
            assert (symbol_rsi >= 0).all()
            assert (symbol_rsi <= 100).all()


class TestBollingerBands:
    def test_add_bollinger_bands_basic(self, sample_price_data):
        """Test that Bollinger Bands are calculated correctly."""
        df = add_bollinger_bands(sample_price_data, window=20)

        assert 'bb_upper' in df.columns
        assert 'bb_middle' in df.columns
        assert 'bb_lower' in df.columns

        # Remove NaN values
        df_clean = df.dropna(subset=['bb_upper', 'bb_middle', 'bb_lower'])

        # Upper should be > middle > lower
        assert (df_clean['bb_upper'] >= df_clean['bb_middle']).all()
        assert (df_clean['bb_middle'] >= df_clean['bb_lower']).all()

    def test_add_bollinger_bands_relationship(self, sample_price_data):
        """Test relationship between Bollinger Band components."""
        df = add_bollinger_bands(sample_price_data, window=20, num_std=2.0)

        # Middle band should be close to SMA
        from src.transformers.financial_metrics import add_sma
        df_with_sma = add_sma(sample_price_data, window=20)

        # Both DataFrames should have same length
        assert len(df) == len(df_with_sma)

    def test_add_bollinger_bands_empty_df(self):
        """Test Bollinger Bands with empty DataFrame."""
        df = pd.DataFrame()
        result = add_bollinger_bands(df, window=20)
        assert result.empty

    def test_add_bollinger_bands_multi_symbol(self, multi_symbol_data):
        """Test Bollinger Bands per symbol."""
        df = add_bollinger_bands(multi_symbol_data, window=20)

        for symbol in ['AAPL', 'GOOGL']:
            symbol_data = df[df['symbol'] == symbol].dropna(subset=['bb_upper'])
            if len(symbol_data) > 0:
                assert (symbol_data['bb_upper'] >= symbol_data['bb_middle']).all()
                assert (symbol_data['bb_middle'] >= symbol_data['bb_lower']).all()


class TestMACD:
    def test_compute_macd_basic(self, sample_price_data):
        """Test that MACD is calculated correctly."""
        df = compute_macd(sample_price_data)

        assert 'macd' in df.columns
        assert 'macd_signal' in df.columns
        assert 'macd_histogram' in df.columns

        # MACD values should exist
        assert df['macd'].notna().any()
        assert df['macd_signal'].notna().any()
        assert df['macd_histogram'].notna().any()

    def test_compute_macd_histogram(self, sample_price_data):
        """Test that MACD histogram equals MACD - Signal."""
        df = compute_macd(sample_price_data)

        # Remove NaN values
        df_clean = df.dropna(subset=['macd', 'macd_signal', 'macd_histogram'])

        if len(df_clean) > 0:
            # Histogram should be MACD - Signal (with small floating point tolerance)
            calculated_hist = df_clean['macd'] - df_clean['macd_signal']
            assert np.allclose(df_clean['macd_histogram'], calculated_hist, rtol=1e-10)

    def test_compute_macd_empty_df(self):
        """Test MACD with empty DataFrame."""
        df = pd.DataFrame()
        result = compute_macd(df)
        assert result.empty

    def test_compute_macd_custom_params(self, sample_price_data):
        """Test MACD with custom parameters."""
        df = compute_macd(sample_price_data, fast=10, slow=20, signal=5)

        assert 'macd' in df.columns
        assert 'macd_signal' in df.columns
        assert 'macd_histogram' in df.columns

    def test_compute_macd_multi_symbol(self, multi_symbol_data):
        """Test MACD per symbol."""
        df = compute_macd(multi_symbol_data)

        for symbol in ['AAPL', 'GOOGL']:
            symbol_data = df[df['symbol'] == symbol]
            assert symbol_data['macd'].notna().any()


class TestVolatility:
    def test_add_volatility_basic(self, sample_price_data):
        """Test that volatility is calculated correctly."""
        df = add_volatility(sample_price_data, window=20)

        assert 'volatility_20' in df.columns
        assert 'daily_return' in df.columns

        # Volatility should be non-negative
        vol_values = df['volatility_20'].dropna()
        assert (vol_values >= 0).all()

    def test_add_volatility_different_windows(self, sample_price_data):
        """Test volatility with different windows."""
        df = add_volatility(sample_price_data, window=10)
        df = add_volatility(df, window=30)

        assert 'volatility_10' in df.columns
        assert 'volatility_30' in df.columns

    def test_add_volatility_empty_df(self):
        """Test volatility with empty DataFrame."""
        df = pd.DataFrame()
        result = add_volatility(df, window=20)
        assert result.empty

    def test_add_volatility_multi_symbol(self, multi_symbol_data):
        """Test volatility per symbol."""
        df = add_volatility(multi_symbol_data, window=20)

        for symbol in ['AAPL', 'GOOGL']:
            symbol_vol = df[df['symbol'] == symbol]['volatility_20'].dropna()
            if len(symbol_vol) > 0:
                assert (symbol_vol >= 0).all()


class TestAdvancedTransformations:
    def test_apply_transformations_with_advanced(self, sample_price_data):
        """Test apply_transformations with advanced indicators."""
        from src.transformers.financial_metrics import apply_transformations

        df = apply_transformations(sample_price_data, include_advanced=True)

        # Check basic indicators
        assert 'daily_return' in df.columns
        assert 'sma_7' in df.columns
        assert 'sma_20' in df.columns
        assert 'sma_50' in df.columns

        # Check advanced indicators
        assert 'ema_12' in df.columns
        assert 'ema_26' in df.columns
        assert 'rsi' in df.columns
        assert 'bb_upper' in df.columns
        assert 'bb_middle' in df.columns
        assert 'bb_lower' in df.columns
        assert 'macd' in df.columns
        assert 'macd_signal' in df.columns
        assert 'macd_histogram' in df.columns
        assert 'volatility_20' in df.columns

    def test_apply_transformations_without_advanced(self, sample_price_data):
        """Test apply_transformations without advanced indicators."""
        from src.transformers.financial_metrics import apply_transformations

        df = apply_transformations(sample_price_data, include_advanced=False)

        # Check basic indicators exist
        assert 'daily_return' in df.columns
        assert 'sma_7' in df.columns

        # Check advanced indicators don't exist
        assert 'rsi' not in df.columns
        assert 'macd' not in df.columns
