import unittest
import cProfile
import pstats
import timeit
import datetime
from app import BOOKS
from models import Cart, User, Order, Book

class TestPerformance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Prepare demo user and books for tests
        cls.books = [
            Book("The Great Gatsby", "Fiction", 10.99, ""),
            Book("1984", "Dystopia", 8.99, ""),
            Book("I Ching", "Traditional", 18.99, ""),
            Book("Moby Dick", "Adventure", 12.49, "")
        ]
        cls.demo_user = User("demo@bookstore.com", "demo123", "Demo User", "123 Demo Street")
        for i in range(1000):
            order = Order(
                order_id=f"ORDER{i}",
                user_email=cls.demo_user.email,
                items=[Book(b.title, b.category, b.price, b.image) for b in cls.books],
                shipping_info={"address": cls.demo_user.address},
                payment_info={"method": "credit_card", "transaction_id": f"TXN{i}"},
                total_amount=sum(b.price for b in cls.books)
            )
            cls.demo_user.add_order(order)

    def test_cart_total_profile(self):
        """Measure total price calculation time with large quantities (TC008-01)"""
        cart = Cart()
        for book in self.books:
            cart.add_book(book, quantity=10000)
        print(f"Cart has {cart.get_total_items()} items in total")
        total = cart.get_total_price()
        print(f"Total cart price: ${total:.2f}")

    def test_order_history_performance(self):
        """Benchmark order history retrieval (TC008-02)"""
        execution_time = timeit.timeit(
            stmt='self.demo_user.get_order_history()',
            globals={'self': self},
            number=1000
        )
        avg_time = execution_time / 1000
        print(f"Average order history retrieval time over 1000 runs: {avg_time:.6f} seconds")
        self.assertLess(avg_time, 0.01, "Order history retrieval too slow!")

    def test_user_init_efficiency(self):
        """Compare inefficient vs efficient User initialization (TC008-03)"""
        class UserInefficient:
            def __init__(self, email, password, name="", address=""):
                self.email = email
                self.password = password
                self.name = name
                self.address = address
                self.orders = []
                self.temp_data = []
                self.cache = {}

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

        inefficient_time = timeit.timeit(create_inefficient_user, number=100_000)
        efficient_time = timeit.timeit(create_efficient_user, number=100_000)
        print(f"Inefficient User init: {inefficient_time:.4f} seconds")
        print(f"Efficient User init:   {efficient_time:.4f} seconds")
        self.assertLess(efficient_time, inefficient_time, "Efficient User should initialize faster")

    def test_order_management_profile(self):
        """Profile order history retrieval with 1000 orders (TC008-04)"""
        user = User("demo@bookstore.com", "demo123")
        for i in range(1000):
            order = Order(
                order_id=str(i),
                user_email=user.email,
                items=[],
                shipping_info={},
                payment_info={},
                total_amount=0
            )
            order.order_date = datetime.datetime.now() - datetime.timedelta(days=i)
            user.add_order(order)

        profiler = cProfile.Profile()
        profiler.enable()
        user.get_order_history()
        profiler.disable()

        stats = pstats.Stats(profiler).sort_stats('cumtime')
        print("Top 10 functions by cumulative time in order management:")
        stats.print_stats(10)

if __name__ == "__main__":
    unittest.main()
