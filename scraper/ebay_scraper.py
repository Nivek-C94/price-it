import threading
import time
import random
from botasaurus_driver import driver
from bs4 import BeautifulSoup
import statistics
import re

def scrape_ebay_sold(query, condition=None, min_price=None, max_price=None):
    """Scrape eBay sold listings with threading and filters."""
    base_url = "https://www.ebay.com/sch/i.html"
    params = {
        "_nkw": query.replace(" ", "+"),
        "LH_Sold": 1,
        "LH_Complete": 1,
        "_ipg": 100  # Get 100 items per page for efficiency
    }
    if condition:
        params["LH_ItemCondition"] = condition
    
    results = []
    prices = []
    lock = threading.Lock()
    
    def scrape_page(page_num):
        """Threaded function to scrape a single page."""
        params["_pgn"] = page_num
        bot = driver.Driver()
        bot.get(f"{base_url}?_nkw={params['_nkw']}&LH_Sold=1&LH_Complete=1&LH_ItemCondition={params.get('LH_ItemCondition', '')}&_pgn={page_num}")
        bot.wait_for_element(".s-item")
        html_source = bot.page_source()
        soup = BeautifulSoup(html_source, "html.parser")
        
        local_results = []
        local_prices = []
        
        items = soup.select(".s-item")
        for item in items:
            try:
                title_elem = item.select_one(".s-item__title > span") or item.select_one(".s-item__title")
                title = title_elem.get_text(strip=True) if title_elem else "No Title"
                title = re.sub(r"^New Listing", "", title).strip()
                
                if "Shop on eBay" in title:
                    continue  # Ignore invalid results
                
                price_elem = item.select_one(".s-item__price")
                price_text = price_elem.get_text(strip=True) if price_elem else "No Price"
                price_value = None
                if price_text.startswith("$"):
                    try:
                        price_value = float(price_text.replace("$", "").replace(",", ""))
                        local_prices.append(price_value)
                    except ValueError:
                        pass
                
                image_elem = item.select_one(".s-item__image img")
                image_url = image_elem.get("src") if image_elem else "No Image"
                
                link_elem = item.select_one(".s-item__link")
                item_url = link_elem.get("href") if link_elem else "No Link"
                
                specifics_elem = item.select_one(".s-item__subtitle")
                specifics_text = specifics_elem.get_text(strip=True) if specifics_elem else "No Details"
                condition = specifics_text.split("·")[0].strip() if "·" in specifics_text else specifics_text
                
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
        
        with lock:
            results.extend(local_results)
            prices.extend(local_prices)
        
        time.sleep(random.uniform(1, 3))  # Randomized delay for anti-detection
    
    threads = []
    for page in range(1, 5):  # Scrape first 5 pages
        thread = threading.Thread(target=scrape_page, args=(page,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    if prices:
        avg_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
        for item in results:
            if item["price_value"] is not None:
                deviation = abs(item["price_value"] - avg_price)
                item["outlier"] = deviation > (1.5 * std_dev)
    
    return results