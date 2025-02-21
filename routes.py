from fastapi import APIRouter, Query
from scraper.ebay_scraper import scraper
from utils.log_manager import console
from scraper.ebay_poster import list_item_on_ebay
router = APIRouter()

@router.get("/sold-items")
def get_sold_items(
    q: str = Query(..., title="Search Query", description="Enter eBay search query"),
    condition: str = Query("", title="Condition", description="eBay condition filter (e.g., New=1000, Used=3000)"),
    specifics: str = Query("", title="Item Specifics", description="Additional search filters like brand, storage size, etc."),
    min_price: float = Query(None, title="Min Price", description="Minimum price filter"),
    max_price: float = Query(None, title="Max Price", description="Maximum price filter"),
):
    """API endpoint to fetch sold eBay items."""
    console.info("/Sold-items endpoint called, fetching results.")
    results = scraper.scrape_ebay_sold(q, condition, specifics, min_price, max_price)
    return {"search_query": q, "results": results}

@router.post("/list-item")
def post_item(item_data: dict):
    """API endpoint to list an item on eBay."""
    result = list_item_on_ebay(item_data)
    return result
