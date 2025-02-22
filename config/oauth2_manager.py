import os
import requests
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("EBAY_REDIRECT_URI")
EBAY_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SCOPES = "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory"

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
    auth_header = f"Basic {requests.utils.quote(CLIENT_ID)}:{requests.utils.quote(CLIENT_SECRET)}"
    headers = {"Authorization": auth_header, "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Failed to get tokens: {response.text}")

# Step 3: Refresh Token
def refresh_access_token(refresh_token):
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    auth_header = f"Basic {requests.utils.quote(CLIENT_ID)}:{requests.utils.quote(CLIENT_SECRET)}"
    headers = {"Authorization": auth_header, "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Failed to refresh token: {response.text}")