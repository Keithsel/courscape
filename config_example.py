import os
from dotenv import load_dotenv

load_dotenv()

# Default settings
DEFAULT_BROWSER = os.getenv("DEFAULT_BROWSER", "chrome").lower()  # Default to Chrome
