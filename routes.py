from http.client import HTTPException

import httpx as httpx
from fastapi import APIRouter, Query,  Request  # Import Body
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from config import oauth2_manager
from platforms.ebay.api.ebay_poster import post_ebay_inventory_item, sanitize_sku
from platforms.ebay.automation.ebay_scraper import scraper
from platforms.mercari.automation import mercari_scraper
from utils.log_manager import console

router = APIRouter()


async def capture_state_and_redirect(request: Request):
    """Handles initial state validation and redirects to /auth/accepted."""
    state = request.query_params.get("state")
    auth_code = request.query_params.get("code")

    if not state or not auth_code:
        raise HTTPException()

    # Redirect to `/auth/accepted` with the authorization code
    return RedirectResponse(url=f"/auth/accepted?code={auth_code}&state={state}")


@router.get("/auth/accepted")
@router.get("/")
async def ebay_auth_accepted(request: Request):
    """Handles eBay OAuth callback and exchanges the auth code for an access token."""
    response = await oauth2_manager.auth_accepted(request)
    print(response)
    return response


@router.get("/auth/accepted")
async def ebay_auth_accepted(request: Request):
    """Handles eBay OAuth callback and exchanges the auth code for an access token."""
    access_token, refresh_token, expires_in = await oauth2_manager.auth_accepted(request)
    return {"access_token": access_token, "refresh_token": refresh_token, "expires_in": expires_in}



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

# Define the request model properly
class SellItemRequest(BaseModel):
    sku: str
    title: str
    price: float
    condition: str = "New"
    specifics: dict = {}

@router.post("/sell-item")
async def sell_item(request: SellItemRequest):
    """API endpoint to post an item for sale on eBay."""
    console.info(f"/sell-item endpoint called: {request}")

    sanitized_sku = sanitize_sku(request.sku)
    response = post_ebay_inventory_item(
        sanitized_sku, request.title, request.price, request.condition, request.specifics
    )

    if not response.get("success", False):
        return {"status": "unauthenticated", "response": response}

    return {"status": "success", "response": response}

