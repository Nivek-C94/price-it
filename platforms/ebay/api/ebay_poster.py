import json
import re
import requests
import time
from config import oauth2_manager
from config.oauth2_manager import get_ebay_access_token

def sanitize_sku(sku):
    """Ensure SKU is valid by removing special characters and truncating if necessary."""
    sku = re.sub(r"[^a-zA-Z0-9]", "", sku)  # Remove non-alphanumeric characters
    return sku[:50]  # Trim to max 50 characters


def post_ebay_inventory_item(sku, title, price, condition, specifics):
    """Post an item to eBay using a valid OAuth2 token."""
    access_token = get_ebay_access_token()

    # Check if authentication is required
    if isinstance(access_token, dict) and "status" in access_token and access_token["status"] == "unauthenticated":
        print(f"❌ Authentication required: {access_token['message']}")
        print(f"🔗 Please log in here: {access_token['oauth_url']}")
        return {"success": False, "response": access_token}

    sku = sanitize_sku(sku)  # Sanitize SKU once

    url = f"https://api.ebay.com/sell/inventory/v1/inventory_item/{sku}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "sku": sku,
        "product": {"title": title, "aspects": specifics, "conditionDescriptors": [str(condition)]},
        "availability": {"shipToLocationAvailability": {"quantity": 1}},
        "price": {"value": price, "currency": "USD"},
        "marketplaceId": "EBAY_US"
    }

    for attempt in range(3):
        response = requests.put(url, json=data, headers=headers)

        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text

        if response.status_code in [200, 201, 204]:
            print("✅ Item posted successfully:", response_data)
            return {"success": True, "response": response_data}

        elif response.status_code in [500, 502, 503, 504]:
            print(f"⚠️ Temporary error ({response.status_code}). Retrying in {2**attempt} seconds...")
            time.sleep(2**attempt)
        else:
            break  # Other errors should not be retried

    print("🚨 Error posting item:", response_data)
    return {"success": False, "response": response_data}



if __name__ == "__main__":
    try:
        post_ebay_inventory_item("Test SKU!@#123", "Sample eBay Item", "19.99")
    except Exception as e:
        print("Error:", e)
