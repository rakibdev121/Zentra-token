"""
Validates Telegram WebApp `initData`.

Telegram signs the data it hands to your Mini App with your bot token.
Any request that claims to be "user 12345" MUST be checked here first —
otherwise anyone can call the API pretending to be any Telegram user and
mine coins or steal referral bonuses under someone else's account.

Docs: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# How long a signed initData payload stays valid for, in seconds.
MAX_AUTH_AGE_SECONDS = 24 * 60 * 60


def _check_signature(init_data: str) -> dict:
    if not BOT_TOKEN:
        raise HTTPException(500, "Server misconfigured: BOT_TOKEN is not set")

    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Missing hash in initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(401, "Invalid initData signature")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > MAX_AUTH_AGE_SECONDS:
        raise HTTPException(401, "initData has expired, reopen the app")

    return parsed


def get_telegram_user(x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data")) -> dict:
    """FastAPI dependency: verifies the request and returns the Telegram user dict."""
    parsed = _check_signature(x_telegram_init_data)
    user_json = parsed.get("user")
    if not user_json:
        raise HTTPException(401, "No user in initData")
    user = json.loads(user_json)
    user["_start_param"] = parsed.get("start_param")
    return user
