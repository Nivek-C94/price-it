import threading
from botasaurus_driver import driver
from bs4 import BeautifulSoup
import statistics
import re

class EbayScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.lock = threading.Lock()
        self.results = []
        self.prices = []

    def scrape_page(self, query, condition, specifics, page, exclude_parts):
        condition_filter = f"&LH_ItemCondition={condition}" if condition else ""
        specifics_filter = f"&_sop=12&{specifics.replace(' ', '+')}" if specifics else ""
        url = f"{self.base_url}?_nkw={query}&LH_Sold=1&LH_Complete=1{condition_filter}{specifics_filter}&_pgn={page}"

        bot = driver.Driver()
        bot.get(url)
        bot.wait_for_element(".s-item")
        html_source = bot.page_html
        soup = BeautifulSoup(html_source, "html.parser")

        local_results = []
        local_prices = []

        items = soup.select(".s-item")
        for item in items:
            try:
                title_elem = item.select_one(".s-item__title > span") or item.select_one(".s-item__title")
                title = title_elem.get_text(strip=True) if title_elem else "No Title"
                title = re.sub(r"^New Listing", "", title).strip()
                
                if "Shop on eBay" in title or "iPhone 7" in title or "iPhone 8" in title:
                    continue  # Ignore irrelevant models
                
                price_elem = item.select_one(".s-item__price")
                price_text = price_elem.get_text(strip=True) if price_elem else "No Price"
                price_value = None
                if price_text.startswith("$"):
                    try:
                        price_value = float(price_text.replace("$", "").replace(",", ""))
                        local_prices.append(price_value)
                    except ValueError:
                        pass
                
                specifics_elem = item.select_one(".s-item__subtitle")
                specifics_text = specifics_elem.get_text(strip=True) if specifics_elem else "No Details"
                condition = specifics_text.split("·")[0].strip() if "·" in specifics_text else specifics_text
                
                if exclude_parts and "Parts Only" in condition:
                    continue  # Skip parts-only listings if specified
                
                image_elem = item.select_one(".s-item__image img")
                image_url = image_elem.get("src") if image_elem else "No Image"
                
                link_elem = item.select_one(".s-item__link")
                item_url = link_elem.get("href") if link_elem else "No Link"
                
                local_results.append({
                    "title": title,
                    "price": price_text,
                    "price_value": price_value,
                    "condition": condition,
                    "image_url": image_url,
                    "item_url": item_url,
                    "specifics": specifics_text,
                    "display_image": f"![]({image_url})"
                })
            except Exception as e:
                print(f"Skipping item due to error: {e}")

        with self.lock:
            self.results.extend(local_results)
            self.prices.extend(local_prices)

        bot.close()

    def scrape_ebay_sold(self, query, condition="", specifics="", min_price=None, max_price=None, exclude_parts=True):
        query = query.replace(" ", "+")
        self.results = []
        self.prices = []

        num_pages = 5
        threads = []
        for page in range(1, num_pages + 1):
            thread = threading.Thread(target=self.scrape_page, args=(query, condition, specifics, page, exclude_parts))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if self.prices:
            avg_price = statistics.mean(self.prices)
            std_dev = statistics.stdev(self.prices) if len(self.prices) > 1 else 0
            for item in self.results:
                if item["price_value"] is not None:
                    deviation = abs(item["price_value"] - avg_price)
                    item["outlier"] = deviation > (1.2 * std_dev)  # Adjusted threshold

        if min_price is not None or max_price is not None:
            self.results = [item for item in self.results if (min_price is None or item["price_value"] >= min_price) and (max_price is None or item["price_value"] <= max_price)]
        
        return self.results
        
        return self.results

scraper = EbayScraper()