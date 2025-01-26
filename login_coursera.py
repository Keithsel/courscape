from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger
from download_webdriver import WebDriverManager
from config import COURSERA_EMAIL, COURSERA_PASSWORD
import time
import random
import json
from pathlib import Path
import requests


class CourseraLogin:
    def __init__(self):
        self.driver_manager = WebDriverManager(headless=False)
        self.driver = self.driver_manager.get_driver()
        self.wait_time = 60
        self.cookie_file = Path("cookies.json")
        self.wait = WebDriverWait(self.driver, self.wait_time)

    def random_delay(self, min_delay=0.2, max_delay=0.5):
        """Add a random delay between actions"""
        time.sleep(random.uniform(min_delay, max_delay))

    def wait_for_element(self, by, value, timeout=None):
        """Wait for element to be clickable"""
        wait_time = timeout if timeout else self.wait_time
        return WebDriverWait(self.driver, wait_time).until(
            EC.element_to_be_clickable((by, value))
        )

    def check_for_captcha(self):
        """Check if CAPTCHA is present by looking for multiple possible indicators"""
        try:
            # Check for invisible reCAPTCHA
            invisible_captcha = self.driver.find_element(
                By.ID, "recaptcha-login-redesign"
            )
            if invisible_captcha:
                return True

            # Check for interactive reCAPTCHA
            interactive_captcha = self.driver.find_element(By.ID, "rc-imageselect")
            if interactive_captcha:
                return True

            # Check for grecaptcha badge
            grecaptcha = self.driver.find_element(By.CLASS_NAME, "grecaptcha-badge")
            if grecaptcha:
                return True

            return False

        except NoSuchElementException:
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
            cookies = self.get_cookies()
            with open(self.cookie_file, "w") as f:
                json.dump(cookies, f)
            logger.success(f"Cookies saved to {self.cookie_file}")
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

    def _is_cauth_cookie_set(self, driver):
        """Check if CAUTH cookie is present"""
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie["name"] == "CAUTH":
                return True
        return False

    def _wait_for_login(self, timeout=300):
        """Wait for login to complete"""
        try:
            # Need to wrap method to match expected signature
            WebDriverWait(self.driver, timeout).until(
                lambda d: self._verify_login_api(d)
            )
            logger.success("Login successful")
            self.save_cookies()
            return True
        except TimeoutException:
            logger.error(f"Login timeout after {timeout} seconds")
            return False

    def manual_login(self):
        """Handle manual login process"""
        logger.info("Opening login page for manual login...")
        self.driver.get("https://www.coursera.org/login")
        logger.info("You have 5 minutes to complete the login process")
        return self._wait_for_login()

    def login(self):
        """Log into Coursera with existing cookies or credentials"""
        try:
            # Navigate to homepage once before trying cookies
            self.driver.get("https://www.coursera.org")

            # Try cookies first
            cookies = self.load_cookies()
            if cookies and self.apply_cookies(cookies):
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

            # Normal login flow
            email_field = self.wait_for_element(By.CSS_SELECTOR, "input[type='email']")
            email_field.clear()
            email_field.send_keys(COURSERA_EMAIL)
            self.random_delay()

            password_field = self.wait_for_element(
                By.CSS_SELECTOR, "input[type='password']"
            )
            password_field.clear()
            password_field.send_keys(COURSERA_PASSWORD)
            self.random_delay()

            submit_button = self.wait_for_element(
                By.CSS_SELECTOR, "button[type='submit']"
            )
            submit_button.click()
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
        if self.driver:
            self.driver.quit()
            self.driver = None

    @property
    def request(self):
        """Get the session with cookies from selenium"""
        if not self.driver:
            return None
        return self.driver.request
