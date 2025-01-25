from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.core.os_manager import ChromeType
from loguru import logger
from config import DEFAULT_BROWSER
import logging

class WebDriverManager:
    def __init__(self, browser=DEFAULT_BROWSER, headless=True):
        self.browser = browser
        self.headless = headless
        logging.getLogger('WDM').disabled = True
        logger.debug(f"Initializing WebDriverManager with browser={browser}, headless={headless}")

    def get_driver(self):
        """
        Initialize a WebDriver instance for Chrome/Chromium or Firefox.
        
        Returns:
            WebDriver: Configured WebDriver instance.
        
        Raises:
            ValueError: If the browser type is not supported.
        """
        logger.debug(f"Getting driver for {self.browser}")
        try:
            if self.browser == 'chrome':
                return self._get_chrome_driver()
            elif self.browser == 'chromium':
                return self._get_chromium_driver()
            elif self.browser == 'firefox':
                return self._get_firefox_driver()
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")
        except Exception as e:
            logger.error(f"Failed to get driver for {self.browser}: {str(e)}")
            raise

    def _get_chrome_driver(self):
        logger.debug("Setting up Chrome driver")
        try:
            options = webdriver.ChromeOptions()
            if self.headless:
                logger.debug("Enabling headless mode for Chrome")
                options.add_argument('--headless')

            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logger.success("Chrome driver setup successful")
            return driver
        except Exception as e:
            logger.error(f"Chrome driver setup failed: {str(e)}")
            raise

    def _get_chromium_driver(self):
        logger.debug("Setting up Chromium driver")
        try:
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            
            service = ChromeService(
                ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            )
            driver = webdriver.Chrome(service=service, options=options)
            logger.success("Chromium driver setup successful")
            return driver
        except Exception as e:
            logger.error(f"Chromium driver setup failed: {str(e)}")
            raise

    def _get_firefox_driver(self):
        logger.debug("Setting up Firefox driver")
        try:
            options = webdriver.FirefoxOptions()
            if self.headless:
                options.add_argument('--headless')
            
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
            logger.success("Firefox driver setup successful")
            return driver
        except Exception as e:
            logger.error(f"Firefox driver setup failed: {str(e)}")
            raise