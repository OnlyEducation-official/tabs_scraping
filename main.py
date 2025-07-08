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
import traceback
import gc
from multiprocessing import Process, current_process, set_start_method
from tqdm import tqdm

load_dotenv()

REQUEST_INTERVAL_SECONDS = 1.0
last_request_time = 0


LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE = os.getenv('LOG_FILE', 'collegedunia_scraper.log')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'university_data')
BASE_URL_FILE = os.getenv('BASE_URL_FILE', 'Medical_college.json')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 10))
ROTATE_DRIVER_INTERVAL = int(os.getenv('ROTATE_DRIVER_INTERVAL', 10))
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

TAB_FUNCTIONS = {
    # "overview": scrape_overview,
    # "admission": scrape_admission,
    # "placement": scrape_placements,
    # "cutoff": scrape_cutoff,
    "courses-fees":scrape_courses
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
    with open("Medical_college.json","r",encoding="utf-8") as f:
        college_urls = json.load(f)
        return college_urls
        

os.makedirs("output", exist_ok=True)

def polite_wait(min_delay=3, max_delay=6):
    """Introduces a random delay to be polite to the server."""
    wait_time = random.uniform(min_delay, max_delay)
    time.sleep(wait_time)

async def scrape_college(page, college_obj, university_data, idx):
    college_name = college_obj.get("college_name", "Unknown College")
    base_url = college_obj.get("url", "")
    stream = college_obj.get("stream", "Unknown Stream")
    slug = get_college_slug(base_url)

    data = {
        "idx": idx,
        "college_name": college_name,
        "stream": stream,
        "tabs": [],
        "data":{}
    }

    for tab in TABS:
        tab_url = base_url if tab == "overview" else f"{base_url}/{tab}"
        retry_attempts = 3

        for attempt in range(retry_attempts):
            try:
                await rate_limit()
                res = await page.goto(tab_url, timeout=30000, wait_until="domcontentloaded")

                if not res:
                    logging.warning(f"[NAVIGATE FAILED] {tab_url} returned None for {college_name}")
                    break

                status = res.status
                if status in (403, 429):
                    logging.info(f"[BACKOFF] {status} for {college_name} - Sleeping for 60 seconds")
                    await asyncio.sleep(60)
                    continue
                elif status != 200:
                    logging.warning(f"[SKIPPED] {tab} tab returned {status} for {college_name}")
                    if tab == "courses-fees":
                        data["data"]["NewCoursesAndFees"] = {}
                    else:
                        data["tabs"].append({
                            "title": tab,
                            "section": ""
                        })
                    break

                await page.wait_for_timeout(2000)
                # logging.info(f"Scraping {tab} tab for college | {college_name}")

                scrape_func = TAB_FUNCTIONS.get(tab)
                if not scrape_func:
                    logging.warning(f"[NO FUNC] No scraping function for tab '{tab}'")
                    break

                tab_data = await scrape_func(page)

                if tab == "courses-fees":
                    if tab_data:
                        data["data"]["NewCoursesAndFees"] = tab_data["NewCoursesAndFees"]
                    else:
                        logging.warning(f"[FORMAT ERROR] courses-fees tab_data not list for {college_name}")
                else:
                    data["tabs"].append({
                        "title": tab,
                        "section": tab_data if isinstance(tab_data, str) else str(tab_data)
                    })

                await delay()
                break

            except Exception as e:

                logging.error(f"[RETRY {attempt+1}/3] {tab} tab failed for {college_name}: {e}")
                traceback.print_exc()
                if attempt == retry_attempts - 1:
                    if tab == "courses-fees":
                        data["data"]["NewCoursesAndFees"] = {}
                    else:
                        data["tabs"].append({
                            "title": tab,
                            "section": ""
                        })

    university_data.append(data)

    # try:
    #     if len(university_data) >= BATCH_SIZE:
    #         await save_data_to_file(university_data, stream)
    # except Exception as e:
    #     logging.error(f"[SAVE FAILED] Error while saving data for {college_name}: {e}")
    #     traceback.print_exc()


async def save_data_to_file(university_data,stream):
    try:
        # file_name = os.path.join("output",f"{stream}_tabs_data.json")
        file_name = os.path.join("output","Courses_tab_data_2000_2501.json")
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
    file_name = "Courses_tab_data_2000_2501.json"
    file_path = f"{folder_name}\\{file_name}"

    data = None

    if not os.path.exists(file_path):
        return 2000

    if os.path.exists(file_path):

        with open(file_path,"r",encoding="utf-8") as f:
            data = json.load(f)

    if data == None:
        return 2000
    else:
        return data[len(data)-1]["idx"] + 1
    
async def setup_driver(p):
    browser = await p.chromium.launch(
        headless=True,
        slow_mo=0,
        args=[
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-background-timer-throttling",
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions"
        ]
    )
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1280, "height": 800}
    )

    await context.route("**/*", lambda route, request: (
        route.abort() if request.resource_type in ["image", "font", "stylesheet"] else route.continue_()
    ))

    page = await context.new_page()

    await page.add_style_tag(content="""
        *, *::before, *::after {
            transition: none !important;
            animation: none !important;
        }
    """)

    return browser, context, page

