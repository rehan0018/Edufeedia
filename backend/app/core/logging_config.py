import logging
import os
import json
import datetime

class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production log aggregation (CloudWatch, Datadog)."""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        return json.dumps(log_obj)

logger = logging.getLogger("edufeedia")
if not logger.handlers:
    handler = logging.StreamHandler()
    if os.getenv("LOG_FORMAT", "").lower() == "json" or os.getenv("ENVIRONMENT") == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
    logger.addHandler(handler)

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))
