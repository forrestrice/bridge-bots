import logging


def configure_logging(log_level: str):
    if log_level == "verbose":
        logging.basicConfig(level=logging.DEBUG)
    elif log_level == "quiet":
        logging.basicConfig(level=logging.CRITICAL)
    else:
        logging.basicConfig(level=logging.INFO)