def run_scraper_batch(batch_data, start_idx, end_idx, batch_id):

    async def batch_main():
        async with async_playwright() as p:
            os.makedirs("output", exist_ok=True)

            with open("output/batch_status.log", "a", encoding="utf-8") as f:
                f.write(f"[{batch_id}] STARTED ({start_idx}-{end_idx})\n")

            browser, context, page = await setup_driver(p)

            start_time = time.time()
            progress_bar = tqdm(
                enumerate(batch_data, start=start_idx),
                total=len(batch_data),
                desc=f"[{batch_id}]",
                unit="college",
                position=0,
                leave=True
            )

            university_data = []

            for idx, college in progress_bar:
                try:
                    college_name = college.get("college_name", "Unknown")
                    logging.info(f"\n[{batch_id}] Scraping {college_name} at idx {idx}")
                    await scrape_college(page, college, university_data, idx)

                    if idx % ROTATE_DRIVER_INTERVAL == 0:
                        await browser.close()
                        browser, context, page = await setup_driver(p)

                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx - start_idx + 1)
                    remaining = avg_time * (end_idx - idx - 1)
                    progress_bar.set_postfix({
                        "Elapsed": f"{elapsed/60:.1f}m",
                        "ETA": f"{remaining/60:.1f}m"
                    })

                except Exception as e:
                    logging.error(f"[{batch_id}] ❌ Skipping {college.get('college_name', '')}: {e}")

            try:
                file_name = f"Courses_tab_data_{start_idx}_{end_idx}.json"
                temp_file = f"{file_name}.tmp"

                with open(f"output/{temp_file}", "w", encoding="utf-8") as f:
                    json.dump(university_data, f, ensure_ascii=False, indent=2)

                os.replace(f"output/{temp_file}", f"output/{file_name}")
                logging.info(f"[{batch_id}] ✅ Safely saved {file_name} with {len(university_data)} entries")

                with open("output/batch_status.log", "a", encoding="utf-8") as f:
                    f.write(f"[{batch_id}] COMPLETED ✅ ({start_idx}-{end_idx}) | Colleges: {len(university_data)}\n")

                university_data.clear()
                gc.collect()

            except Exception as e:
                logging.error(f"[{batch_id}] ❌ Save failed: {e}")
                with open("output/batch_status.log", "a", encoding="utf-8") as f:
                    f.write(f"[{batch_id}] FAILED ❌ ({start_idx}-{end_idx}) - Save Error: {e}\n")

            await browser.close()

    try:
        asyncio.run(batch_main())
    except Exception as e:
        logging.error(f"[{batch_id}] ❌ Batch crashed: {e}")
        with open("output/batch_status.log", "a", encoding="utf-8") as f:
            f.write(f"[{batch_id}] FAILED ❌ ({start_idx}-{end_idx}) - Runtime Error: {e}\n")


