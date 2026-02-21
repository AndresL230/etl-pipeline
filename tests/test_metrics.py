import pytest
import time
from datetime import datetime
from src.monitoring.metrics import MetricsCollector, ExtractionMetrics, TransformationMetrics, LoadMetrics


class TestMetricsCollector:
    def test_initialization(self):
        """Test that metrics collector initializes correctly."""
        collector = MetricsCollector()
        assert collector.metrics is not None
        assert isinstance(collector.metrics.pipeline_start_time, datetime)
        assert collector.metrics.pipeline_end_time is None
        assert collector.metrics.pipeline_success is False

    def test_extraction_metrics(self):
        """Test extraction metrics tracking."""
        collector = MetricsCollector()

        collector.start_extraction(3)
        assert collector.metrics.extraction.total_symbols == 3
        assert collector.metrics.extraction.start_time is not None

        collector.record_symbol_extraction('AAPL', 100, 1.5, success=True)
        assert collector.metrics.extraction.successful_symbols == 1
        assert collector.metrics.extraction.records_per_symbol['AAPL'] == 100
        assert collector.metrics.extraction.total_records_extracted == 100
        assert collector.metrics.extraction.api_response_times['AAPL'] == 1.5

        collector.record_symbol_extraction('GOOGL', 0, 0.5, success=False)
        assert len(collector.metrics.extraction.failed_symbols) == 1
        assert 'GOOGL' in collector.metrics.extraction.failed_symbols

        collector.end_extraction()
        assert collector.metrics.extraction.extraction_duration_seconds > 0
        assert collector.metrics.extraction.end_time is not None

    def test_transformation_metrics(self):
        """Test transformation metrics tracking."""
        collector = MetricsCollector()

        collector.start_transformation(100)
        assert collector.metrics.transformation.records_before == 100
        assert collector.metrics.transformation.start_time is not None

        collector.record_transformation('daily_returns')
        collector.record_transformation('sma_7')
        assert 'daily_returns' in collector.metrics.transformation.transformations_applied
        assert 'sma_7' in collector.metrics.transformation.transformations_applied

        collector.end_transformation(100, null_values=3)
        assert collector.metrics.transformation.records_after == 100
        assert collector.metrics.transformation.null_values_created == 3
        assert collector.metrics.transformation.transformation_duration_seconds > 0

    def test_load_metrics(self):
        """Test load metrics tracking."""
        collector = MetricsCollector()

        collector.start_load()
        assert collector.metrics.load.start_time is not None

        collector.record_database_connection(0.5)
        assert collector.metrics.load.database_connection_time_seconds == 0.5

        collector.end_load(100, success=True)
        assert collector.metrics.load.rows_loaded == 100
        assert collector.metrics.load.load_success is True
        assert collector.metrics.load.error_message is None
        assert collector.metrics.load.load_duration_seconds > 0

    def test_load_metrics_with_error(self):
        """Test load metrics with error tracking."""
        collector = MetricsCollector()

        collector.start_load()
        collector.end_load(0, success=False, error="Database connection failed")

        assert collector.metrics.load.rows_loaded == 0
        assert collector.metrics.load.load_success is False
        assert collector.metrics.load.error_message == "Database connection failed"

    def test_finalize(self):
        """Test finalizing metrics."""
        collector = MetricsCollector()
        time.sleep(0.1)

        collector.finalize(success=True)

        assert collector.metrics.pipeline_end_time is not None
        assert collector.metrics.total_duration_seconds > 0
        assert collector.metrics.pipeline_success is True

    def test_get_summary(self):
        """Test getting metrics summary as dictionary."""
        collector = MetricsCollector()
        collector.start_extraction(1)
        collector.record_symbol_extraction('AAPL', 50, 1.0, success=True)
        collector.end_extraction()
        collector.finalize(success=True)

        summary = collector.get_summary()

        assert isinstance(summary, dict)
        assert 'extraction' in summary
        assert 'transformation' in summary
        assert 'load' in summary
        assert summary['extraction']['total_symbols'] == 1
        assert summary['extraction']['successful_symbols'] == 1

    def test_formatted_summary(self):
        """Test getting formatted summary string."""
        collector = MetricsCollector()
        collector.start_extraction(2)
        collector.record_symbol_extraction('AAPL', 50, 1.0, success=True)
        collector.record_symbol_extraction('GOOGL', 45, 1.2, success=True)
        collector.end_extraction()

        collector.start_transformation(95)
        collector.record_transformation('daily_returns')
        collector.end_transformation(95, null_values=2)

        collector.start_load()
        collector.end_load(95, success=True)

        collector.finalize(success=True)

        formatted = collector.get_formatted_summary()

        assert isinstance(formatted, str)
        assert 'ETL PIPELINE METRICS SUMMARY' in formatted
        assert 'EXTRACTION METRICS' in formatted
        assert 'TRANSFORMATION METRICS' in formatted
        assert 'LOAD METRICS' in formatted
        assert 'SUCCESS' in formatted
        assert 'AAPL: 50 records' in formatted
        assert 'GOOGL: 45 records' in formatted

    def test_save_to_json(self, tmp_path):
        """Test saving metrics to JSON file."""
        collector = MetricsCollector()
        collector.start_extraction(1)
        collector.record_symbol_extraction('AAPL', 50, 1.0, success=True)
        collector.end_extraction()
        collector.finalize(success=True)

        filepath = tmp_path / "test_metrics.json"
        collector.save_to_json(str(filepath))

        assert filepath.exists()

        import json
        with open(filepath) as f:
            data = json.load(f)

        assert data['extraction']['total_symbols'] == 1
        assert data['extraction']['successful_symbols'] == 1
        assert data['pipeline_success'] is True

    def test_full_etl_metrics_flow(self):
        """Test complete ETL metrics flow."""
        collector = MetricsCollector()

        collector.start_extraction(2)
        collector.record_symbol_extraction('AAPL', 100, 1.5, success=True)
        collector.record_symbol_extraction('GOOGL', 95, 1.3, success=True)
        collector.end_extraction()

        collector.start_transformation(195)
        collector.record_transformation('daily_returns')
        collector.record_transformation('sma_7')
        collector.end_transformation(195, null_values=2)

        collector.start_load()
        collector.record_database_connection(0.5)
        collector.end_load(195, success=True)

        collector.finalize(success=True)

        assert collector.metrics.extraction.total_symbols == 2
        assert collector.metrics.extraction.successful_symbols == 2
        assert collector.metrics.extraction.total_records_extracted == 195
        assert len(collector.metrics.transformation.transformations_applied) == 2
        assert collector.metrics.load.rows_loaded == 195
        assert collector.metrics.pipeline_success is True
        assert collector.metrics.total_duration_seconds > 0
