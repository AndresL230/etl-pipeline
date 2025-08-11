CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    dividends DECIMAL(10,4),
    stock_splits DECIMAL(10,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_time ON stock_prices (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_prices_timestamp ON stock_prices (timestamp DESC);

CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (symbol) 
    symbol, 
    timestamp, 
    close as latest_price,
    volume
FROM stock_prices 
ORDER BY symbol, timestamp DESC;