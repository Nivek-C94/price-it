from fastapi import APIRouter, Query
from scraper.ebay_scraper import scrape_ebay_sold

router = APIRouter()

@router.get("/sold-items")
def get_sold_items(
    q: str = Query(..., title="Search Query", description="Enter eBay search query"),
    condition: str = Query(None, title="Condition", description="Filter by item condition (e.g., New, Used)"),
    min_price: float = Query(None, title="Min Price", description="Filter by minimum price"),
    max_price: float = Query(None, title="Max Price", description="Filter by maximum price"),
):
    """API endpoint to fetch sold eBay items."""
    results = scrape_ebay_sold(q, condition, min_price, max_price)
    return {"search_query": q, "results": results}