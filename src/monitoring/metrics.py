import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ExtractionMetrics:
    """Metrics for the extraction phase."""
    total_symbols: int = 0
    successful_symbols: int = 0
    failed_symbols: List[str] = field(default_factory=list)
    total_records_extracted: int = 0
    records_per_symbol: Dict[str, int] = field(default_factory=dict)
    extraction_duration_seconds: float = 0.0
    api_response_times: Dict[str, float] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class TransformationMetrics:
    """Metrics for the transformation phase."""
    records_before: int = 0
    records_after: int = 0
    transformations_applied: List[str] = field(default_factory=list)
    transformation_duration_seconds: float = 0.0
    null_values_created: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class LoadMetrics:
    """Metrics for the load phase."""
    rows_loaded: int = 0
    load_duration_seconds: float = 0.0
    database_connection_time_seconds: float = 0.0
    load_success: bool = False
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class ETLMetrics:
    """Aggregated metrics for the entire ETL pipeline."""
    pipeline_start_time: datetime = field(default_factory=datetime.now)
    pipeline_end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    pipeline_success: bool = False
    extraction: ExtractionMetrics = field(default_factory=ExtractionMetrics)
    transformation: TransformationMetrics = field(default_factory=TransformationMetrics)
    load: LoadMetrics = field(default_factory=LoadMetrics)


