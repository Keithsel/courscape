from loguru import logger
from seleniumbase_webdriver import SeleniumBaseManager
from config import COURSERA_EMAIL, COURSERA_PASSWORD
import time
import random
import json
from pathlib import Path
import requests


class CourseraLogin:
    def __init__(self):
        self.driver_manager = SeleniumBaseManager(headless=False)
        self.driver = None
        self.wait_time = 60
        self.cookie_file = Path("cookies.json")

    def random_delay(self, min_delay=0.2, max_delay=0.5):
        """Add a random delay between actions"""
        time.sleep(random.uniform(min_delay, max_delay))

    def check_for_captcha(self):
        """Check if CAPTCHA is present by looking for multiple possible indicators"""
        try:
            # Check for invisible reCAPTCHA
            if self.driver.is_element_present("#recaptcha-login-redesign"):
                return True

            # Check for interactive reCAPTCHA
            if self.driver.is_element_present("#rc-imageselect"):
                return True

            # Check for grecaptcha badge
            if self.driver.is_element_present(".grecaptcha-badge"):
                return True

            return False

        except Exception:
            return False

    def _verify_login_api(self, driver=None):
        """Internal method to verify login status via API"""
        try:
            # Use provided driver or instance driver
            driver = driver or self.driver
            cauth = driver.get_cookie("CAUTH")
            if not cauth:
                logger.debug("CAUTH cookie not found")
                return False

            response = requests.get(
                "https://www.coursera.org/api/adminUserPermissions.v1",
                params={"q": "my"},
                cookies={"CAUTH": cauth["value"]},
            )

            if response.status_code != 200:
                logger.debug(f"API request failed with status {response.status_code}")
                return False

            data = response.json()
            return bool(data.get("elements", []))

        except Exception as e:
            logger.debug(f"Login verification failed: {str(e)}")
            return False

    def check_login_success(self):
        """Verify if login was successful"""
        try:
            return self._verify_login_api()
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False

    def save_cookies(self):
        """Save cookies to file"""
        try:
            if self.driver:
                self.driver_manager.save_cookies(self.cookie_file)
        except Exception as e:
            logger.error(f"Error saving cookies: {str(e)}")

    def load_cookies(self):
        """Load cookies from file if they exist"""
        try:
            if self.cookie_file.exists():
                with open(self.cookie_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cookies: {str(e)}")
            return None

    def apply_cookies(self, cookies):
        """Apply cookies to current session and verify login"""
        if not cookies:
            return False

        try:
            self.driver.get("https://www.coursera.org")
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.get("https://www.coursera.org")
            return self.is_logged_in()
        except Exception as e:
            logger.error(f"Error applying cookies: {str(e)}")
            return False

    def is_logged_in(self):
        """Check if current session is logged in"""
        return self._verify_login_api()

    def _wait_for_login(self, timeout=300):
        """Wait for login to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._verify_login_api():
                logger.success("Login successful")
                self.save_cookies()
                return True
            time.sleep(2)
        
        logger.error(f"Login timeout after {timeout} seconds")
        return False

    def manual_login(self):
        """Handle manual login process"""
        try:
            self.driver = self.driver_manager.get_driver()
            logger.info("Opening login page for manual login...")
            self.driver.get("https://www.coursera.org/login")
            logger.info("You have 5 minutes to complete the login process")
            return self._wait_for_login()
        except Exception as e:
            logger.error(f"Manual login failed: {str(e)}")
            return False

    def login(self):
        """Log into Coursera with existing cookies or credentials"""
        try:
            self.driver = self.driver_manager.get_driver()
            
            # Navigate to homepage once before trying cookies
            self.driver.get("https://www.coursera.org")

            # Try cookies first
            cookies = self.load_cookies()
            if cookies and self.driver_manager.load_cookies(self.cookie_file) and self._verify_login_api():
                logger.success("Login successful using cookies")
                return True

            # Try credentials if available
            if COURSERA_EMAIL and COURSERA_PASSWORD:
                return self._login_with_credentials()

            # If no credentials, fallback to manual
            return self.manual_login()

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def _login_with_credentials(self):
        """Login using email/password"""
        try:
            logger.info("Attempting login with credentials...")
            self.driver.get("https://www.coursera.org/login")
            self.random_delay(0.3, 0.7)

            # Normal login flow - use SeleniumBase's convenient methods
            self.driver.wait_for_element_visible("input[type='email']")
            self.driver.type("input[type='email']", COURSERA_EMAIL)
            self.random_delay()

            self.driver.wait_for_element_visible("input[type='password']")
            self.driver.type("input[type='password']", COURSERA_PASSWORD)
            self.random_delay()

            self.driver.wait_for_element_clickable("button[type='submit']")
            self.driver.click("button[type='submit']")
            self.random_delay(0.3, 0.7)

            if self.check_for_captcha():
                logger.info("CAPTCHA detected! Waiting for completion...")
                return self._wait_for_login()

            return self._wait_for_login(timeout=10)

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def get_cookies(self):
        """Return cookies after successful login"""
        return self.driver.get_cookies() if self.driver else None

    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver_manager'):
            self.driver_manager.close()
            self.driver = None
