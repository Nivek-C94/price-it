import threading
import urllib.parse
import logging
import re
import os
import queue

from botasaurus_driver import driver
from botasaurus_driver.core import config
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import settings
from utils.log_manager import console
from utils.utils import detect_price_outliers


def get_fixed_linux_executable_path():
    """
    Determines the Chrome executable to use.
    First, it checks the CHROME_PATH environment variable.
    If not set or the file does not exist, it searches common paths.
    """
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

    console.error(
        "Chrome executable not found. Please set the CHROME_PATH environment variable to a valid Chrome binary path."
    )
    return ""


# Override Botasaurus's default function for obtaining the Chrome binary path.
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
        """Initialize a fixed number of persistent Botasaurus drivers."""
        num_drivers = getattr(settings, "SCRAPER_NUM_DRIVERS", 3)
        console.info(f"Spawning {num_drivers} persistent Botasaurus drivers...")
        for _ in range(num_drivers):
            try:
                bot = driver.Driver(user_agent=UserAgent().random, headless=True)
                self.driver_pool.put(bot)
            except Exception as e:
                console.error(f"Error initializing a driver: {e}")
        console.info("All drivers initialized and ready for requests.")

    def _check_driver_health(self, bot):
        """Ensure the driver is still running and responsive."""
        try:
            bot.get("about:blank")  # Quick health check
            return True
        except Exception:
            console.error("A Botasaurus driver has failed and will be replaced.")
            return False

    def scrape_page(
        self, query, condition="", specifics="", page=1, exclude_parts=True
    ):
        condition_filter = f"&LH_ItemCondition={condition}" if condition else ""
        specifics_filter = f"&_sop=12&{specifics}" if specifics else ""
        url = f"{self.base_url}?_nkw={query}&LH_Sold=1&LH_Complete=1{condition_filter}{specifics_filter}&_pgn={page}"

        # Acquire a driver from the pool
        try:
            bot = self.driver_pool.get(timeout=10)
        except queue.Empty:
            console.error("No available drivers in pool.")
            return

        try:
            bot.get(url)
            bot.wait_for_element(".s-item")
            html_source = bot.page_html
        except Exception as e:
            console.error(f"Error fetching page {page}: {e}")
            try:
                bot.close()
            except Exception:
                pass
            try:
                new_bot = driver.Driver(user_agent=UserAgent().random, headless=True)
                self.driver_pool.put(new_bot)
            except Exception as e:
                console.error(f"Error reinitializing driver: {e}")
            return
        else:
            # Return the driver to the pool if healthy; else, replace it.
            if self._check_driver_health(bot):
                self.driver_pool.put(bot)
            else:
                try:
                    bot.close()
                except Exception:
                    pass
                try:
                    new_bot = driver.Driver(
                        user_agent=UserAgent().random, headless=True
                    )
                    self.driver_pool.put(new_bot)
                except Exception as e:
                    console.error(f"Error reinitializing driver: {e}")

        soup = BeautifulSoup(html_source, "html.parser")
        local_results = []
        local_prices = []

        items = soup.select(".s-item")
        for item in items:
            try:
                title_elem = item.select_one(
                    ".s-item__title > span"
                ) or item.select_one(".s-item__title")
                title = title_elem.get_text(strip=True) if title_elem else "No Title"
                title = re.sub(r"^New Listing", "", title).strip()

                if (
                    "Shop on eBay" in title
                    or "iPhone 7" in title
                    or "iPhone 8" in title
                ):
                    continue

                price_elem = item.select_one(".s-item__price")
                price_text = (
                    price_elem.get_text(strip=True) if price_elem else "No Price"
                )
                price_value = None
                if price_text.startswith("$"):
                    try:
                        price_value = float(
                            price_text.replace("$", "").replace(",", "")
                        )
                        local_prices.append(price_value)
                    except ValueError:
                        pass

                specifics_elem = item.select_one(".s-item__subtitle")
                specifics_text = (
                    specifics_elem.get_text(strip=True)
                    if specifics_elem
                    else "No Details"
                )
                condition_text = (
                    specifics_text.split("\u00b7")[0].strip()
                    if "\u00b7" in specifics_text
                    else specifics_text
                )

                if exclude_parts and "Parts Only" in condition_text:
                    continue

                image_elem = item.select_one(".s-item__image img")
                image_url = image_elem.get("src") if image_elem else "No Image"

                link_elem = item.select_one(".s-item__link")
                item_url = link_elem.get("href") if link_elem else "No Link"

                local_results.append(
                    {
                        "title": title,
                        "price": price_text,
                        "price_value": price_value,
                        "condition": condition_text,
                        "image_url": image_url,
                        "item_url": item_url,
                        "specifics": specifics_text,
                        "display_image": f"![Image]({image_url})",
                    }
                )
            except Exception as e:
                console.error(f"Skipping item due to error: {e}")

        with self.lock:
            self.results.extend(local_results)
            self.prices.extend(local_prices)

    def scrape_ebay_sold(
        self,
        query,
        condition="",
        specifics="",
        min_price=None,
        max_price=None,
        exclude_parts=True,
    ):
        query_encoded = urllib.parse.quote_plus(query)
        specifics_encoded = urllib.parse.quote_plus(specifics) if specifics else ""
        self.results = []
        self.prices = []

        num_pages = getattr(settings, "SCRAPER_NUM_PAGES", 5)
        threads = []
        for page in range(1, num_pages + 1):
            thread = threading.Thread(
                target=self.scrape_page,
                args=(query_encoded, condition, specifics_encoded, page, exclude_parts),
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.results = detect_price_outliers(self.results)

        if min_price is not None or max_price is not None:
            self.results = [
                item
                for item in self.results
                if (
                    min_price is None
                    or (
                        item["price_value"] is not None
                        and item["price_value"] >= min_price
                    )
                )
                and (
                    max_price is None
                    or (
                        item["price_value"] is not None
                        and item["price_value"] <= max_price
                    )
                )
            ]

        return self.results


scraper = EbayScraper()
