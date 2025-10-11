import cProfile
import timeit
import datetime
from app import BOOKS
from models import Cart, User, Order, Book

# Measure cart price total calculation time with large quantities. (TC008-01)
def profile_cart_total():
    # Create a new cart
    cart = Cart()
    
    # Add large quantities of existing books
    for book in BOOKS:
        cart.add_book(book, quantity=10000)  # 10,000 copies each
    
    print(f"Cart has {cart.get_total_items()} items in total")
    
    # Measure total price calculation time
    total = cart.get_total_price()
    print(f"Total cart price: ${total:.2f}")   

#Performance of user order history retrieval on ‘My Account’ page (TC008-02)   

BOOKS = [
    Book("The Great Gatsby", "Fiction", 10.99, ""),
    Book("1984", "Dystopia", 8.99, ""),
    Book("I Ching", "Traditional", 18.99, ""),
    Book("Moby Dick", "Adventure", 12.49, "")
]

# Create a demo user
demo_user = User("demo@bookstore.com", "demo123", "Demo User", "123 Demo Street")

# Populate the user with 1000 orders
for i in range(1000):
    order = Order(
        order_id=f"ORDER{i}",
        user_email=demo_user.email,
        items=[Book(b.title, b.category, b.price, b.image) for b in BOOKS],
        shipping_info={"address": demo_user.address},
        payment_info={"method": "credit_card", "transaction_id": f"TXN{i}"},
        total_amount=sum(b.price for b in BOOKS)
    )
    demo_user.add_order(order)

# Benchmark order history retrieval
execution_time = timeit.timeit(
    stmt='demo_user.get_order_history()', #Inefficient code
    globals={'demo_user': demo_user},
    number=1000
)

print(f"Average order history retrieval time over 1000 runs: {execution_time / 1000:.6f} seconds")

# User object initialisation time. (TC008-03)
class UserInefficient:
    def __init__(self, email, password, name="", address=""):
        self.email = email
        self.password = password
        self.name = name
        self.address = address
        self.orders = []
        self.temp_data = []  # Never used
        self.cache = {}      # Never used

class UserEfficient:
    def __init__(self, email, password, name="", address=""):
        self.email = email
        self.password = password
        self.name = name
        self.address = address
        self.orders = []

def create_inefficient_user():
    UserInefficient("demo@bookstore.com", "demo123", "Demo User", "123 Demo Street")

def create_efficient_user():
    UserEfficient("demo@bookstore.com", "demo123", "Demo User", "123 Demo Street")

inefficient_time = timeit.timeit(create_inefficient_user, number=1_000_000)
efficient_time = timeit.timeit(create_efficient_user, number=1_000_000)

print(f"Inefficient User init: {inefficient_time:.4f} seconds")
print(f"Efficient User init:   {efficient_time:.4f} seconds")

# Order Management Performance (TC008-04)
def test_order_management():
   
    user = User("demo@bookstore.com", "demo123")
    
    # Add 1000 orders
    for i in range(1000):
        order = Order(
            order_id=str(i),
            user_email=user.email,
            items=[],
            shipping_info={},
            payment_info={},
            total_amount=0
        )
        # Artificially vary the order date
        order.order_date = datetime.datetime.now() - datetime.timedelta(days=i)
        user.add_order(order)
    
    # Access order history multiple times
    for _ in range(1000):
        history = user.get_order_history()

if __name__ == "__main__":
    print("Detecting inefficiencies in User order management...\n")
    cProfile.run("profile_cart_total()")
    cProfile.run('test_order_management()')
