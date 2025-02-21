import os
import json
import requests
from fastapi import HTTPException

# eBay OAuth Credentials (Set in environment variables)
EBAY_CLIENT_ID = "RobitRep-SnapNSel-PRD-8298f5758-ea82f57f"
EBAY_CLIENT_SECRET = "PRD-298f5758b408-05cb-47f5-bc2b-dc80"
EBAY_REFRESH_TOKEN = ""# eBay API URLs
EBAY_OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_LISTING_URL = "https://api.ebay.com/sell/listing/v1/item"

def get_ebay_access_token():
    """
    Retrieves a new OAuth 2.0 access token using the refresh token.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {get_basic_auth_header()}"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": EBAY_REFRESH_TOKEN,
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"
    }

    response = requests.post(EBAY_OAUTH_URL, headers=headers, data=data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        raise HTTPException(status_code=response.status_code, detail=response.json())


def get_basic_auth_header():
    """
    Returns the Base64 encoded Client ID and Secret required for OAuth.
    """
    import base64
    credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    return base64.b64encode(credentials.encode()).decode()


def check_missing_specifics(item_data: dict, required_specifics: list):
    """
    Checks for missing item specifics and returns them.
    """
    missing_specifics = {}
    normalized_item_data = {key.lower(): value for key, value in item_data.items()}  # Normalize keys

    for specific in required_specifics:
        specific_lower = specific.lower()  # Normalize required specifics
        if specific_lower not in normalized_item_data or not normalized_item_data[specific_lower]:
            missing_specifics[specific] = "MISSING"

    return missing_specifics



def list_item_on_ebay(item_data: dict):
    """
    Posts an item to eBay after validating specifics.
    """
    print("\n🚀 Debugging Item Data Before Checking Specifics:")
    print(json.dumps(item_data, indent=2))  # ✅ Print item data for verification

    required_specifics = ["Brand", "Model", "Condition", "Color", "Storage Capacity"]
    missing_specifics = check_missing_specifics(item_data.get("product", {}).get("aspects", {}), required_specifics)

    if missing_specifics:
        return {"status": "missing_specifics", "missing_details": missing_specifics}

    # Get new access token
    EBAY_ACCESS_TOKEN = get_ebay_access_token()

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(EBAY_LISTING_URL, headers=headers, json=item_data)
    if response.status_code == 201:
        return {"status": "success", "message": "Item listed successfully", "response": response.json()}
    else:
        return {"status": "error", "detail": response.json()}

item_data = {
    "sku": "iphone12promax256",
    "product": {
        "title": "Apple iPhone 12 Pro Max - 256GB - Pacific Blue (Unlocked)",
        "description": "Gently used iPhone 12 Pro Max in excellent condition.",
        "aspects": {  # REQUIRED Specifics should be inside "aspects"
            "Brand": ["Apple"],
            "Model": ["iPhone 12 Pro Max"],
            "Condition": ["Used"],  # Ensure format is a LIST
            "Color": ["Pacific Blue"],
            "Storage Capacity": ["256GB"]  # ✅ FIXED: Ensure this is a LIST
        },
        "imageUrls": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg"
        ]
    },
    "availability": {
        "shipToLocationAvailability": {
            "quantity": 1
        }
    },
    "price": {
        "value": "799.99",
        "currency": "USD"
    },
    "condition": "USED_EXCELLENT",
    "categoryId": "9355",
    "merchantLocationKey": "Default",
    "listingPolicies": {
        "fulfillmentPolicyId": "1234567890",  # Replace with actual IDs
        "paymentPolicyId": "1234567890",
        "returnPolicyId": "1234567890"
    }
}
