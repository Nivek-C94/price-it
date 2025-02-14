import threading
import time
import random
from botasaurus_driver import driver
from scraper.utils import detect_price_outliers

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
    
    def scrape_page(page_num):
        """Threaded function to scrape a single page."""
        params["_pgn"] = page_num
        response = requests.get(base_url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select(".s-item")
            
            for item in items:
                title = item.select_one(".s-item__title")
                price = item.select_one(".s-item__price")
                image = item.select_one(".s-item__image-img")
                link = item.select_one(".s-item__link")
                condition = item.select_one(".s-item__subtitle span")
                
                result = {
                    "title": title.text.strip() if title else "No Title",
                    "price": price.text.strip() if price else "No Price",
                    "image_url": image["src"] if image else "No Image",
                    "item_url": link["href"] if link else "No Link",
                    "condition": condition.text.strip() if condition else "Unknown"
                }
                results.append(result)
        
        time.sleep(random.uniform(1, 3))  # Randomized delay for anti-detection
    
    threads = []
    for page in range(1, 5):  # Scrape first 5 pages
        thread = threading.Thread(target=scrape_page, args=(page,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    return detect_price_outliers(results)