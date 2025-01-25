import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import browsers
from download_webdriver import WebDriverManager
from loguru import logger

def test_available_browsers():
    """Test WebDriver initialization for available browsers."""
    browser_types = {browser['browser_type'] for browser in browsers.browsers()}
    logger.info(f"Found browsers: {browser_types}")

    results = {'pass': 0, 'fail': 0}
    
    for browser_type in browser_types:
        try:
            driver = WebDriverManager(browser=browser_type, headless=True).get_driver()
            driver.get("https://www.python.org")
            driver.quit()
            logger.success(f"✓ {browser_type}")
            results['pass'] += 1
        except Exception as e:
            logger.error(f"✗ {browser_type}: {str(e)}")
            results['fail'] += 1

    # Print overall verdict
    total = results['pass'] + results['fail']
    logger.info("\n" + "="*40)
    logger.info(f"Overall Verdict: {results['pass']}/{total} browsers passed")
    if results['fail'] > 0:
        logger.error(f"❌ {results['fail']} browser(s) failed")
    if results['pass'] > 0:
        logger.success(f"✅ {results['pass']} browser(s) passed")

if __name__ == "__main__":
    test_available_browsers()
