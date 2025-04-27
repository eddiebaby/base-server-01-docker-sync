import pytest
import pandas as pd
import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from data_collection.market_data_collector import (
    MarketDataCollector, NetworkError, RateLimitExceeded,
    DataValidationError, IncompleteDataError, MarketDataError
)

# Test data fixtures
@pytest.fixture
def sample_ohlcv_data():
    """Valid OHLCV data fixture"""
    return pd.DataFrame({
        'timestamp': [pd.Timestamp('2025-04-24'), pd.Timestamp('2025-04-25')],
        'open': [100.0, 101.0],
        'high': [102.0, 103.0],
        'low': [99.0, 100.0],
        'close': [101.0, 102.0],
        'volume': [1000000, 1100000],
        'symbol': ['AAPL', 'AAPL']
    })

@pytest.fixture
def invalid_ohlcv_data():
    """Invalid OHLCV data fixture with validation issues"""
    return pd.DataFrame({
        'timestamp': [pd.Timestamp('2025-04-24'), pd.Timestamp('2025-04-25')],
        'open': [-100.0, 101.0],  # Invalid negative price
        'high': [98.0, 103.0],    # High < Low
        'low': [99.0, 100.0],
        'close': [101.0, 102.0],
        'volume': [-1000, 1100000],  # Invalid negative volume
        'symbol': ['AAPL', 'AAPL']
    })

@pytest.fixture
def mock_yf_ticker():
    """Mock yfinance Ticker object"""
    mock = Mock()
    mock.info = {
        'longName': 'Apple Inc.',
        'exchange': 'NASDAQ',
        'sector': 'Technology'
    }
    # Create DataFrame with proper index
    df = pd.DataFrame({
        'Open': [100.0],
        'High': [102.0],
        'Low': [99.0],
        'Close': [101.0],
        'Volume': [1000000]
    }, index=[pd.Timestamp('2025-04-24')])
    mock.history.return_value = df
    return mock

@pytest.fixture
def mock_db_connection():
    """Mock database connection manager with proper context manager support"""
    mock = MagicMock()
    mock.execute_query.return_value = [(1,)]  # Return symbol_id
    
    # Create a context manager mock
    ctx_manager = MagicMock()
    ctx_manager.__enter__.return_value = mock
    ctx_manager.__exit__.return_value = None
    
    # Set up the transaction method to return our context manager
    mock.transaction.return_value = ctx_manager
    
    return mock

@pytest.fixture
def market_data_collector(mock_db_connection):
    """MarketDataCollector instance with mocked dependencies"""
    with patch('data_collection.market_data_collector.ConnectionManager') as mock_cm:
        mock_cm.return_value = mock_db_connection
        collector = MarketDataCollector()
        return collector

# Test initialization and configuration
def test_init_with_default_config(market_data_collector):
    """Test MarketDataCollector initialization with default config"""
    assert market_data_collector.config['max_retries'] == 3
    assert market_data_collector.config['retry_delay'] == 1.0
    assert market_data_collector.config['batch_size'] == 10

def test_init_with_custom_config():
    """Test MarketDataCollector initialization with custom config"""
    custom_config = {
        'max_retries': 5,
        'retry_delay': 2.0,
        'batch_size': 20
    }
    collector = MarketDataCollector(config=custom_config)
    assert collector.config['max_retries'] == 5
    assert collector.config['retry_delay'] == 2.0
    assert collector.config['batch_size'] == 20

# Test data fetching
@patch('yfinance.Ticker')
def test_fetch_ohlcv_data_success(mock_ticker_class, market_data_collector, mock_yf_ticker):
    """Test successful OHLCV data fetching"""
    mock_ticker_class.return_value = mock_yf_ticker
    
    data = market_data_collector.fetch_ohlcv_data(
        symbol='AAPL',
        start_date='2025-04-24',
        end_date='2025-04-25'
    )
    
    assert not data.empty
    assert 'open' in data.columns
    assert 'symbol' in data.columns
    assert data['symbol'].iloc[0] == 'AAPL'

@patch('yfinance.Ticker')
def test_fetch_ohlcv_data_network_error(mock_ticker_class, market_data_collector):
    """Test handling of :NetworkError during data fetching"""
    mock_ticker = Mock()
    mock_ticker.history.side_effect = Exception("Connection timeout")
    mock_ticker_class.return_value = mock_ticker
    
    with pytest.raises(NetworkError):
        market_data_collector.fetch_ohlcv_data('AAPL', '2025-04-24')

