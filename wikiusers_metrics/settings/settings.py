from pathlib import Path

DEFAULT_METRICS_DIR = Path.cwd().joinpath('metrics') if __name__ != '__main__' else Path(__file__).parent.parent.parent.joinpath('metrics')
DEFAULT_DROPOFF_MONTH_THRESHOLD = 12
DEFAULT_ACTIVE_PER_MONTH_THRESHOLD = 5