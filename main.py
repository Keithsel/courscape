import argparse
from loguru import logger
from login_coursera import CourseraLogin
import sys

def main():
    parser = argparse.ArgumentParser(description='Coursera Login Tool')
    args = parser.parse_args()
    login = CourseraLogin()

    try:
        if not login.login():
            logger.error("Login failed. Please:\n"
                            "1. Check your credentials in the .env file\n"
                            "2. Make sure you can log in manually at https://www.coursera.org/login\n"
                            "3. Remove the cookies.json file if exists and delete the credentials in your .env file, and try again to log in manually.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during login process: {str(e)}")
        sys.exit(1)
    finally:
        login.close()

if __name__ == '__main__':
    main()
