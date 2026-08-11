import logging
import sys
import os

def setup_structured_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configures structured logging for Edufeedia microservices and containers.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    root_logger = logging.getLogger("edufeedia")
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if re-initialized
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return root_logger

# Default module logger
logger = setup_structured_logging(os.getenv("LOG_LEVEL", "INFO"))
