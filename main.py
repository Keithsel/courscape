import argparse
from loguru import logger
from login_coursera import CourseraLogin
from course_processor import CourseProcessor
import sys
from log_config import setup_logging


def get_login_session(force_manual=False):
    """Get a valid login session using cookies or credentials"""
    login = CourseraLogin()

    if not force_manual and login.login():
        cookies = login.get_cookies()
        login.close()
        return cookies

    # If force_manual or automatic login failed, try manual login
    logger.info("Waiting for manual login...")
    if login.manual_login():
        cookies = login.get_cookies()
        login.close()
        return cookies

    logger.error(
        "Login failed. Please:\n"
        "1. Make sure you can log in manually at https://www.coursera.org/login\n."
        "2. Try again with --manual-login or -m flag if needed."
    )
    return None


def process_course(processor, course_slug):
    """Process a single course with all its materials"""
    logger.info(f"Processing course: {course_slug}")
    return processor.process_content(course_slug=course_slug)


def process_specialization(processor, spec_slug):
    """Process all courses in a specialization"""
    logger.info(f"Processing specialization: {spec_slug}")
    return processor.process_content(spec_slug=spec_slug)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Coursera content automation")
    # Required arguments (at least one)
    parser.add_argument("--course", "-c", 
                       help="Course slug(s) to process, comma-separated")
    parser.add_argument("--spec", "-s", 
                       help="Specialization slug(s) to process, comma-separated")

    # Optional flags
    parser.add_argument(
        "--manual-login",
        "-m",
        action="store_true",
        help="Force manual login (ignore cookies and credentials)",
    )
    parser.add_argument(
        "--from-config",
        "-f",
        action="store_true",
        help="Read course/specialization from config file",
    )
    parser.add_argument(
        "--reset-progress",
        "-r",
        action="store_true",
        help="Ignore existing progress and start fresh",
    )
    parser.add_argument(
        "--update-types",
        "-u",
        action="store_true",
        help="Update item skippability based on current BYPASS_TYPES configuration",
    )
    return parser.parse_args()


def validate_args(args):
    """Validate command line arguments"""
    if args.from_config:
        if args.course or args.spec:
            logger.error("Cannot use --course or --spec with --from-config. Choose either command line arguments or config file.")
            return False
        return True
    
    if not (args.course or args.spec):
        logger.error("Please provide at least one: --course and/or --spec argument")
        return False
    return True


def load_config():
    """Load configuration from .env file"""
    from config import SKIP_COURSES, SKIP_SPECIALIZATIONS
    
    if not any([SKIP_COURSES, SKIP_SPECIALIZATIONS]):
        logger.error("No courses or specializations found in .env file")
        sys.exit(1)
    
    return {
        "courses": [c.strip() for c in SKIP_COURSES if c.strip()],
        "specializations": [s.strip() for s in SKIP_SPECIALIZATIONS if s.strip()]
    }


def main():
    setup_logging()

    args = parse_arguments()
    if not validate_args(args):
        sys.exit(1)

    login = CourseraLogin()
    try:
        logger.info("Attempting login...")
        if not login.login():
            logger.error("Login failed")
            sys.exit(1)

        cookies = login.get_cookies()
        login.close()  # Close browser after getting cookies

        logger.info("Initializing content processor...")
        processor = CourseProcessor(cookies)
        if not processor.setup():
            sys.exit(1)

        logger.info("Processing content...")
        if args.from_config:
            _process_from_config(processor, args.reset_progress)
        else:
            _process_from_args(processor, args)

        logger.success("Content processing completed")

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        sys.exit(1)
    finally:
        if 'processor' in locals():
            processor.close()


def process_content(processor, args):
    """Process content based on input source"""
    try:
        if args.from_config:
            _process_from_config(processor, args.reset_progress)
        else:
            _process_from_args(processor, args)
        logger.success("Content processing completed")
    except Exception as e:
        logger.error(f"Content processing failed: {e}")
        return False
    return True


def _process_from_config(processor, reset_progress=False):
    """Process content from config file"""
    config = load_config()
    total_processed = 0
    total_failed = 0

    specs = [s.strip() for s in config["specializations"] if s.strip()]
    if specs:
        logger.info(f"Processing {len(specs)} specializations from config")
        for i, spec in enumerate(specs, 1):
            logger.info(f"Specialization {i}/{len(specs)}: {spec}")
            if process_specialization(processor, spec):
                total_processed += 1
            else:
                total_failed += 1

    courses = [c.strip() for c in config["courses"] if c.strip()]
    if courses:
        logger.info(f"Processing {len(courses)} courses from config")
        for i, course in enumerate(courses, 1):
            logger.info(f"Course {i}/{len(courses)}: {course}")
            if process_course(processor, course):
                total_processed += 1
            else:
                total_failed += 1

    logger.info(f"Processed {total_processed} items successfully, {total_failed} failed")


def _process_from_args(processor, args):
    """Process content from command line arguments only"""
    total_processed = 0
    total_failed = 0

    # Handle the update-types flag
    if args.update_types:
        logger.info("Updating skippable content types in progress files...")
        
    if args.spec:
        specs = [s.strip() for s in args.spec.split(',') if s.strip()]
        logger.info(f"Processing {len(specs)} specializations from arguments")
        for spec in specs:
            if args.reset_progress:
                logger.info(f"Resetting progress for specialization: {spec}")
            if process_specialization(processor, spec):
                total_processed += 1
            else:
                total_failed += 1

    if args.course:
        courses = [c.strip() for c in args.course.split(',') if c.strip()]
        logger.info(f"Processing {len(courses)} courses from arguments")
        for course in courses:
            if args.reset_progress:
                logger.info(f"Resetting progress for course: {course}")
            if process_course(processor, course):
                total_processed += 1
            else:
                total_failed += 1

    logger.info(f"Processed {total_processed} items successfully, {total_failed} failed")


if __name__ == "__main__":
    main()