class MetricsCollector:
    """Centralized metrics collection for ETL pipeline."""

    def __init__(self):
        self.metrics = ETLMetrics()
        self._extraction_start_time: Optional[float] = None
        self._transformation_start_time: Optional[float] = None
        self._load_start_time: Optional[float] = None

    def start_extraction(self, total_symbols: int):
        """Mark the start of extraction phase."""
        self.metrics.extraction.total_symbols = total_symbols
        self.metrics.extraction.start_time = datetime.now()
        self._extraction_start_time = time.time()
        logger.info(f"Starting extraction for {total_symbols} symbols")

    def record_symbol_extraction(self, symbol: str, records: int, duration: float, success: bool = True):
        """Record metrics for a single symbol extraction."""
        if success:
            self.metrics.extraction.successful_symbols += 1
            self.metrics.extraction.records_per_symbol[symbol] = records
            self.metrics.extraction.total_records_extracted += records
            self.metrics.extraction.api_response_times[symbol] = duration
            logger.debug(f"Symbol {symbol}: {records} records in {duration:.2f}s")
        else:
            self.metrics.extraction.failed_symbols.append(symbol)
            logger.warning(f"Symbol {symbol}: extraction failed")

    def end_extraction(self):
        """Mark the end of extraction phase."""
        if self._extraction_start_time:
            self.metrics.extraction.extraction_duration_seconds = time.time() - self._extraction_start_time
            self.metrics.extraction.end_time = datetime.now()
            logger.info(
                f"Extraction completed: {self.metrics.extraction.successful_symbols}/"
                f"{self.metrics.extraction.total_symbols} symbols, "
                f"{self.metrics.extraction.total_records_extracted} records in "
                f"{self.metrics.extraction.extraction_duration_seconds:.2f}s"
            )

    def start_transformation(self, records_count: int):
        """Mark the start of transformation phase."""
        self.metrics.transformation.records_before = records_count
        self.metrics.transformation.start_time = datetime.now()
        self._transformation_start_time = time.time()
        logger.info(f"Starting transformation on {records_count} records")

    def record_transformation(self, transformation_name: str):
        """Record a transformation that was applied."""
        self.metrics.transformation.transformations_applied.append(transformation_name)
        logger.debug(f"Applied transformation: {transformation_name}")

    def end_transformation(self, records_count: int, null_values: int = 0):
        """Mark the end of transformation phase."""
        if self._transformation_start_time:
            self.metrics.transformation.transformation_duration_seconds = time.time() - self._transformation_start_time
            self.metrics.transformation.records_after = records_count
            self.metrics.transformation.null_values_created = null_values
            self.metrics.transformation.end_time = datetime.now()
            logger.info(
                f"Transformation completed: {len(self.metrics.transformation.transformations_applied)} "
                f"transformations in {self.metrics.transformation.transformation_duration_seconds:.2f}s"
            )

    def start_load(self):
        """Mark the start of load phase."""
        self.metrics.load.start_time = datetime.now()
        self._load_start_time = time.time()
        logger.info("Starting load phase")

    def record_database_connection(self, duration: float):
        """Record database connection time."""
        self.metrics.load.database_connection_time_seconds = duration
        logger.debug(f"Database connection established in {duration:.2f}s")

    def end_load(self, rows_loaded: int, success: bool = True, error: Optional[str] = None):
        """Mark the end of load phase."""
        if self._load_start_time:
            self.metrics.load.load_duration_seconds = time.time() - self._load_start_time
            self.metrics.load.rows_loaded = rows_loaded
            self.metrics.load.load_success = success
            self.metrics.load.error_message = error
            self.metrics.load.end_time = datetime.now()

            if success:
                logger.info(f"Load completed: {rows_loaded} rows in {self.metrics.load.load_duration_seconds:.2f}s")
            else:
                logger.error(f"Load failed: {error}")

    def finalize(self, success: bool = True):
        """Finalize the ETL metrics collection."""
        self.metrics.pipeline_end_time = datetime.now()
        self.metrics.total_duration_seconds = (
            self.metrics.pipeline_end_time - self.metrics.pipeline_start_time
        ).total_seconds()
        self.metrics.pipeline_success = success
        logger.info(f"ETL pipeline completed in {self.metrics.total_duration_seconds:.2f}s")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics as a dictionary."""
        return asdict(self.metrics)

    def get_formatted_summary(self) -> str:
        """Get a human-readable formatted summary of metrics."""
        lines = [
            "=" * 60,
            "ETL PIPELINE METRICS SUMMARY",
            "=" * 60,
            "",
            f"Pipeline Status: {'SUCCESS' if self.metrics.pipeline_success else 'FAILED'}",
            f"Total Duration: {self.metrics.total_duration_seconds:.2f}s",
            f"Start Time: {self.metrics.pipeline_start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"End Time: {self.metrics.pipeline_end_time.strftime('%Y-%m-%d %H:%M:%S') if self.metrics.pipeline_end_time else 'N/A'}",
            "",
            "-" * 60,
            "EXTRACTION METRICS",
            "-" * 60,
            f"  Total Symbols: {self.metrics.extraction.total_symbols}",
            f"  Successful: {self.metrics.extraction.successful_symbols}",
            f"  Failed: {len(self.metrics.extraction.failed_symbols)}",
        ]

        if self.metrics.extraction.failed_symbols:
            lines.append(f"  Failed Symbols: {', '.join(self.metrics.extraction.failed_symbols)}")

        lines.extend([
            f"  Total Records Extracted: {self.metrics.extraction.total_records_extracted}",
            f"  Duration: {self.metrics.extraction.extraction_duration_seconds:.2f}s",
        ])

        if self.metrics.extraction.records_per_symbol:
            lines.append("  Records per Symbol:")
            for symbol, count in sorted(self.metrics.extraction.records_per_symbol.items()):
                api_time = self.metrics.extraction.api_response_times.get(symbol, 0)
                lines.append(f"    {symbol}: {count} records ({api_time:.2f}s)")

        lines.extend([
            "",
            "-" * 60,
            "TRANSFORMATION METRICS",
            "-" * 60,
            f"  Records Before: {self.metrics.transformation.records_before}",
            f"  Records After: {self.metrics.transformation.records_after}",
            f"  Transformations Applied: {', '.join(self.metrics.transformation.transformations_applied) if self.metrics.transformation.transformations_applied else 'None'}",
            f"  Null Values Created: {self.metrics.transformation.null_values_created}",
            f"  Duration: {self.metrics.transformation.transformation_duration_seconds:.2f}s",
            "",
            "-" * 60,
            "LOAD METRICS",
            "-" * 60,
            f"  Rows Loaded: {self.metrics.load.rows_loaded}",
            f"  Load Success: {self.metrics.load.load_success}",
            f"  Database Connection Time: {self.metrics.load.database_connection_time_seconds:.2f}s",
            f"  Load Duration: {self.metrics.load.load_duration_seconds:.2f}s",
        ])

        if self.metrics.load.error_message:
            lines.append(f"  Error: {self.metrics.load.error_message}")

        lines.append("=" * 60)

        return "\n".join(lines)

    def save_to_json(self, filepath: str):
        """Save metrics to a JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.get_summary(), f, indent=2, default=str)
            logger.info(f"Metrics saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save metrics to {filepath}: {str(e)}")
