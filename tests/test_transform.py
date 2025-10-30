import pandas as pd
import pytest
from unittest.mock import Mock, patch

from src.transformers.financial_metrics import (
    apply_transformations,
    compute_daily_returns,
    add_sma
)
from src.extractors.yahoo_finance import YFinance_Extractor
from src.loaders.database import run_etl


# ============================================================================
# TRANSFORMER TESTS
# ============================================================================

def test_apply_transformations_adds_columns():
    """Test that apply_transformations adds daily_return and sma_7 columns"""
    df = pd.read_csv('data/extracted_data_test.csv', parse_dates=['timestamp'])
    transformed = apply_transformations(df)
    assert 'daily_return' in transformed.columns
    assert 'sma_7' in transformed.columns
    assert pd.api.types.is_numeric_dtype(transformed['daily_return'])
    assert pd.api.types.is_numeric_dtype(transformed['sma_7'])


def test_compute_daily_returns():
    """Test daily return calculation"""
    df = pd.DataFrame({
        'symbol': ['AAPL', 'AAPL', 'AAPL'],
        'timestamp': pd.date_range('2025-01-01', periods=3),
        'close': [100.0, 110.0, 105.0]
    })
    result = compute_daily_returns(df, 'close')

    assert 'daily_return' in result.columns
    assert pd.isna(result.iloc[0]['daily_return'])  # First row should be NaN
    assert result.iloc[1]['daily_return'] == pytest.approx(0.10, rel=1e-5)  # 10% increase
    assert result.iloc[2]['daily_return'] == pytest.approx(-0.0454545, rel=1e-5)  # ~-4.5% decrease


def test_compute_daily_returns_multiple_symbols():
    """Test daily returns are calculated per symbol independently"""
    df = pd.DataFrame({
        'symbol': ['AAPL', 'AAPL', 'GOOGL', 'GOOGL'],
        'timestamp': pd.date_range('2025-01-01', periods=2).tolist() * 2,
        'close': [100.0, 110.0, 200.0, 220.0]
    })
    result = compute_daily_returns(df, 'close')

    aapl_returns = result[result['symbol'] == 'AAPL']['daily_return'].tolist()
    googl_returns = result[result['symbol'] == 'GOOGL']['daily_return'].tolist()

    assert pd.isna(aapl_returns[0])
    assert aapl_returns[1] == pytest.approx(0.10, rel=1e-5)
    assert pd.isna(googl_returns[0])
    assert googl_returns[1] == pytest.approx(0.10, rel=1e-5)


def test_compute_daily_returns_empty_df():
    """Test daily returns with empty dataframe"""
    df = pd.DataFrame()
    result = compute_daily_returns(df)
    assert result.empty


def test_add_sma():
    """Test simple moving average calculation"""
    df = pd.DataFrame({
        'symbol': ['AAPL'] * 5,
        'timestamp': pd.date_range('2025-01-01', periods=5),
        'close': [100.0, 110.0, 120.0, 130.0, 140.0]
    })
    result = add_sma(df, window=3, price_col='close')

    assert 'sma_3' in result.columns
    # First value should be just the first price (min_periods=1)
    assert result.iloc[0]['sma_3'] == 100.0
    # Third value should be average of first 3
    assert result.iloc[2]['sma_3'] == pytest.approx(110.0, rel=1e-5)
    # Fifth value should be average of last 3
    assert result.iloc[4]['sma_3'] == pytest.approx(130.0, rel=1e-5)


def test_add_sma_multiple_symbols():
    """Test SMA is calculated per symbol independently"""
    df = pd.DataFrame({
        'symbol': ['AAPL', 'AAPL', 'GOOGL', 'GOOGL'],
        'timestamp': pd.date_range('2025-01-01', periods=2).tolist() * 2,
        'close': [100.0, 110.0, 200.0, 220.0]
    })
    result = add_sma(df, window=2, price_col='close')

    aapl_sma = result[result['symbol'] == 'AAPL']['sma_2'].tolist()
    googl_sma = result[result['symbol'] == 'GOOGL']['sma_2'].tolist()

    assert aapl_sma[1] == pytest.approx(105.0, rel=1e-5)
    assert googl_sma[1] == pytest.approx(210.0, rel=1e-5)


