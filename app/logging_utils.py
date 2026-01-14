import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "ts": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Add extra fields if they exist
        for key in ['request_id', 'method', 'path', 'status', 'latency_ms', 'message_id', 'dup', 'result']:
            if hasattr(record, key):
                log_record[key] = getattr(record, key)
        return json.dumps(log_record)

def setup_logger():
    logger = logging.getLogger("lyftr_api")
    handler = logging.StreamHandler()
    formatter = JSONFormatter(datefmt='%Y-%m-%dT%H:%M:%SZ')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logger()