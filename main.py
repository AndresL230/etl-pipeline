from src.loaders.database import run_etl
from src.monitoring.metrics import MetricsCollector
import os


def main():
	collector = MetricsCollector()
	rows = run_etl(metrics_collector=collector)

	print(f'\nETL completed. Rows loaded: {rows}')
	print(collector.get_formatted_summary())

	metrics_dir = 'metrics'
	if not os.path.exists(metrics_dir):
		os.makedirs(metrics_dir)

	timestamp = collector.metrics.pipeline_start_time.strftime('%Y%m%d_%H%M%S')
	metrics_file = os.path.join(metrics_dir, f'etl_metrics_{timestamp}.json')
	collector.save_to_json(metrics_file)


if __name__ == '__main__':
	main()
