import requests
import base64
import re

# eBay API credentials (replace with your actual keys)
CLIENT_ID = "RobitRep-SnapNSel-PRD-8298f5758-ea82f57f"
CLIENT_SECRET = "c8f5f942-c595-4548-9166-207db4bcb30a"
REDIRECT_URI = "https://snap-n-sell.duckdns.org/auth/accepted"
EBAY_ENV = "PRODUCTION"

# OAuth endpoints
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token" if EBAY_ENV == "PRODUCTION" else "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

def get_ebay_access_token():
    """Obtain an OAuth2 token from eBay."""
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data)

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get OAuth token: {response.text}")

def sanitize_sku(sku):
    """Ensure SKU is valid by removing special characters and truncating if necessary."""
    sku = re.sub(r'[^a-zA-Z0-9]', '', sku)  # Remove non-alphanumeric characters
    return sku[:50]  # Trim to max 50 characters

def post_ebay_inventory_item(sku, title, price):
    """Post an item to eBay using a valid OAuth2 token."""
    access_token = get_ebay_access_token()  # Get a fresh OAuth2 token
    url = f"https://api.ebay.com/sell/inventory/v1/inventory_item/{sanitize_sku(sku)}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "sku": sanitize_sku(sku),
        "product": {
            "title": title
        },
        "price": {
            "value": price,
            "currency": "USD"
        }
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
