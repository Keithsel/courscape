import os
from dotenv import load_dotenv

load_dotenv()

# Browser settings
DEFAULT_BROWSER = os.getenv("DEFAULT_BROWSER", "chrome").lower()
if DEFAULT_BROWSER not in ["chrome", "chromium", "firefox"]:
    DEFAULT_BROWSER = "chrome"

# Coursera credentials (optional)
COURSERA_EMAIL = os.getenv("COURSERA_EMAIL")
COURSERA_PASSWORD = os.getenv("COURSERA_PASSWORD")

# Content to skip
SKIP_COURSES = os.getenv("SKIP_COURSES", "").split(",")
SKIP_SPECIALIZATIONS = os.getenv("SKIP_SPECIALIZATIONS", "").split(",")
