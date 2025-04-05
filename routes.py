import requests
from fastapi import APIRouter, Query, Request
from http.client import HTTPException
from platforms.ebay.api.ebay_poster import post_ebay_inventory_item, sanitize_sku, create_ebay_offer, publish_ebay_offer
from platforms.ebay.automation.ebay_scraper import scraper
from platforms.ebay.automation.ebay_web_poster import post_item_stealth
from platforms.ebay.security.oauth2_manager import auth_accepted, get_ebay_access_token
from platforms.mercari.automation import mercari_scraper
from pydantic import BaseModel
from starlette.responses import RedirectResponse
from utils.log_manager import console

router = APIRouter()


async def capture_state_and_redirect(request: Request):
    """Handles initial state validation and redirects to /auth/accepted."""
    auth_code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not state or not auth_code:
        raise HTTPException()

    # Redirect to `/auth/accepted` with the authorization code
    return RedirectResponse(url=f"/auth/accepted?code={auth_code}&state={state}")


@router.get("/auth/accepted")
@router.get("/")
async def ebay_auth_accepted(request: Request):
    """Handles eBay OAuth callback and exchanges the auth code for an access token."""
    response = await auth_accepted(request)
    return response


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
    return results


@router.get("/mercari-sold-items")
def get_mercari_sold_items(
    q: str = Query(..., title="Search Query", description="Enter Mercari search query"),
    num_pages: int = Query(
        3, title="Number of Pages", description="Number of pages to scrape"
    ),
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
        sanitized_sku,
        request.title,
        request.price,
        request.condition,
        request.specifics,
    )

    if not response:
        return {"status": "unauthenticated", "response": response.get("response")}

    offer_response = create_ebay_offer(sanitized_sku, request.price)
    if "offerId" not in offer_response:
        return {"status": "error", "message": "Failed to create offer", "response": offer_response}

    publish_response = publish_ebay_offer(offer_response["offerId"])
    return {"status": "success", "response": publish_response}
    sku: str
    title: str
    price: float
    condition: str = "New"
    specifics: dict = {}  # Can support any nested item specifics dynamically
# Clone of SellItemRequest for the stealth route

@router.post("/sell-item-stealth")
async def sell_item_stealth(request: SellItemRequest):
    """Post eBay item using full stealth Botasaurus browser automation."""
    console.info("/sell-item-stealth endpoint called")
    try:
        result = post_item_stealth(
            sku=request.sku,
            title=request.title,
            price=request.price,
            condition=request.condition,
            specifics=request.specifics,
        )
        return {"status": "success", "result": result}
    except Exception as e:
        console.error(f"Botasaurus stealth post failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/listings")
async def get_active_listings():
    """Fetch all active eBay listings (not just inventory)."""
    access_token = get_ebay_access_token()
    url = "https://api.ebay.com/sell/inventory/v1/offer?format=FIXED_PRICE"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    return response.json()


@router.get("/drafts")
async def get_draft_listings():
    """Fetch all eBay draft listings."""
    access_token = get_ebay_access_token()
    url = "https://api.ebay.com/sell/inventory/v1/inventory_item?listingStatus=DRAFT"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

    response = requests.get(url, headers=headers)
    return response.json()


@router.put("/modify-listing/{listing_id}")
async def modify_ebay_listing(listing_id: str, updated_data: dict):
    """Modify an active eBay listing."""
    access_token = get_ebay_access_token()
    url = f"https://api.ebay.com/sell/inventory/v1/inventory_item/{listing_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.put(url, json=updated_data, headers=headers)
    return response.json()

@router.get("/listing/{listing_id}")
async def get_ebay_listing(listing_id: str):
    """Fetch details of a specific eBay listing."""
    access_token = get_ebay_access_token()
    url = f"https://api.ebay.com/sell/inventory/v1/inventory_item/{listing_id}"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

    response = requests.get(url, headers=headers)
    return response.json()
