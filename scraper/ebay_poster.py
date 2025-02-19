import os
import json
import requests
from fastapi import HTTPException

# eBay API Credentials (Must be configured in the environment variables)
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_ACCESS_TOKEN = os.getenv("EBAY_ACCESS_TOKEN")

# eBay Listing API URL
EBAY_LISTING_URL = "https://api.ebay.com/sell/inventory/v1/inventory_item"


def check_missing_specifics(item_data: dict, required_specifics: list):
    """
    Checks for missing item specifics and returns them.
    """
    missing_specifics = {}
    for specific in required_specifics:
        if specific not in item_data or not item_data[specific]:
            missing_specifics[specific] = "MISSING"
    return missing_specifics


def list_item_on_ebay(item_data: dict):
    """
    Posts an item to eBay after validating specifics.
    """
    required_specifics = ["brand", "model", "condition", "color", "storage_capacity"]
    missing_specifics = check_missing_specifics(item_data, required_specifics)

    if missing_specifics:
        return {"status": "missing_specifics", "missing_details": missing_specifics}

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(EBAY_LISTING_URL, headers=headers, json=item_data)
    if response.status_code == 201:
        return {"status": "success", "message": "Item listed successfully", "response": response.json()}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)