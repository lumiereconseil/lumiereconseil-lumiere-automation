import os
import requests

class StripeClient:
    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")

    def create_customer(self, email: str):
        url = "https://api.stripe.com/v1/customers"
        headers = {
            "Authorization": f"Bearer {self.secret_key}"
        }
        data = {
            "email": email
        }
        response = requests.post(url, headers=headers, data=data)
        return response.json()

    def create_subscription(self, customer_id: str, price_id: str):
        url = "https://api.stripe.com/v1/subscriptions"
        headers = {
            "Authorization": f"Bearer {self.secret_key}"
        }
        data = {
            "customer": customer_id,
            "items[0][price]": price_id
        }
        response = requests.post(url, headers=headers, data=data)
        return response.json()

