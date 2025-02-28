import logging
from loguru import logger
from config import DEFAULT_BROWSER
from seleniumbase_webdriver import SeleniumBaseManager


class WebDriverManager:
    def __init__(self, browser=DEFAULT_BROWSER, headless=True):
        self.browser = browser
        self.headless = headless
        self.sb_manager = SeleniumBaseManager(browser=browser, headless=headless)
        logging.getLogger("WDM").disabled = True
        logger.debug(
            f"Initializing WebDriverManager with browser={browser}, headless={headless}"
        )

    def get_driver(self):
        """
        Initialize a WebDriver instance using SeleniumBase.

        Returns:
            WebDriver: Configured WebDriver instance.

        Raises:
            ValueError: If the browser type is not supported.
        """
        try:
            return self.sb_manager.get_driver()
        except Exception as e:
            logger.error(f"Failed to get driver for {self.browser}: {str(e)}")
            raise
    
    def close(self):
        """Close the browser instance"""
        if hasattr(self, 'sb_manager'):
            self.sb_manager.close()
