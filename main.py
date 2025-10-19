from src.loaders.database import run_etl


def main():
	rows = run_etl()
	print(f'ETL completed. Rows loaded: {rows}')


if __name__ == '__main__':
	main()
