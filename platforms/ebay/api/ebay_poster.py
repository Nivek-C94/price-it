import requests
import json
import re
import time

from config import oauth2_manager
from config.oauth2_manager import get_ebay_access_token


def sanitize_sku(sku):
    """Ensure SKU is valid by removing special characters and truncating if necessary."""
    sku = re.sub(r"[^a-zA-Z0-9]", "", sku)  # Remove non-alphanumeric characters
    return sku[:50]  # Trim to max 50 characters


def post_ebay_inventory_item(sku, title, price):
    """Post an item to eBay using a valid OAuth2 token."""
    access_token = get_ebay_access_token()  # Get a fresh OAuth2 token
    url = f"https://api.ebay.com/sell/inventory/v1/inventory_item/{sanitize_sku(sku)}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "sku": sanitize_sku(sku),
        "product": {"title": title},
        "price": {"value": price, "currency": "USD"},
    }

    response = requests.put(url, json=data, headers=headers)

    if response.status_code in [200, 201]:
        print("Item posted successfully:", response.json())
    else:
        print("Error:", response.text)


if __name__ == "__main__":
    try:
        post_ebay_inventory_item("Test SKU!@#123", "Sample eBay Item", "19.99")
    except Exception as e:
        print("Error:", e)