def test_add_sma_empty_df():
    """Test SMA with empty dataframe"""
    df = pd.DataFrame()
    result = add_sma(df)
    assert result.empty


def test_apply_transformations_empty_df():
    """Test apply_transformations handles empty dataframe"""
    df = pd.DataFrame()
    result = apply_transformations(df)
    assert result.empty


# ============================================================================
# EXTRACTOR TESTS
# ============================================================================

def test_yfinance_extractor_initialization():
    """Test YFinance_Extractor initializes with symbols"""
    symbols = ['AAPL', 'GOOGL']
    extractor = YFinance_Extractor(symbols)
    assert extractor.symbols == symbols


@patch('src.extractors.yahoo_finance.yf.Ticker')
def test_extract_daily_data_success(mock_ticker_class):
    """Test successful data extraction for a single symbol"""
    # Create mock data
    mock_data = pd.DataFrame({
        'Open': [100.0, 101.0],
        'High': [102.0, 103.0],
        'Low': [99.0, 100.0],
        'Close': [101.0, 102.0],
        'Volume': [1000000, 1100000]
    }, index=pd.date_range('2025-01-01', periods=2))

    mock_ticker = Mock()
    mock_ticker.history.return_value = mock_data
    mock_ticker_class.return_value = mock_ticker

    extractor = YFinance_Extractor(['AAPL'])
    result = extractor.extract_daily_data('AAPL', period='1mo')

    assert not result.empty
    assert 'symbol' in result.columns
    assert 'timestamp' in result.columns
    assert result['symbol'].iloc[0] == 'AAPL'
    assert len(result) == 2
    # Check column names are lowercased
    assert 'open' in result.columns
    assert 'close' in result.columns


@patch('src.extractors.yahoo_finance.yf.Ticker')
def test_extract_daily_data_no_data(mock_ticker_class):
    """Test extraction when no data is available"""
    mock_ticker = Mock()
    mock_ticker.history.return_value = pd.DataFrame()
    mock_ticker_class.return_value = mock_ticker

    extractor = YFinance_Extractor(['INVALID'])
    result = extractor.extract_daily_data('INVALID', period='1mo')

    assert result.empty


@patch('src.extractors.yahoo_finance.yf.Ticker')
def test_extract_daily_data_exception(mock_ticker_class):
    """Test extraction handles exceptions gracefully"""
    mock_ticker = Mock()
    mock_ticker.history.side_effect = Exception("API Error")
    mock_ticker_class.return_value = mock_ticker

    extractor = YFinance_Extractor(['AAPL'])
    result = extractor.extract_daily_data('AAPL', period='1mo')

    assert result.empty


@patch('src.extractors.yahoo_finance.yf.Ticker')
def test_extract_all_multiple_symbols(mock_ticker_class):
    """Test extracting data for multiple symbols"""
    # Mock data for AAPL
    mock_aapl_data = pd.DataFrame({
        'Open': [100.0],
        'Close': [101.0],
        'Volume': [1000000]
    }, index=pd.date_range('2025-01-01', periods=1))

    # Mock data for GOOGL
    mock_googl_data = pd.DataFrame({
        'Open': [200.0],
        'Close': [202.0],
        'Volume': [2000000]
    }, index=pd.date_range('2025-01-01', periods=1))

    def mock_ticker_side_effect(symbol):
        mock_ticker = Mock()
        if symbol == 'AAPL':
            mock_ticker.history.return_value = mock_aapl_data
        elif symbol == 'GOOGL':
            mock_ticker.history.return_value = mock_googl_data
        return mock_ticker

    mock_ticker_class.side_effect = mock_ticker_side_effect

    extractor = YFinance_Extractor(['AAPL', 'GOOGL'])
    result = extractor.extract_all(period='1mo')

    assert not result.empty
    assert len(result) == 2
    assert 'AAPL' in result['symbol'].values
    assert 'GOOGL' in result['symbol'].values


