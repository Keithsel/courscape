# Courscape

[🇻🇳 Đọc hướng dẫn Tiếng Việt](README.vi.md)

A Python tool for automating online course progression with browser automation and API integration.

## Introduction

Many universities require students to complete online courses as part of their curriculum. However, some courses may be irrelevant, leading to wasted time and effort. This tool aims to automate the process of completing online courses by automatically progressing through the course content to unlock the assessments. This allows students to focus on the assessments and skip the irrelevant content.

Key features:

- Browser automation with support for Chrome, Chromium, and Firefox
- Cookie-based session management
- API integration with the endpoints
- Support for both course and specialization processing
- Configurable through environment variables or command line arguments

## Requirements

- Python 3.8 or higher
- One of the following browsers:
  - Google Chrome
  - Chromium
  - Firefox
- Python packages (install using `pip install -r requirements.txt`):

  ```
  loguru==0.7.3
  pybrowsers==0.6.0
  python-dotenv==1.0.1
  selenium==4.28.1
  webdriver-manager==4.0.2
  ```

## Usage

1. Clone the repository:

   ```bash
   git clone https://github.com/Keithsel/courscape.git
   cd courscape
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure settings:
   - Make a copy of `.env.example` and rename it to `.env`:
   - Edit `.env` to set your preferences (credential is optional, if you leave it blank, you will login manually):

     ```bash
     # Browser selection
     DEFAULT_BROWSER=chrome  # or firefox/chromium
     
     # Optional: Credentials for auto-login
     ACCOUNT_EMAIL=your.email@example.com
     ACCOUNT_PASSWORD=your_password
     ```

- Specify courses and specializations in `.env` (optional):

    ```bash
    # Courses and specializations to process
    COURSES=course1-slug,course2-slug
    SPECS=spec1-slug,spec2-slug
    ```

4. Run the tool:

   ```bash
   # Process a single course
   python main.py --course course-slug

   # Process a specialization
   python main.py --spec specialization-slug

   # Force manual login
   python main.py --course course-slug --manual-login
   
   # Read course/specialization from config file (only if specified in .env, by using this option, you can skip the --course and --spec options)
   python main.py --from-config
   ```

## Command Line Arguments

- `--course`, `-c`: Course slug(s) to process (comma-separated)
- `--spec`, `-s`: Specialization slug(s) to process (comma-separated)
- `--manual-login`, `-m`: Force manual login
- `--from-config`, `-f`: Read course/specialization from config file. To use this option, specify the courses and specializations in the `.env` file. Using this option will skip the `--course` and `--spec` options.

## Getting Course/Specialization Slugs

The slug is the unique identifier in the page URL:

- For courses: `https://www.course.org/learn/[course-slug]`
- For specializations: `https://www.course.org/specializations/[specialization-slug]`

## Acknowledgements

This project was inspired by [skipera](https://github.com/serv0id/skipera) and aims to provide a more maintainable and feature-rich solution.
