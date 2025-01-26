from loguru import logger
import sys


def setup_logging():
    """Configure logging to both console and file with different levels"""
    logger.remove()

    logger.add(
        sys.stderr,
        format="<level>{message}</level>",
        level="INFO",
        filter=lambda record: record["level"].name != "DEBUG",
    )

    logger.add(
        "courscape.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="5 MB",
        retention="7 days",
    )