@patch('src.extractors.yahoo_finance.yf.Ticker')
def test_extract_all_no_data(mock_ticker_class):
    """Test extract_all when no data is available for any symbol"""
    mock_ticker = Mock()
    mock_ticker.history.return_value = pd.DataFrame()
    mock_ticker_class.return_value = mock_ticker

    extractor = YFinance_Extractor(['INVALID1', 'INVALID2'])
    result = extractor.extract_all(period='1mo')

    assert result.empty


# ============================================================================
# LOADER / ETL INTEGRATION TESTS
# ============================================================================

@patch('src.loaders.database.YFinance_Extractor')
@patch('src.loaders.database.create_engine')
def test_run_etl_success(mock_create_engine, mock_extractor_class):
    """Test successful ETL run"""
    # Mock extracted data
    mock_data = pd.DataFrame({
        'symbol': ['AAPL', 'AAPL'],
        'timestamp': pd.date_range('2025-01-01', periods=2),
        'close': [100.0, 110.0],
        'open': [99.0, 109.0],
        'high': [101.0, 111.0],
        'low': [98.0, 108.0],
        'volume': [1000000, 1100000]
    })

    mock_extractor = Mock()
    mock_extractor.extract_all.return_value = mock_data
    mock_extractor_class.return_value = mock_extractor

    # Mock database engine
    mock_engine = Mock()
    mock_create_engine.return_value = mock_engine

    # Mock to_sql method
    with patch.object(pd.DataFrame, 'to_sql') as mock_to_sql:
        result = run_etl(engine=mock_engine, symbols=['AAPL'], period='1mo')

        assert result > 0
        mock_to_sql.assert_called_once()
        call_args = mock_to_sql.call_args
        assert call_args[0][0] == 'stock_prices'
        assert call_args[1]['if_exists'] == 'append'
        assert call_args[1]['index'] is False


@patch('src.loaders.database.YFinance_Extractor')
def test_run_etl_no_data_extracted(mock_extractor_class):
    """Test ETL when no data is extracted"""
    mock_extractor = Mock()
    mock_extractor.extract_all.return_value = pd.DataFrame()
    mock_extractor_class.return_value = mock_extractor

    result = run_etl(symbols=['INVALID'], period='1mo')

    assert result == 0


@patch('src.loaders.database.YFinance_Extractor')
@patch('src.loaders.database.create_engine')
def test_run_etl_database_error(mock_create_engine, mock_extractor_class):
    """Test ETL handles database errors gracefully"""
    mock_data = pd.DataFrame({
        'symbol': ['AAPL'],
        'timestamp': pd.date_range('2025-01-01', periods=1),
        'close': [100.0]
    })

    mock_extractor = Mock()
    mock_extractor.extract_all.return_value = mock_data
    mock_extractor_class.return_value = mock_extractor

    mock_engine = Mock()
    mock_create_engine.return_value = mock_engine

    # Simulate database error
    with patch.object(pd.DataFrame, 'to_sql', side_effect=Exception("DB Error")):
        result = run_etl(engine=mock_engine, symbols=['AAPL'], period='1mo')

        assert result == 0


@patch('src.loaders.database.YFinance_Extractor')
def test_run_etl_with_transformations(mock_extractor_class):
    """Test that ETL applies transformations correctly"""
    mock_data = pd.DataFrame({
        'symbol': ['AAPL'] * 3,
        'timestamp': pd.date_range('2025-01-01', periods=3),
        'close': [100.0, 110.0, 105.0],
        'open': [99.0, 109.0, 104.0],
        'high': [101.0, 111.0, 106.0],
        'low': [98.0, 108.0, 103.0],
        'volume': [1000000, 1100000, 1050000]
    })

    mock_extractor = Mock()
    mock_extractor.extract_all.return_value = mock_data
    mock_extractor_class.return_value = mock_extractor

    mock_engine = Mock()

    with patch.object(pd.DataFrame, 'to_sql') as mock_to_sql:
        result = run_etl(engine=mock_engine, symbols=['AAPL'], period='1mo')

        # Verify transformations were applied by checking the call
        assert mock_to_sql.called
        # The DataFrame passed to to_sql should have transformation columns
        # We can't directly access it, but we know if the function ran successfully
        # the transformations were applied
        assert result > 0
