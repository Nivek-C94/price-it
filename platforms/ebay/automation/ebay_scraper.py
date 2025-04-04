import os
import queue
import threading
import time
import urllib.parse
from botasaurus_driver import driver
from botasaurus_driver.core import config
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from utils import settings
from utils.log_manager import console
from utils.utils import detect_price_outliers

def get_fixed_linux_executable_path():
    """Determines the Chrome executable to use."""
    chrome_path = os.environ.get("CHROME_PATH")
    if chrome_path and os.path.exists(chrome_path):
        console.info(f"Using Chrome binary from CHROME_PATH: {chrome_path}")
        return chrome_path
    fallback_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chrome",
    ]
    for path in fallback_paths:
        if os.path.exists(path):
            console.info(f"Found Chrome binary at fallback path: {path}")
            return path
    console.error("Chrome executable not found. Set CHROME_PATH.")
    return ""

config.get_linux_executable_path = get_fixed_linux_executable_path

class EbayScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.lock = threading.Lock()
        self.driver_pool = queue.Queue()
        self.results = []
        self.prices = []
        self._initialize_drivers()

    def _initialize_drivers(self):
        num_drivers = getattr(settings, "SCRAPER_NUM_DRIVERS", 3)
        console.info(f"Spawning {num_drivers} persistent drivers...")
        for _ in range(num_drivers):
            try:
                user_agent = UserAgent().random if hasattr(UserAgent(), 'random') else 'Mozilla/5.0'
                bot = driver.Driver(user_agent=user_agent, headless=True)
                self.driver_pool.put(bot)
            except Exception as e:
                console.error(f"Error initializing driver: {e}")

    def scrape_page(self, query, condition="", specifics="", page=1, exclude_parts=True):
        condition_filter = f"&LH_ItemCondition={condition}" if condition else ""
        specifics_filter = f"&_sop=12&{specifics}" if specifics else ""
        url = f"{self.base_url}?_nkw={query}&LH_Sold=1&LH_Complete=1{condition_filter}{specifics_filter}&_pgn={page}"

        try:
            bot = self.driver_pool.get(timeout=10)
        except queue.Empty:
            console.error("No available drivers in pool.")
            return

        for attempt in range(3):
            try:
                bot.get(url)
                bot.wait_for_element(".s-item")
                html_source = bot.page_html
                break
            except Exception as e:
                console.error(f"Error fetching page {page} (Attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)
        else:
            console.error(f"❌ Failed to fetch page {page} after multiple attempts.")
            return

        if "Please verify you're a human" in html_source:
            console.warning("🚨 CAPTCHA detected! Retrying after 10 seconds...")
            time.sleep(10)
            return self.scrape_page(query, condition, specifics, page, exclude_parts)

        soup = BeautifulSoup(html_source, "html.parser")
        local_results = []
        local_prices = []

        for item in soup.select(".s-item"):
            try:
                title_elem = item.select_one(".s-item__title > span") or item.select_one(".s-item__title")
                title = title_elem.get_text(strip=True) if title_elem else "No Title"
                price_elem = item.select_one(".s-item__price")
                price_text = price_elem.get_text(strip=True) if price_elem else "No Price"
                price_value = float(price_text.replace("$", "").replace(",", "")) if price_text.startswith("$") else None
                local_prices.append(price_value)
                image_elem = item.select_one(".s-item__image img")
                image_url = image_elem.get("src") if image_elem else "No Image"
                link_elem = item.select_one(".s-item__link")
                item_url = link_elem.get("href") if link_elem else "No Link"
                local_results.append({
                    "title": title,
                    "price": price_text,
                    "price_value": price_value,
                    "image_url": image_url,
                    "item_url": item_url,
                    "display_image": f"![Image]({image_url})",
                })
            except Exception as e:
                console.error(f"Skipping item due to error: {e}")

        with self.lock:
            self.results.extend(local_results)
            self.prices.extend(local_prices)

    def scrape_ebay_sold(self, query, condition="", specifics="", min_price=None, max_price=None, exclude_parts=True):
        query_encoded = urllib.parse.quote_plus(query)
        specifics_encoded = urllib.parse.quote_plus(specifics) if specifics else ""
        self.results = []
        self.prices = []
        num_pages = getattr(settings, "SCRAPER_NUM_PAGES", 5)
        threads = []
        for page in range(1, num_pages + 1):
            thread = threading.Thread(target=self.scrape_page, args=(query_encoded, condition, specifics_encoded, page, exclude_parts))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        self.results = detect_price_outliers(self.results)
        return self.results

scraper = EbayScraper()