import asyncio
import json
import os
from playwright.async_api import async_playwright
from utils import get_college_slug, delay, USER_AGENTS
from tabs import scrape_cutoff ,scrape_placements,scrape_admission ,scrape_overview , scrape_placements, scrape_courses
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
import psutil 
import random
import time

load_dotenv()

# Global rate limit config
REQUEST_INTERVAL_SECONDS = 1.0  # One request per second
last_request_time = 0


LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE = os.getenv('LOG_FILE', 'collegedunia_scraper.log')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'university_data')
BASE_URL_FILE = os.getenv('BASE_URL_FILE', 'Medical_college.json')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 10))
ROTATE_DRIVER_INTERVAL = int(os.getenv('ROTATE_DRIVER_INTERVAL', 5))
MAX_MEMORY_PERCENT = int(os.getenv('MAX_MEMORY_PERCENT', 80))
STRAPI_DATA_FILE = os.getenv('STRAPI_DATA_FILE', 'all_strapi_data.json')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


# Define the tabs and their corresponding scraping functions
TAB_FUNCTIONS = {
    "overview": scrape_overview,
    # "admission": scrape_admission,
    # "placement": scrape_placements,
    # "cutoff": scrape_cutoff,
    # "courses-fees":scrape_courses
}

TABS = list(TAB_FUNCTIONS.keys())

async def rate_limit():
    global last_request_time
    now = time.time()
    elapsed = now - last_request_time
    if elapsed < REQUEST_INTERVAL_SECONDS:
        await asyncio.sleep(REQUEST_INTERVAL_SECONDS - elapsed)
    last_request_time = time.time()


def readurl():
    with open("Medical_colleges.json","r",encoding="utf-8") as f:
        college_urls = json.load(f)
        return college_urls
        

os.makedirs("output", exist_ok=True)

def polite_wait(min_delay=3, max_delay=6):
    """Introduces a random delay to be polite to the server."""
    wait_time = random.uniform(min_delay, max_delay)
    time.sleep(wait_time)

async def scrape_college(page, college_obj,university_data,idx):
    college_name = college_obj.get("college_name")
    base_url = college_obj.get("url")
    stream = college_obj.get("stream")
    slug = get_college_slug(base_url)

    data = {
        "idx":idx,
        "college_name": college_name,
        "stream": stream,
        "tabs": [],
        "courses":[]
    }
    
    for tab in TABS:
        tab_url = base_url if tab == "overview" else f"{base_url}/{tab}"
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                await rate_limit()
                res = await page.goto(tab_url, timeout=30000, wait_until="domcontentloaded")
                if res:
                    status = res.status
                    if status == 403 or status == 429:
                        logging.info(f"[BACKOFF] {status} for {college_name} - Sleeping for 60 seconds")
                        await asyncio.sleep(60) 
                        continue  
                    elif status != 200:
                        logging.info(f"[SKIPPED] {tab} tab returned {status} for {college_name}")
                        data["tabs"].append({
                            "title": tab,
                            "section": ""
                        })
                        
                        break 

                await page.wait_for_timeout(2000)

                logging.info(f"Scraping {tab} tab for college | {college_name}")

                scrape_func = TAB_FUNCTIONS[tab]
                

                tab_data = await scrape_func(page)
                if tab == "courses-fees":
                    for item in tab_data:
                        data["tabs"].extend(item.get("tabs", []))
                        data["courses"].extend(item.get("courses", []))
                else:
                    data["tabs"].append({
                        "title":tab,
                        "section":tab_data
                    })

                await delay()
                break
            except Exception as e:
                logging.info(f"[RETRY {attempt+1}/3] {tab} tab failed for {college_name}: {e}")
                if attempt == retry_attempts - 1:
                    data["tabs"].append({
                        "title": tab,
                        "section": ""
                    })

    university_data.append(data)
    if len(university_data) >= BATCH_SIZE or psutil.virtual_memory().percent > MAX_MEMORY_PERCENT:
        await save_data_to_file(university_data,stream)

async def save_data_to_file(university_data,stream):
    try:
        # file_name = os.path.join("output",f"{stream}_tabs_data.json")
        file_name = os.path.join("output","College_tab_data.json")
        if os.path.exists(file_name):
            with open(file_name,"r",encoding="utf-8") as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        existing_data.extend(university_data)

        with open(file_name,"w",encoding="utf-8") as f:
            json.dump(existing_data,f,ensure_ascii=False,indent=2)

        existing_data.clear()

        university_data.clear()

        logging.info("SUccesfully Saved!")

    except Exception as e:
        logging.info(f"[ERROR] Failed to save data: {e}")

    return file_name

def resume():

    folder_name = "output"
    file_name = "College_tab_data.json"
    file_path = f"{folder_name}\\{file_name}"

    data = None
    if os.path.exists(file_path):

        with open(file_path,"r",encoding="utf-8") as f:
            data = json.load(f)

    if data == None:
        return 0
    else:
        return data[len(data)-1]["idx"] + 1

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=100)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()
        university_data = []

        college_data = readurl()
        resume_url = resume()
        idx = resume_url

        college_name = ''

        for data in college_data[:1]:
            try:
                if idx % ROTATE_DRIVER_INTERVAL == 0:
                    await browser.close()
                    browser = await p.chromium.launch(headless=True, slow_mo=100)
                    context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
                    page = await context.new_page()

                college_name = data["college_name"]
                await scrape_college(page, data,university_data,idx)
                logging.info(f"\nSuccesfully Scraped {idx} out of {len(college_data)}")
                idx += 1

            except Exception as e:
                logging.info(f"[FATAL ERROR] Skipping college {college_name}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
