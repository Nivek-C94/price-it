import os
import requests
import base64
import logging
import json
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("EBAY_REDIRECT_URI")
EBAY_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SCOPES = "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"

TOKEN_STORAGE = "config/ebay_tokens.json"

def load_tokens():
    try:
        with open(TOKEN_STORAGE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_tokens(tokens):
    with open(TOKEN_STORAGE, "w") as file:
        json.dump(tokens, file)

# Step 1: Generate Authorization URL
def get_auth_url():
    ebay = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    auth_url, state = ebay.authorization_url(EBAY_AUTH_URL)
    return auth_url

# Step 2: Exchange Authorization Code for Tokens
def fetch_tokens(auth_code):
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens)
        return tokens
    raise Exception(f"Failed to get tokens: {response.text}")

# Step 3: Refresh Token
def refresh_access_token(refresh_token):
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        if "access_token" in token_data:
            logging.info("Access token refreshed successfully.")
            tokens = load_tokens()
            tokens["access_token"] = token_data["access_token"]
            tokens["refresh_token"] = token_data.get("refresh_token", refresh_token)
            save_tokens(tokens)
            return token_data["access_token"]
        else:
            logging.error("No access token returned: %s", token_data)
            raise Exception("Invalid token response.")
    except requests.exceptions.RequestException as e:
        logging.error("Token refresh failed: %s", str(e))
        raise Exception("Failed to refresh token.")