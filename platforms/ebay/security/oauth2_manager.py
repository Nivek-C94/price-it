from fastapi import Request

import base64
import cryptography.fernet
import hashlib
import json
import logging
import os
import requests
import time
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('EBAY_CLIENT_ID')
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
REDIRECT_URI = "https://snap-n-sell.duckdns.org/auth/accepted"
EBAY_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SCOPES = " ".join([
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
    "https://api.ebay.com/oauth/api_scope/sell.account",
    "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    "https://api.ebay.com/oauth/api_scope/sell.marketing",
    "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
    "https://api.ebay.com/oauth/api_scope/sell.reputation",
    "https://api.ebay.com/oauth/api_scope/sell.stores"
])



TOKEN_STORAGE = os.getenv("TOKEN_STORAGE_PATH", "resources/ebay_tokens.json")
STATE_STORAGE = os.getenv("STATE_STORAGE_PATH", "resources/oauth_state.json")

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
# Ensure the resources directory exists
if not os.path.exists("resources"):
    os.makedirs("resources")

if not ENCRYPTION_KEY:
    if os.path.exists("resources/encryption_key.txt"):
        with open("resources/encryption_key.txt", "r") as key_file:
            ENCRYPTION_KEY = key_file.read().strip()
    else:
        ENCRYPTION_KEY = Fernet.generate_key().decode()
        with open("resources/encryption_key.txt", "w") as key_file:
            key_file.write(ENCRYPTION_KEY)

cipher = Fernet(ENCRYPTION_KEY.encode())

async def auth_accepted(request: Request):
    """Handle eBay OAuth2 authorization callback."""
    params = request.query_params

    if "code" not in params or "state" not in params:
        return {"success": False, "error": "Missing code or state parameter."}

    auth_code = params["code"]
    state = params["state"]

    if not validate_state(state):
        return {"success": False, "error": "Invalid state parameter. Possible CSRF attack."}

    return fetch_tokens(auth_code, state)

def load_tokens():
    """Load encrypted tokens from storage."""
    try:
        with open(TOKEN_STORAGE, "rb") as file:
            encrypted_data = file.read()
            decrypted_data = cipher.decrypt(encrypted_data).decode()
            return json.loads(decrypted_data)
    except (FileNotFoundError, cryptography.fernet.InvalidToken):
        return {}

def save_tokens(tokens):
    """Save encrypted tokens securely."""
    encrypted_data = cipher.encrypt(json.dumps(tokens).encode())
    with open(TOKEN_STORAGE, "wb") as file:
        file.write(encrypted_data)



def get_ebay_access_token():
    """Retrieve a valid access token or force a refresh if invalid."""
    tokens = load_tokens()
    print(f"🔍 DEBUG: Loaded Tokens: {tokens}")

    if "access_token" in tokens:
        print("✅ Using stored access token")
        return refresh_access_token(tokens["refresh_token"])  # Always refresh the token

    if "refresh_token" in tokens:
        print("♻️ Refreshing access token")
        return refresh_access_token(tokens["refresh_token"])

    print("🚨 No valid token found. Authentication required.")
    return {"status": "unauthenticated", "message": "User needs to authenticate.", "oauth_url": get_auth_url()}





# CSRF Protection: Generate and Validate State


def generate_state():
    state = base64.urlsafe_b64encode(os.urandom(32)).decode()
    with open(STATE_STORAGE, "w") as file:
        file.write(state)  # Save state immediately
    return state


def validate_state(received_state):
    try:
        with open(STATE_STORAGE, "r") as file:
            expected_state = file.read().strip()
            return received_state == expected_state
    except FileNotFoundError:
        return False
    return received_state == expected_state


def get_auth_url():
    state = generate_state()  # Generate state before using it
    with open(STATE_STORAGE, "w") as file:
        file.write(state)
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip("=")
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    ebay = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        state=state,
    )
    auth_url, _ = ebay.authorization_url(EBAY_AUTH_URL)
    return auth_url


def fetch_tokens(auth_code, state):
    if not validate_state(state):
        raise Exception("Invalid state parameter. Possible CSRF attack.")

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    for attempt in range(3):
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        if response.status_code == 200:
            tokens = response.json()
            save_tokens(tokens)
            return tokens
        elif response.status_code in {500, 502, 503, 504}:
            logging.warning(
                f"Temporary error from server, retrying in {2**attempt} seconds..."
            )
            time.sleep(2**attempt)
        else:
            break
    raise Exception(f"Failed to get tokens after retries: {response.text}")


def refresh_access_token(refresh_token):
    """Refresh the access token using eBay's OAuth2 API."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": SCOPES,
    }
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()

        if "access_token" in token_data:
            logging.info("✅ Access token refreshed successfully.")
            tokens = load_tokens()
            tokens["access_token"] = token_data["access_token"]
            tokens["refresh_token"] = token_data.get("refresh_token", refresh_token)
            save_tokens(tokens)
            return token_data["access_token"]
        else:
            logging.error("⚠️ No access token returned: %s", token_data)
            raise Exception("Invalid token response.")
    except requests.exceptions.RequestException as e:
        logging.error("🚨 Token refresh failed: %s", str(e))
        raise Exception("Failed to refresh token.")


print(get_auth_url())