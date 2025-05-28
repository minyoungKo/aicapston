import os
import json
import requests
from datetime import datetime
from utils.config_loader import APP_KEY, APP_SECRET, URL_BASE

TOKEN_FILE = "token_cache.json"

def load_token_from_file():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data["access_token"], data["expired_at"]
    return None, None

def save_token_to_file(token, expired_at):
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "access_token": token,
            "expired_at": expired_at
        }, f)

def get_access_token():
    token, expired_str = load_token_from_file()
    if token and expired_str:
        now = datetime.now()
        expired_at = datetime.strptime(expired_str, "%Y-%m-%d %H:%M:%S")
        if now < expired_at:
            return token

    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    URL = f"{URL_BASE}/oauth2/tokenP"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    data = res.json()
    new_token = data["access_token"]
    expired_at = data["access_token_token_expired"]
    save_token_to_file(new_token, expired_at)
    return new_token