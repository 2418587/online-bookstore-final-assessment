from locust import HttpUser, task, between
import random
from app import BOOKS  

# Test application response time under load (TC008-05)
class BookstoreUser(HttpUser):
    host = "http://127.0.0.1:5000"  # make sure Flask is running here
    wait_time = between(1, 3)

    @task
    def browse_and_checkout(self):
        # Browse books
        self.client.get("/")

        # Pick a random book
        book = random.choice(BOOKS)
        self.client.post("/add-to-cart", data={"title": book.title, "quantity": 1})

        # Proceed to checkout with mock payment
        checkout_data = {
            "name": "Demo User",
            "email": "demo@bookstore.com",
            "address": "123 Demo Street",
            "city": "Demo City",
            "zip_code": "12345",
            "payment_method": "credit_card",
            "card_number": "4111111111111234",
            "expiry_date": "12/25",
            "cvv": "123"
        }
        self.client.post("/process-checkout", data=checkout_data)

