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

class CourseraLogin:
    def __init__(self):
        self.driver_manager = WebDriverManager(headless=False)
        self.driver = self.driver_manager.get_driver()
        self.wait_time = 15
        self.cookie_file = Path("cookies.json")
        self.wait = WebDriverWait(self.driver, self.wait_time)

    def random_delay(self, min_delay=0.5, max_delay=1.5):
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
            invisible_captcha = self.driver.find_element(By.ID, "recaptcha-login-redesign")
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

    def check_login_success(self):
        """Verify if login was successful by checking multiple indicators"""
        try:
            # Check if still on login page (failed login)
            if "coursera.org/login" in self.driver.current_url:
                return False

            # Check for authenticated menu by ID
            try:
                menu = self.driver.find_element(By.ID, "authenticated-info-menu")
                return menu.is_displayed()
            except NoSuchElementException:
                return False

        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False

    def save_cookies(self):
        """Save cookies to file"""
        try:
            cookies = self.get_cookies()
            with open(self.cookie_file, 'w') as f:
                json.dump(cookies, f)
            logger.success(f"Cookies saved to {self.cookie_file}")
        except Exception as e:
            logger.error(f"Error saving cookies: {str(e)}")

    def load_cookies(self):
        """Load cookies from file if they exist"""
        try:
            if self.cookie_file.exists():
                with open(self.cookie_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cookies: {str(e)}")
        return None

    def apply_cookies(self, cookies):
        """Apply cookies to current session and verify login"""
        if not cookies:
            return False
        
        try:
            # Apply cookies before navigating to homepage
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            # Navigate once and check login status
            self.driver.get("https://www.coursera.org")
            return self.is_logged_in()
        except Exception as e:
            logger.error(f"Error applying cookies: {str(e)}")
            return False

    def is_logged_in(self):
        """Check if current session is logged in"""
        try:
            return self.wait.until(
                EC.presence_of_element_located((By.ID, "authenticated-info-menu"))
            ).is_displayed()
        except TimeoutException:
            return False

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
            
            # Check if credentials exist
            if not COURSERA_EMAIL or not COURSERA_PASSWORD:
                logger.warning("Credentials not found. Waiting for manual login...")
                self.driver.get("https://www.coursera.org/login")
                
                # Wait up to 300 seconds (5 minutes) for manual login
                try:
                    WebDriverWait(self.driver, 300).until(
                        EC.presence_of_element_located((By.ID, "authenticated-info-menu"))
                    )
                    logger.success("Manual login successful")
                    self.save_cookies()
                    return True
                except TimeoutException:
                    logger.error("Manual login timeout - no login detected after 5 minutes")
                    return False
                
            # Normal login flow with credentials
            logger.info("Proceeding with automated login")
            self.driver.get("https://www.coursera.org/login")
            self.random_delay(1, 2)

            # Normal login flow
            email_field = self.wait_for_element(By.CSS_SELECTOR, "input[type='email']")
            email_field.clear()
            email_field.send_keys(COURSERA_EMAIL)
            self.random_delay()

            password_field = self.wait_for_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(COURSERA_PASSWORD)
            self.random_delay()

            submit_button = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            self.random_delay(1, 2)

            if self.check_for_captcha():
                logger.info("CAPTCHA detected! Waiting for completion...")
                self.random_delay(1, 2)

            # Verify login success
            if self.is_logged_in():
                logger.success("Login successful")
                self.save_cookies()
                return True
            
            logger.error("Login verification failed")
            return False

        except TimeoutException:
            logger.error("Login timeout - please try again")
            return False
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
