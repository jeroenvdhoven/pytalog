import logging
from typing import Optional


def build_logger(name: Optional[str]) -> logging.Logger:
    """
    Function to build a logger. It helps in logging the messages to the console.

    Args:
        name (Optional[str]): Name of the logger.

    Returns:
        logging.Logger: Logger object.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.getLogger("py4j").setLevel(logging.WARNING)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s")
        handler = logging.StreamHandler()
        logger.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
