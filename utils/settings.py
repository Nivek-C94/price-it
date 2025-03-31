# Configuration settings

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}

# Number of pages to scrape on eBay (can be adjusted)
SCRAPER_NUM_PAGES = 1
# Number of Botasaurus drivers to spawn at startup
SCRAPER_NUM_DRIVERS = 1
# Outlier detection multiplier for the IQR method (default 1.5)
OUTLIER_IQR_MULTIPLIER = 1.5
# eBay maketplace ID
EBAY_MARKETPLACE_ID = "EBAY_US"