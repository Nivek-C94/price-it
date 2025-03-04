import json
import requests
from fastapi import Request
from config.oauth2_manager import validate_state, fetch_tokens

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