import os
from dotenv import load_dotenv
from loguru import logger

def validate_env_value(key, value):
    """Check if env value contains comments"""
    if value and '#' in value:
        logger.warning(f"Warning: Environment variable {key} contains a comment character '#'. "
                      "Comments in .env values will be treated as part of the value. "
                      "Please remove comments from your .env file.")

load_dotenv()

# Browser settings
DEFAULT_BROWSER = os.getenv("DEFAULT_BROWSER", "chrome").lower()
validate_env_value("DEFAULT_BROWSER", os.getenv("DEFAULT_BROWSER"))
if DEFAULT_BROWSER not in ["chrome", "chromium", "firefox"]:
    DEFAULT_BROWSER = "chrome"

# Coursera credentials (optional)
COURSERA_EMAIL = os.getenv("COURSERA_EMAIL")
validate_env_value("COURSERA_EMAIL", COURSERA_EMAIL)
COURSERA_PASSWORD = os.getenv("COURSERA_PASSWORD")
validate_env_value("COURSERA_PASSWORD", COURSERA_PASSWORD)

# Content to skip
SKIP_COURSES = os.getenv("SKIP_COURSES", "").split(",")
validate_env_value("SKIP_COURSES", os.getenv("SKIP_COURSES"))
SKIP_SPECIALIZATIONS = os.getenv("SKIP_SPECIALIZATIONS", "").split(",")
validate_env_value("SKIP_SPECIALIZATIONS", os.getenv("SKIP_SPECIALIZATIONS"))