@patch('yfinance.Ticker')
def test_fetch_ohlcv_data_rate_limit(mock_ticker_class, market_data_collector):
    """Test handling of :RateLimitExceeded during data fetching"""
    mock_ticker = Mock()
    mock_ticker.history.side_effect = Exception("Rate limit exceeded")
    mock_ticker_class.return_value = mock_ticker
    
    with pytest.raises(RateLimitExceeded):
        market_data_collector.fetch_ohlcv_data('AAPL', '2025-04-24')

# Test data validation
def test_validate_data_success(market_data_collector, sample_ohlcv_data):
    """Test successful data validation"""
    validated_data = market_data_collector.validate_data(sample_ohlcv_data)
    assert len(validated_data) == len(sample_ohlcv_data)
    assert all(validated_data['open'] > 0)
    assert all(validated_data['volume'] >= 0)

def test_validate_data_invalid_prices(market_data_collector):
    """Test handling of invalid price data"""
    # Create data with multiple valid rows and one invalid
    data = pd.DataFrame({
        'timestamp': [pd.Timestamp('2025-04-24')] * 4,
        'open': [100.0, -100.0, 100.0, 100.0],
        'high': [102.0, 102.0, 102.0, 102.0],
        'low': [99.0, 99.0, 99.0, 99.0],
        'close': [101.0, 101.0, 101.0, 101.0],
        'volume': [1000000, 1000000, 1000000, 1000000],
        'symbol': ['AAPL'] * 4
    })
    
    validated_data = market_data_collector.validate_data(data)
    assert len(validated_data) == 3  # One row removed
    assert all(validated_data['open'] > 0)

def test_validate_data_missing_columns(market_data_collector):
    """Test handling of missing required columns"""
    invalid_data = pd.DataFrame({'timestamp': [pd.Timestamp('2025-04-24')]})
    with pytest.raises(DataValidationError):
        market_data_collector.validate_data(invalid_data)

# Test database operations
def test_get_symbol_id_existing(market_data_collector, mock_db_connection):
    """Test retrieving existing symbol ID"""
    symbol_id = market_data_collector.get_symbol_id('AAPL')
    assert symbol_id == 1
    mock_db_connection.execute_query.assert_called_once()

@patch('yfinance.Ticker')
def test_get_symbol_id_new(mock_ticker_class, market_data_collector, mock_db_connection, mock_yf_ticker):
    """Test inserting new symbol"""
    mock_ticker_class.return_value = mock_yf_ticker
    mock_db_connection.execute_query.side_effect = [[], [(1,)]]
    
    symbol_id = market_data_collector.get_symbol_id('NEWSTOCK')
    assert symbol_id == 1
    assert mock_db_connection.execute_query.call_count == 2

def test_store_ohlcv_data_success(market_data_collector, sample_ohlcv_data, mock_db_connection):
    """Test successful data storage"""
    rows_stored = market_data_collector.store_ohlcv_data(sample_ohlcv_data)
    assert rows_stored == len(sample_ohlcv_data)
    assert mock_db_connection.transaction.called

# Test full pipeline
@patch('yfinance.Ticker')
def test_collect_market_data_success(mock_ticker_class, market_data_collector, mock_yf_ticker):
    """Test successful end-to-end data collection pipeline"""
    mock_ticker_class.return_value = mock_yf_ticker
    
    results = market_data_collector.collect_market_data(
        symbols=['AAPL'],  # Test with single symbol for simplicity
        start_date='2025-04-24',
        end_date='2025-04-25'
    )
    
    assert results['symbols_processed'] == 1
    assert results['symbols_failed'] == 0
    assert results['total_rows_collected'] > 0
    assert results['total_rows_stored'] > 0
    assert not results['errors']

@patch('yfinance.Ticker')
def test_collect_market_data_partial_failure(mock_ticker_class, market_data_collector, mock_yf_ticker):
    """Test pipeline handling of partial failures"""
    # First call succeeds, second raises network error
    mock_ticker_class.side_effect = [
        mock_yf_ticker,
        Exception("Network error")
    ]
    
    results = market_data_collector.collect_market_data(
        symbols=['AAPL', 'MSFT'],
        start_date='2025-04-24'
    )
    
    assert results['symbols_processed'] == 1
    assert results['symbols_failed'] == 1
    assert len(results['errors']) == 1
    assert "Network error" in str(results['errors'][0]['error'])