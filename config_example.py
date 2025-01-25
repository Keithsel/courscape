import os
from dotenv import load_dotenv

load_dotenv()

# Default settings
browser = os.getenv("DEFAULT_BROWSER", "").lower()
DEFAULT_BROWSER = browser if browser in ["chrome", "chromium", "firefox"] else "chrome"

# Coursera credentials (optional)
COURSERA_EMAIL = os.getenv("COURSERA_EMAIL")
COURSERA_PASSWORD = os.getenv("COURSERA_PASSWORD")
