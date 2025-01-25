import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import browsers
from download_webdriver import WebDriverManager
from loguru import logger
import logging


def configure_logging():
    """Configure logging to show only relevant information."""
    logger.remove()

    logger.add(
        sys.stdout,
        format="<level>{message}</level>",
        filter=lambda record: "courscape" in record["name"]
        or record["name"] == "__main__",
        level="INFO",
    )

    logging.getLogger("WDM").setLevel(logging.NOTSET)
    for name in ["selenium", "urllib3"]:
        logging.getLogger(name).setLevel(logging.WARNING)


def test_available_browsers():
    """Test WebDriver initialization for available browsers."""
    browser_types = {browser["browser_type"] for browser in browsers.browsers()}
    logger.info(f"Available browsers: {', '.join(sorted(browser_types))}\n")

    results = {"pass": 0, "fail": 0}

    for browser_type in browser_types:
        try:
            driver = WebDriverManager(browser=browser_type, headless=True).get_driver()
            driver.get("https://www.python.org")
            driver.quit()
            logger.success(f"✓ {browser_type:10} OK")
            results["pass"] += 1
        except Exception as e:
            logger.error(f"✗ {browser_type:10} FAILED ({str(e)})")
            results["fail"] += 1

    # Print overall verdict
    total = results["pass"] + results["fail"]
    print(f"\n{'=' * 40}")
    if results["fail"] > 0:
        logger.error(f"FAILED ({results['pass']}/{total} passed)")
    else:
        logger.success(f"PASSED ({total}/{total} browsers)")


if __name__ == "__main__":
    configure_logging()
    test_available_browsers()
