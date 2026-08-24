import requests
import os

class InstagramClient:
    def __init__(self):
        self.access_token = os.getenv("IG_ACCESS_TOKEN")
        self.business_account_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")

    def post_photo(self, image_url: str, caption: str):
        # Step 1: Create media object
        create_url = (
            f"https://graph.facebook.com/v18.0/{self.business_account_id}/media"
        )
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token
        }
        create_res = requests.post(create_url, data=payload).json()

        # Step 2: Publish media object
        publish_url = (
            f"https://graph.facebook.com/v18.0/{self.business_account_id}/media_publish"
        )
        publish_payload = {
            "creation_id": create_res.get("id"),
            "access_token": self.access_token
        }
        publish_res = requests.post(publish_url, data=publish_payload).json()

        return publish_res

