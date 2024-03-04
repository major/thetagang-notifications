"""Handle authentication for API requests."""

import os

import requests

THETAGANG_USERNAME = os.getenv("THETAGANG_USERNAME", None)
THETAGANG_PASSWORD = os.getenv("THETAGANG_PASSWORD", None)


def get_auth_token():
    """Get the authentication token."""
    url = "https://api3.thetagang.com/auth/login"
    data = {"username": THETAGANG_USERNAME, "password": THETAGANG_PASSWORD}
    resp = requests.post(url, json=data, timeout=30)

    return resp.json()["token"]
