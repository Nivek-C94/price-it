import re
import time

import requests
import json
from platforms.ebay.security.oauth2_manager import get_ebay_access_token


def get_or_create_policy(policy_type):
    """Checks if an eBay policy exists. If not, retrieves or creates one."""
    access_token = get_ebay_access_token()

    if not access_token:
        print("❌ Error: Unable to retrieve access token.")
        return None

    url = f"https://api.ebay.com/sell/account/v1/{policy_type}_policy"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json"
    }

    # ✅ Step 1: Check for existing policies
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        policies = response.json().get(f"{policy_type}Policies", [])
        if policies:
            print(f"✅ Found existing {policy_type} policy: {policies[0][f'{policy_type}PolicyId']}")
            return policies[0][f"{policy_type}PolicyId"]

    elif response.status_code in [403, 401]:
        print(f"❌ Error: Insufficient permissions to access {policy_type} policies. Check OAuth scopes!")
        return None

    # ✅ Step 2: Create a new policy (only if needed)
    print(f"🚀 Creating {policy_type} policy...")
    create_url = f"https://api.ebay.com/sell/account/v1/{policy_type}_policy"

    category_types = [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}]  # Required format

    policy_data = {
        "marketplaceId": "EBAY_US",
        "name":          f"Auto-{policy_type}-{int(time.time())}",  # ✅ Unique policy name
        "categoryTypes": category_types
    }

    if policy_type == "return":
        policy_data.update({
            "returnMethods":           ["MONEY_BACK"],
            "returnShippingCostPayer": "BUYER",
            "returnsAccepted":         True,
            "returnPeriod":            {"value": 30, "unit": "DAY"}
        })

    elif policy_type == "payment":
        policy_data.update({
            "immediatePay": True
        })

    elif policy_type == "fulfillment":
        policy_data.update({
            "shippingOptions": [{
                "costType":         "FLAT_RATE",
                "optionType":       "DOMESTIC",
                "handlingTime":     {  # 🔥 Fix: Ensure handling time is included
                    "unit":  "DAY",
                    "value": 2
                },
                "shippingServices": [{
                    "shippingServiceCode":    "USPSPriority",
                    "shippingCost":           {"value": "5.00", "currency": "USD"},
                    "additionalShippingCost": {"value": "2.00", "currency": "USD"},
                    "freeShipping":           False
                }]
            }]
        })

    # ✅ Send policy creation request
    response = requests.post(create_url, json=policy_data, headers=headers)
    response_data = response.json()

    if response.status_code in [200, 201]:
        print(f"✅ Successfully created {policy_type} policy: {response_data.get(f'{policy_type}PolicyId')}")
        return response_data.get(f"{policy_type}PolicyId")

    # 🚨 **Handle Duplicate Policy Errors**:
    if response.status_code == 400 and "Duplicate Policy" in response.text:
        duplicate_policy_id = response_data["errors"][0]["parameters"][0]["value"]
        print(f"⚠️ Duplicate {policy_type} policy found: Using existing ID {duplicate_policy_id}")
        return duplicate_policy_id  # Return existing policy ID

    print(f"❌ Error creating {policy_type} policy: {response_data}")
    return None


def sanitize_sku(sku):
    """Ensure SKU is valid by removing special characters and truncating if necessary."""
    sku = re.sub(r"[^a-zA-Z0-9]", "", sku)  # Remove non-alphanumeric characters
    return sku[:50]  # Trim to max 50 characters


def format_aspects(specifics):
    """Ensure all aspects are formatted as lists (required by eBay API)."""
    return {key: [value] if not isinstance(value, list) else value for key, value in specifics.items()}


def post_ebay_inventory_item(sku, title, price, condition, specifics):
    """Post an item to eBay using a valid OAuth2 token with corrected policy handling."""
    access_token = get_ebay_access_token()
    if not access_token:
        return {"success": False, "error": "Authentication failed"}

    sku = re.sub(r"[^a-zA-Z0-9]", "", sku)[:50]  # Sanitize SKU
    formatted_aspects = {key: [value] if not isinstance(value, list) else value for key, value in specifics.items()}

    # ✅ Ensure policies are created BEFORE listing an item
    fulfillment_policy_id = get_or_create_policy("fulfillment")
    payment_policy_id = get_or_create_policy("payment")
    return_policy_id = get_or_create_policy("return")

    if not all([fulfillment_policy_id, payment_policy_id, return_policy_id]):
        print(f"❌ Policy creation failed: "
              f"Fulfillment: {fulfillment_policy_id}, Payment: {payment_policy_id}, Return: {return_policy_id}")
        return {"success": False, "error": "Failed to retrieve eBay policies"}

    url = f"https://api.ebay.com/sell/inventory/v1/inventory_item/{sku}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json"
    }

    data = {
        "sku":                  sku,
        "product":              {
            "title":                title,
            "aspects":              formatted_aspects,
            "conditionDescriptors": [str(condition)],
            "categoryId":           "9355"  # Example: Cell Phones
        },
        "availability":         {"shipToLocationAvailability": {"quantity": 1}},
        "price":                {"value": price, "currency": "USD"},
        "marketplaceId":        "EBAY_US",
        "packageWeightAndSize": {
            "dimensions":  {
                "height": 5,
                "length": 10,
                "width":  15,
                "unit":   "INCH"
            },
            "packageType": "PACKAGE_THICK_ENVELOPE",
            "weight":      {"value": 2, "unit": "POUND"}
        },
        "listingPolicies":      {
            "paymentPolicyId":     payment_policy_id,
            "returnPolicyId":      return_policy_id,
            "fulfillmentPolicyId": fulfillment_policy_id
        }
    }

    response = requests.put(url, json=data, headers=headers)

    if response.status_code in [200, 201, 204]:
        print("✅ Inventory item posted successfully.")
        return {"success": True, "response": response.json()}

    print(f"❌ Error posting item: {response.text}")
    return {"success": False, "response": response.text}


def create_ebay_offer(sku, price):
    """Create an eBay offer for the given SKU and price."""
    access_token = get_ebay_access_token()
    if not access_token:
        return {"success": False, "error": "Authentication failed"}

    url = "https://api.ebay.com/sell/inventory/v1/offer"

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
    return response.json() if response.status_code in [200, 201] else {"success": False, "response": response.text}

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
    return response.json() if response.status_code in [200, 201] else {"success": False, "response": response.text}
