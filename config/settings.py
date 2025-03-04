import os
from dotenv import load_dotenv

load_dotenv()

RATE_LIMIT_CONFIG = {
    'max_retries': int(os.getenv('MAX_RETRIES', 3)),
    'base_retry_delay': int(os.getenv('BASE_RETRY_DELAY', 5)),
    'max_retry_delay': int(os.getenv('MAX_RETRY_DELAY', 60)),
    'jitter_range': (
        float(os.getenv('JITTER_MIN', 0.8)),
        float(os.getenv('JITTER_MAX', 1.2))
    )
}