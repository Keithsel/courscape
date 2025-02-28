import os
import sys
from dotenv import load_dotenv
from loguru import logger
from log_config import setup_logging

setup_logging()

def validate_env_values():
    """Check if any env values contain comments"""
    affected_keys = []
    for key, value in os.environ.items():
        if value and '#' in value:
            affected_keys.append(key)
    
    if affected_keys:
        logger.error(
            "Comments detected in environment variables. This will cause incorrect behavior!\n"
            "Please remove comments from these variables in your .env file:\n"
            + "\n".join(f"  - {key}" for key in affected_keys)  # Changed from \t to 2 spaces
            + "\nComments should only be kept in .env.template for reference."
        )
        sys.exit(1)

load_dotenv()
validate_env_values()

# Browser settings
DEFAULT_BROWSER = os.getenv("DEFAULT_BROWSER", "chrome").lower()
if DEFAULT_BROWSER not in ["chrome", "edge" "firefox"]:
    DEFAULT_BROWSER = "chrome"

# Coursera credentials (optional)
COURSERA_EMAIL = os.getenv("COURSERA_EMAIL")
COURSERA_PASSWORD = os.getenv("COURSERA_PASSWORD")

# Content to skip
SKIP_COURSES = os.getenv("SKIP_COURSES", "").split(",")
SKIP_SPECIALIZATIONS = os.getenv("SKIP_SPECIALIZATIONS", "").split(",")
