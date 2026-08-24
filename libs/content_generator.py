import os
import requests

class ContentGenerator:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.api_url = "https://api.anthropic.com/v1/messages"

    def generate_post(self, topic: str):
        headers = {
            "x-api-key": self.api_key,
            "content-type": "application/json"
        }

        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate a short social media post about: {topic}"
                }
            ]
        }

        response = requests.post(self.api_url, json=payload, headers=headers)
        return response.json()

