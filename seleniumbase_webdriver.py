from seleniumbase import Driver
from loguru import logger
from config import DEFAULT_BROWSER
import json
from pathlib import Path


class SeleniumBaseManager:
    """SeleniumBase manager to replace WebDriverManager"""
    
    def __init__(self, browser=DEFAULT_BROWSER, headless=True, incognito=False):
        self.browser = browser
        self.headless = headless
        self.incognito = incognito
        self.driver = None
        logger.debug(
            f"Initializing SeleniumBaseManager with browser={browser}, headless={headless}"
        )
        
    def get_driver(self):
        """
        Initialize a SeleniumBase Driver instance.
        
        Returns:
            Driver: Configured SeleniumBase Driver instance.
        """
        logger.debug(f"Getting SeleniumBase driver for {self.browser}")
        try:
            self.driver = Driver(
                browser=self.browser,
                headless=self.headless,
                incognito=self.incognito,
                use_wire=True,  # request interception
                undetectable=True,  # uc
            )
            logger.success(f"{self.browser.capitalize()} driver setup successful")
            return self.driver
        except Exception as e:
            logger.error(f"Driver setup failed: {str(e)}")
            raise

    def close(self):
        """Close the browser instance"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.debug("Driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing driver: {str(e)}")

    def save_cookies(self, file_path):
        """Save cookies to a file"""
        if not self.driver:
            logger.error("No active driver to save cookies from")
            return False
            
        try:
            cookies = self.driver.get_cookies()
            with open(file_path, 'w') as f:
                json.dump(cookies, f)
            logger.success(f"Cookies saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving cookies: {str(e)}")
            return False
    
    def load_cookies(self, file_path):
        """Load cookies from a file and apply them to the driver"""
        if not self.driver:
            logger.error("No active driver to load cookies into")
            return False
            
        try:
            cookie_file = Path(file_path)
            if not cookie_file.exists():
                logger.debug(f"Cookie file {file_path} does not exist")
                return False
                
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
                
            # First navigate to a blank page to avoid domain issues
            current_url = self.driver.current_url
            if not current_url.startswith('http'):
                self.driver.get('about:blank')
                
            for cookie in cookies:
                try:
                    # SeleniumBase requires domain to match current URL
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Error adding cookie: {str(e)}")
                    
            logger.success("Cookies loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {str(e)}")
            return False
