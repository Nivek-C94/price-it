from fastapi import APIRouter, Query
from platforms.ebay.api.ebay_poster import post_ebay_inventory_item
from platforms.ebay.automation.ebay_scraper import scraper
from utils.log_manager import console

router = APIRouter()

@router.get("/sold-items")
def get_sold_items(
    q: str = Query(..., title="Search Query", description="Enter eBay search query"),
    condition: str = Query(
        "",
        title="Condition",
        description="eBay condition filter (e.g., New=1000, Used=3000)",
    ),
    specifics: str = Query(
        "",
        title="Item Specifics",
        description="Additional search filters like brand, storage size, etc.",
    ),
    min_price: float = Query(
        None, title="Min Price", description="Minimum price filter"
    ),
    max_price: float = Query(
        None, title="Max Price", description="Maximum price filter"
    ),
):
    """API endpoint to fetch sold eBay items."""
    console.info("/Sold-items endpoint called, fetching results.")
    results = scraper.scrape_ebay_sold(q, condition, specifics, min_price, max_price)

@router.get("/mercari-sold-items")
def get_mercari_sold_items(
    q: str = Query(..., title="Search Query", description="Enter Mercari search query"),
    num_pages: int = Query(3, title="Number of Pages", description="Number of pages to scrape"),
):
    """API endpoint to fetch sold Mercari items."""
    console.info("/mercari-sold-items endpoint called, fetching results.")
    results = mercari_scraper.scrape_mercari_sold(q, num_pages)
    return {"search_query": q, "results": results}

@router.post("/sell-item")
def sell_item(
    sku: str = Query(..., title="SKU", description="Stock Keeping Unit for eBay"),
    title: str = Query(..., title="Item Title", description="Title of the item to sell"),
    price: float = Query(..., title="Price", description="Price of the item in USD"),
    condition: str = Query("New", title="Condition", description="Condition of the item"),
    specifics: dict = Query({}, title="Item Specifics", description="Additional details such as brand, color, etc."),
):
):
    """API endpoint to post an item for sale on eBay."""
    console.info(f"/sell-item endpoint called: SKU={sku}, Title={title}, Price={price}, Condition={condition}, Specifics={specifics}")
    sanitized_sku = sanitize_sku(sku)
    response = post_ebay_inventory_item(sanitized_sku, title, price, condition, specifics)
    return {"status": "success", "response": response}
