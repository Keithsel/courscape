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
            logger.error("Login failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during login process: {str(e)}")
        sys.exit(1)
    finally:
        login.close()

if __name__ == '__main__':
    main()
