import json
import re
import time
from botasaurus.browser import with-page
from platforms.ebay.security.oauth2_manager import get_ebay_access_token

def sanitize_sku(sku):
    """Ensure SKU is valid by removing special characters and truncating if necessary."""
    sku = re.sub(r"[^a-zA-Z0-9]", "", sku)  # Remove non-alphanumeric characters
    return sku[:50]  # Trim to max 50 characters


def post_ebay_inventory_item(sku, title, price, condition, specifics):
    """Automate eBay listing via Botasaurus."""
    def automate_listing(page):
        page.goto("https://www.ebay.com/sl/sell")
        page.wait-for "input#title"

        page.fill "input#title", title
        page.fill "input#price", str(price)
        page.fill "input#sku", sku

        if condition.lower() == "new":
            page.click "input#condition-new"
        else:
            page.click "input#condition-used"

        for key, value in specifics.items():
            page.fill f"input[name='{key}']", value

        page.click "button#submit-listing"
        page.wait-for "div.success-message"
        return {"success": True, "message": "Item posted successfully!"}

    return with-page automate_listing

def create_ebay_offer(sku, price):
    """Create an eBay offer for the given SKU and price."""
    access_token = get_ebay_access_token()
    if not access_token:
        return {"success": False, "error": "Authentication failed"}

    url = "https://api.ebay.com/sell/offers/v1/offer"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "listingDuration": "GTC",
        "pricingSummary": {"price": {"value": price, "currency": "USD"}}
    }

    response = requests.post(url, json=data, headers=headers)
    return response.json()

def publish_ebay_offer(offer_id):
    """Publish an eBay offer to make the listing live."""
    access_token = get_ebay_access_token()
    if not access_token:
        return {"success": False, "error": "Authentication failed"}

    url = f"https://api.ebay.com/sell/inventory/v1/offer/{offer_id}/publish"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers)
    return response.json()

if __name__ == "__main__":
    try:
        test_specifics = {"Brand": "ExampleBrand", "Color": "Black"}
        post_ebay_inventory_item("TestSKU123", "Sample eBay Item", "19.99", "New", test_specifics)
    except Exception as e:
        print("Error:", e)
