import asyncio
import json
import os
from playwright.async_api import async_playwright
from utils import get_college_slug, delay, USER_AGENTS
from tabs import scrape_cutoff   # scrape_placements,scrape_admission ,scrape_overview , scrape_placements  , 
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
import psutil 
import random
import time


load_dotenv()

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE = os.getenv('LOG_FILE', 'collegedunia_scraper.log')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'university_data')
BASE_URL_FILE = os.getenv('BASE_URL_FILE', 'Medical_colleges.json')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 2))
ROTATE_DRIVER_INTERVAL = int(os.getenv('ROTATE_DRIVER_INTERVAL', 5))
MAX_MEMORY_PERCENT = int(os.getenv('MAX_MEMORY_PERCENT', 80))
STRAPI_DATA_FILE = os.getenv('STRAPI_DATA_FILE', 'all_strapi_data.json')


# Define the tabs and their corresponding scraping functions
TAB_FUNCTIONS = {
    # "overview": scrape_overview,
    # "admission": scrape_admission,
    # "placement": scrape_placements,
    "cutoff": scrape_cutoff,
}

TABS = list(TAB_FUNCTIONS.keys())

# Load college base URLs
# with open("urls.txt", "r") as f:
#     college_urls = [line.strip() for line in f if line.strip()]

def readurl():
    with open("Medical_colleges.json","r",encoding="utf-8") as f:
        college_urls = json.load(f)
        return college_urls
        

os.makedirs("output", exist_ok=True)

def polite_wait(min_delay=3, max_delay=6):
    """Introduces a random delay to be polite to the server."""
    wait_time = random.uniform(min_delay, max_delay)
    time.sleep(wait_time)

def remove_a_img(soup):
    
    for tag in soup.select("a"):
        tag.unwrap()

    for tag in soup.select("iframe"):
        tag.decompose()

    for tag in soup.select("img"):
        tag.decompose()

    for tag in soup.select("svg"):
        tag.decompose()

    for tag in soup.select("div.body-adslot"):
        tag.decompose()
    
    for tag in soup.select("div.bodyslot-new"):
        tag.decompose()

    faq = soup.select_one(".cdcms_faqs")
    if faq: faq.decompose()

    return soup

async def scrape_college(page, college_obj,university_data,idx):
    college_name = college_obj.get("college_name")
    base_url = college_obj.get("url")
    stream = college_obj.get("stream")
    slug = get_college_slug(base_url)


    data = {
        "idx":idx,
        "college_name": college_name,
        "stream": stream,
        "tabs": []
    }
    

    for tab in TABS:
        tab_url = base_url if tab == "overview" else f"{base_url}/{tab}"
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                polite_wait()
                res = await page.goto(tab_url, timeout=30000, wait_until="domcontentloaded")
                if res and res.status != 200:
                    print(f"[SKIPPED] {tab} tab returned {res.status} for {college_name}")
                    data["tabs"][tab] = None
                    break

                await page.wait_for_timeout(2000)

                print(f"Scraping {tab} tab for college | {college_name}")

                scrape_func = TAB_FUNCTIONS[tab]
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                soup = remove_a_img(soup)

                tab_data = await scrape_func(soup)
                data["tabs"].append({
                    "title":tab,
                    "section":tab_data
                })
                await delay()
                break
            except Exception as e:
                print(f"[RETRY {attempt+1}/3] {tab} tab failed for {college_name}: {e}")
                if attempt == retry_attempts - 1:
                    data["tabs"][tab] = None


    university_data.append(data)
    print(len(university_data))
    if len(university_data) >= BATCH_SIZE or psutil.virtual_memory().percent > MAX_MEMORY_PERCENT:
        await save_data_to_file(university_data,stream)

async def save_data_to_file(university_data,stream):
    try:
        file_name = os.path.join("output",f"{stream}_colleges.json")

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

    except Exception as e:
        print(f"[ERROR] Failed to save data: {e}")

    return file_name

def resume():

    folder_name = "output"
    file_name = "Medical_colleges.json"
    file_path = f"{folder_name}\{file_name}"

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
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(user_agent=USER_AGENTS[0])
        page = await context.new_page()
        university_data = []

        college_data = readurl()
        resume_url = resume()
        idx = resume_url

        college_name = ''

        for data in college_data[0:31]:
            try:

                if idx % ROTATE_DRIVER_INTERVAL == 0:
                    await browser.close()
                    browser = await p.chromium.launch(headless=False, slow_mo=100)
                    context = await browser.new_context(user_agent=USER_AGENTS[0])
                    page = await context.new_page()

                college_name = data["college_name"]
                await scrape_college(page, data,university_data,idx)
                print(f"Succesfully Scraped {idx} out of {len(college_data)}")
                idx += 1

            except Exception as e:
                print(f"[FATAL ERROR] Skipping college {college_name}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
