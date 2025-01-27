import json
import os
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

with open("misc/uni_crawl/curriculum_entry.json", "r") as f:
    data = json.load(f)

save_path = "misc/uni_crawl/curriculum_pages"

# Create save directory if it doesn't exist
os.makedirs(save_path, exist_ok=True)

# Base URL for the curriculum pages
base_url = "https://flm.fpt.edu.vn/gui/role/student/"

def fetch_and_save(driver, code, link, base_url, save_path):
    try:
        url = base_url + link
        driver.get(url) 
        
        filepath = os.path.join(save_path, f"{code}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
            
        return True
    except Exception as e:
        print(f"Error downloading {code}: {e}")
        return False

def main():
    options = Options()
    service = Service(executable_path="/home/ibi/Inbox/chromedriver-linux64/chromedriver")
    
    num_browsers = 8
    drivers = []
    for i in range(num_browsers):
        driver = webdriver.Chrome(options=options, service=service)
        drivers.append(driver)
        driver.get("https://flm.fpt.edu.vn")
        print(f"Please log in to browser {i+1}.")
        input("Press Enter after you have logged in and see the dashboard...")

    try:
        # Split data into chunks for each browser
        data_chunks = [data[i::num_browsers] for i in range(num_browsers)]
        
        with ThreadPoolExecutor(max_workers=num_browsers) as executor:
            for driver, chunk in zip(drivers, data_chunks):
                executor.submit(process_chunk, driver, chunk)
    finally:
        for driver in drivers:
            driver.quit()

def process_chunk(driver, chunk):
    for entry in chunk:
        fetch_and_save(driver, entry['code'], entry['link'], base_url, save_path)

if __name__ == "__main__":
    main()