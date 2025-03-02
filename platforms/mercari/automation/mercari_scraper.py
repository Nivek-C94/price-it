import threading
import urllib.parse
import queue
import re
from botasaurus_driver import driver
from botasaurus_driver.core import config
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from utils.log_manager import console
from utils.utils import detect_price_outliers
from config import settings

class MercariScraper:
    def __init__(self):
        self.base_url = "https://www.mercari.com/search/"
        self.lock = threading.Lock()
        self.driver_pool = queue.Queue()
        self.results = []
        self._initialize_drivers()

    def _initialize_drivers(self):
        num_drivers = getattr(settings, "SCRAPER_NUM_DRIVERS", 3)
        console.info(f"Spawning {num_drivers} persistent Botasaurus drivers for Mercari...")
        for _ in range(num_drivers):
            try:
                bot = driver.Driver(user_agent=UserAgent().random, headless=True)
                self.driver_pool.put(bot)
            except Exception as e:
                console.error(f"Error initializing a driver: {e}")
        console.info("All drivers initialized for Mercari scraping.")

    def scrape_page(self, query, page=1):
        query_encoded = urllib.parse.quote_plus(query)
        url = f"{self.base_url}?keyword={query_encoded}&status=sold&page={page}"
        
        try:
            bot = self.driver_pool.get(timeout=10)
        except queue.Empty:
            console.error("No available drivers in pool for Mercari.")
            return
        
        try:
            bot.get(url)
            bot.wait_for_element(".items-box")
            html_source = bot.page_html
        except Exception as e:
            console.error(f"Error fetching page {page}: {e}")
            return
        finally:
            self.driver_pool.put(bot)

        soup = BeautifulSoup(html_source, "html.parser")
        local_results = []
        
        items = soup.select(".items-box")
        for item in items:
            try:
                title_elem = item.select_one(".items-box-name")
                title = title_elem.get_text(strip=True) if title_elem else "No Title"

                price_elem = item.select_one(".items-box-price")
                price_text = price_elem.get_text(strip=True) if price_elem else "No Price"
                price_value = None
                if price_text.startswith("$"):
                    try:
                        price_value = float(price_text.replace("$", "").replace(",", ""))
                    except ValueError:
                        pass

                image_elem = item.select_one(".items-box-photo img")
                image_url = image_elem.get("src") if image_elem else "No Image"

                link_elem = item.select_one("a")
                item_url = f"https://www.mercari.com{link_elem.get('href')}" if link_elem else "No Link"
                
                local_results.append({
                    "title": title,
                    "price": price_text,
                    "price_value": price_value,
                    "image_url": image_url,
                    "item_url": item_url,
                })
            except Exception as e:
                console.error(f"Skipping item due to error: {e}")
        
        with self.lock:
            self.results.extend(local_results)

    def scrape_mercari_sold(self, query, num_pages=3):
        self.results = []
        threads = []
        
        for page in range(1, num_pages + 1):
            thread = threading.Thread(target=self.scrape_page, args=(query, page))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        return detect_price_outliers(self.results)

scraper = MercariScraper()