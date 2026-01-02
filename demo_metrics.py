"""
Demo script to showcase the metrics tracking functionality.
This script runs a simulated ETL pipeline without requiring database connectivity.
"""

import pandas as pd
from datetime import datetime, timedelta
from src.monitoring.metrics import MetricsCollector
from src.extractors.yahoo_finance import YahooFinanceExtractor
from src.transformers.financial_metrics import apply_transformations


def generate_mock_data(symbol, num_days=30):
    """Generate mock stock price data for testing."""
    dates = [datetime.now() - timedelta(days=i) for i in range(num_days, 0, -1)]

    data = pd.DataFrame({
        'open': [100 + i * 0.5 for i in range(num_days)],
        'high': [105 + i * 0.5 for i in range(num_days)],
        'low': [95 + i * 0.5 for i in range(num_days)],
        'close': [102 + i * 0.5 for i in range(num_days)],
        'volume': [1000000 + i * 10000 for i in range(num_days)],
        'dividends': [0.0] * num_days,
        'stock_splits': [0.0] * num_days,
        'symbol': [symbol] * num_days,
        'timestamp': dates
    })

    return data


def demo_metrics():
    """Demonstrate the metrics tracking system."""
    print("=" * 60)
    print("ETL PIPELINE METRICS TRACKING DEMO")
    print("=" * 60)
    print()

    # Create metrics collector
    collector = MetricsCollector()

    # Simulate extraction phase
    print("Step 1: Extracting data...")
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    collector.start_extraction(len(symbols))

    all_data = []
    for symbol in symbols:
        import time
        start = time.time()
        data = generate_mock_data(symbol, num_days=30)
        duration = time.time() - start

        collector.record_symbol_extraction(symbol, len(data), duration, success=True)
        all_data.append(data)

    combined_df = pd.concat(all_data, ignore_index=True)
    collector.end_extraction()
    print(f"  ✓ Extracted {len(combined_df)} records from {len(symbols)} symbols")
    print()

    # Simulate transformation phase
    print("Step 2: Applying transformations...")
    transformed_df = apply_transformations(combined_df, metrics_collector=collector)
    print(f"  ✓ Applied {len(collector.metrics.transformation.transformations_applied)} transformations")
    print(f"  ✓ Transformations: {', '.join(collector.metrics.transformation.transformations_applied)}")
    print()

    # Simulate load phase
    print("Step 3: Loading to database (simulated)...")
    collector.start_load()
    collector.record_database_connection(0.25)

    import time
    time.sleep(0.1)

    collector.end_load(len(transformed_df), success=True)
    print(f"  ✓ Loaded {len(transformed_df)} rows")
    print()

    # Finalize metrics
    collector.finalize(success=True)

    # Display formatted summary
    print(collector.get_formatted_summary())

    # Save to JSON
    collector.save_to_json('demo_metrics.json')
    print()
    print(f"Metrics saved to: demo_metrics.json")
    print()

    # Show how to access specific metrics programmatically
    print("=" * 60)
    print("PROGRAMMATIC ACCESS EXAMPLES")
    print("=" * 60)
    print()
    print("Extraction Metrics:")
    print(f"  - Total records: {collector.metrics.extraction.total_records_extracted}")
    print(f"  - Success rate: {collector.metrics.extraction.successful_symbols}/{collector.metrics.extraction.total_symbols}")
    print(f"  - Average API time: {sum(collector.metrics.extraction.api_response_times.values()) / len(collector.metrics.extraction.api_response_times):.3f}s")
    print()

    print("Transformation Metrics:")
    print(f"  - Null values created: {collector.metrics.transformation.null_values_created}")
    print(f"  - Processing rate: {collector.metrics.transformation.records_after / collector.metrics.transformation.transformation_duration_seconds:.0f} rows/sec")
    print()

    print("Load Metrics:")
    print(f"  - Database connection: {collector.metrics.load.database_connection_time_seconds:.3f}s")
    print(f"  - Load rate: {collector.metrics.load.rows_loaded / collector.metrics.load.load_duration_seconds:.0f} rows/sec")
    print()

    print("Pipeline Metrics:")
    print(f"  - Total duration: {collector.metrics.total_duration_seconds:.2f}s")
    print(f"  - Status: {'✓ SUCCESS' if collector.metrics.pipeline_success else '✗ FAILED'}")


if __name__ == '__main__':
    demo_metrics()
