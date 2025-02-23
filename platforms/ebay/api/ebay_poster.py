import requests
from config.oauth2_manager import get_auth_url, fetch_tokens, refresh_access_token
import json
import re

# eBay API credentials (replace with your actual keys)
from config.oauth2_manager import load_tokens, save_tokens, refresh_access_token

# OAuth endpoints
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token" if EBAY_ENV == "PRODUCTION" else "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

# Load tokens from a local file or environment
TOKEN_STORAGE = os.getenv("TOKEN_STORAGE_PATH", "config/ebay_tokens.json")
def load_tokens():
    try:
        with open(TOKEN_STORAGE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_tokens(tokens):
    with open(TOKEN_STORAGE, "w") as file:
        json.dump(tokens, file)

def get_ebay_access_token():
    tokens = load_tokens()
    
    if "access_token" in tokens:
        return tokens["access_token"]
    
    if "refresh_token" in tokens:
        return refresh_access_token(tokens["refresh_token"])
    
    raise Exception("No valid access or refresh token found. Authenticate the application first.")

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