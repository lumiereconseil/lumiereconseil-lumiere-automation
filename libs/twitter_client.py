import os
import requests
from requests_oauthlib import OAuth1


class TwitterClient:
    def __init__(self):
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_secret = os.getenv("X_ACCESS_SECRET")
        missing = [name for name, value in {
            "X_API_KEY": self.api_key,
            "X_API_SECRET": self.api_secret,
            "X_ACCESS_TOKEN": self.access_token,
            "X_ACCESS_SECRET": self.access_secret,
        }.items() if not value]
        if missing:
            raise RuntimeError("Missing X credentials: " + ", ".join(missing))

    def post_tweet(self, text: str):
        if not text or not text.strip():
            raise ValueError("Tweet text must not be empty")
        url = "https://api.x.com/2/tweets"
        auth = OAuth1(self.api_key, self.api_secret, self.access_token, self.access_secret)
        response = requests.post(url, json={"text": text.strip()}, auth=auth, timeout=30)
        response.raise_for_status()
        return response.json()