def split_into_batches(data, batch_size):
    return [data[i:i+batch_size] for i in range(0, len(data), batch_size)]

def get_failed_batches():
    failed_batches = []

    if not os.path.exists("output/batch_status.log"):
        return failed_batches

    with open("output/batch_status.log", "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if "] FAILED ❌" in line:
            batch_id = line.split("]")[0][1:]
            range_text = line.split("(")[1].split(")")[0]
            start_idx, end_idx = map(int, range_text.split("-"))
            failed_batches.append((batch_id, start_idx, end_idx))

    return failed_batches

def retry_failed_batches(all_data):
    failed = get_failed_batches()
    if not failed:
        print("✅ No failed batches found.")
        return

    print(f"🔁 Retrying {len(failed)} failed batches...")

    for batch_id, start_idx, end_idx in failed:
        batch_data = all_data[start_idx:end_idx]
        p = Process(target=run_scraper_batch, args=(batch_data, start_idx, end_idx, batch_id))
        p.start()
        p.join() 

def merge_all_batches_to_single():
    merged = []
    output_dir = "output"

    for file in sorted(os.listdir(output_dir)):
        if file.startswith("Courses_tab_data_") and file.endswith(".json"):
            try:
                with open(os.path.join(output_dir, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    merged.extend(data)
            except Exception as e:
                logging.warning(f"⚠️ Could not read {file}: {e}")

    final_file = os.path.join(output_dir, "MERGED_all_colleges.json")
    with open(final_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    logging.info(f"✅ Merged {len(merged)} colleges into {final_file}")

def get_completed_batch_ranges(output_dir="output"):
    completed_ranges = set()
    for file in os.listdir(output_dir):
        if file.startswith("Courses_tab_data_") and file.endswith(".json"):
            try:
                parts = file.replace("Courses_tab_data_", "").replace(".json", "").split("_")
                start, end = int(parts[0]), int(parts[1])
                completed_ranges.add((start, end))
            except:
                continue
    return completed_ranges

def wait_if_system_busy(threshold_ram=85, threshold_cpu=90):
    while True:
        ram_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=1)

        if ram_percent < threshold_ram and cpu_percent < threshold_cpu:
            break
        else:
            print(f"⚠️ High usage — RAM: {ram_percent}%, CPU: {cpu_percent}%. Waiting...")
            time.sleep(10)

if __name__ == "__main__":
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    all_data = readurl()
    batch_size = 100
    batches = split_into_batches(all_data, batch_size)

    completed = get_completed_batch_ranges()
    incomplete_batches = []

    for i, batch_data in enumerate(batches):
        start_idx = i * batch_size
        end_idx = start_idx + len(batch_data)
        if (start_idx, end_idx) in completed:
            print(f"⏩ Skipping completed batch: {start_idx}-{end_idx}")
            continue
        incomplete_batches.append((batch_data, start_idx, end_idx, f"Batch-{i+1}"))

    MAX_CONCURRENT_PROCESSES = 4
    running = []

    for batch_data, start_idx, end_idx, batch_id in incomplete_batches:
        print(f"🚀 Launching {batch_id} ({start_idx}–{end_idx})")
        p = Process(target=run_scraper_batch, args=(batch_data, start_idx, end_idx, batch_id))
        wait_if_system_busy()
        p.start()
        running.append(p)

        if len(running) >= MAX_CONCURRENT_PROCESSES:
            for r in running:
                r.join()
            running = []

    for r in running:
        r.join()

    print("✅ All initial batches complete.")
    retry_failed_batches(all_data)
    merge_all_batches_to_single()

    


