from src.loaders.database import run_etl
from src.monitoring.metrics import MetricsCollector
import os


def save_metrics_to_file(collector: MetricsCollector, output_dir: str = 'metrics') -> str:
	"""Save metrics to a timestamped JSON file.

	Args:
		collector: MetricsCollector instance with pipeline metrics
		output_dir: Directory to save metrics files (default: 'metrics')

	Returns:
		Path to the saved metrics file
	"""
	os.makedirs(output_dir, exist_ok=True)

	timestamp = collector.metrics.pipeline_start_time.strftime('%Y%m%d_%H%M%S')
	metrics_file = os.path.join(output_dir, f'etl_metrics_{timestamp}.json')
	collector.save_to_json(metrics_file)

	return metrics_file


def main():
	"""Run the ETL pipeline and save metrics."""
	collector = MetricsCollector()
	rows = run_etl(metrics_collector=collector)

	print(f'\nETL completed. Rows loaded: {rows}')
	print(collector.get_formatted_summary())

	metrics_file = save_metrics_to_file(collector)
	print(f'Metrics saved to: {metrics_file}')


if __name__ == '__main__':
	main()
