# Price-It: eBay Sold Listings Scraper

## Overview
Price-It is a FastAPI-based web scraper that fetches sold eBay listings efficiently using threading, Botasaurus, and BeautifulSoup.

## Features
- Multi-threaded scraping for improved performance.
- Filters by item condition, min/max price, and other specifics.
- Detects price outliers using statistical methods.
- Parses images, titles, and links correctly.

## Installation
```sh
git clone https://github.com/Nivek-C94/price-it.git
cd price-it
pip install -r requirements.txt
```

## Usage
```sh
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

Access the API at `http://localhost:3000/sold-items?q=iphone+12`

## API Endpoints
- **`/sold-items`**: Fetches sold listings based on search query and optional filters.