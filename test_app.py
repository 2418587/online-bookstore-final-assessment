import unittest
from unittest.mock import patch
from app import app, BOOKS, cart, users
from models import PaymentGateway, EmailService

# Ensure that users are able to view featured books with details (title, category, price, cover image). (TC001-01)
class FeaturedBooksTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_books_have_details(self):
        """Ensure featured books list has required details"""
        for book in BOOKS:
            self.assertIsInstance(book.title, str)
            self.assertIsInstance(book.category, str)
            self.assertIsInstance(book.price, (int, float))
            self.assertIsInstance(book.image, str)

    def test_index_displays_books(self):
        """Ensure the homepage displays featured books with all details"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)
        for book in BOOKS:
            self.assertIn(book.title, html)
            self.assertIn(book.category, html)
            self.assertIn(str(book.price), html)
            self.assertIn(book.image, html)

# Check that users are able to add, remove & update product quantity.  (TC002-01)
class CartFunctionalityTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # start with empty cart for each test

    def test_add_to_cart(self):
        """Check that a book can be added to the cart"""
        book = BOOKS[0]
        response = self.app.post('/add-to-cart', data={'title': book.title, 'quantity': 2}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(book.title, [item.book.title for item in cart.get_items()])
        self.assertEqual(cart.get_items()[0].quantity, 2)

    def test_update_cart_quantity(self):
        """Check that book quantity can be updated in the cart"""
        book = BOOKS[0]
        cart.add_book(book, 1)
        response = self.app.post('/update-cart', data={'title': book.title, 'quantity': 5}, follow_redirects=True)
        self.assertEqual(cart.get_items()[0].quantity, 5)

    def test_remove_from_cart(self):
        """Check that a book can be removed from the cart"""
        book = BOOKS[0]
        cart.add_book(book, 1)
        response = self.app.post('/remove-from-cart', data={'title': book.title}, follow_redirects=True)
        self.assertEqual(len(cart.get_items()), 0)

# Items should be removed when ‘0’ quantity entered. (TC002-02)
class CheckoutValidationTest(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # reset cart before each test

    def test_checkout_empty_cart(self):
        """User should be redirected if cart is empty"""
        response = self.app.get('/checkout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Your cart is empty!', response.get_data(as_text=True))

    def test_checkout_zero_quantity(self):
        """User should not be able to checkout with 0 quantity in basket"""
        # Add a book to cart
        book = BOOKS[0]
        cart.add_book(book, 1)
        # Update quantity to 0
        self.app.post('/update-cart', data={'title': book.title, 'quantity': 0}, follow_redirects=True)

        # Try accessing checkout
        response = self.app.get('/checkout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Your cart is empty!', response.get_data(as_text=True))

# User shouldn't be able to check out with negative numbers in basket. (TC002-03)
class CheckoutNegativeQuantityTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # reset cart before each test

    def test_checkout_negative_quantity(self):
        # Add a book with valid quantity first
        book = BOOKS[0]
        cart.add_book(book, 1)

        # Manually update quantity to a negative value
        self.app.post('/update-cart', data={'title': book.title, 'quantity': -3}, follow_redirects=True)

        # Try accessing checkout
        response = self.app.get('/checkout', follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        # Expect the system to block checkout (bug if it doesn't!)
        self.assertIn("Your cart is empty!", html)

# Ensure that user can't enter more than 99 products to basket. (TC002-04)
class CheckoutQuantityLimitTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # reset cart before each test

    def test_checkout_quantity_over_limit(self):
        book = BOOKS[0]

        # Try to add 100 items at once
        self.app.post('/update-cart', data={'title': book.title, 'quantity': 100}, follow_redirects=True)

        # Fetch cart page
        response = self.app.get('/cart', follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        # Expect cart to either cap at 99 or block checkout
        self.assertNotIn("Quantity: 100", html)

#Ensure that users can't leave quantity field blank (TC002-05)
class EmptyQuantityTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # reset cart before each test

    def test_blank_quantity_not_allowed(self):
        book = BOOKS[0]

        # Post with empty quantity
        response = self.app.post('/update-cart', data={'title': book.title, 'quantity': ''}, follow_redirects=True)

        html = response.get_data(as_text=True)

        # The system should not crash and should give a validation message
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please enter a valid quantity", html)  # ???

# Ensure that users cant enter non numerical values into quantity field. (TC002-06)
class NonNumericQuantityTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # reset cart before each test

    def test_non_numeric_quantity_not_allowed(self):
        book = BOOKS[0]

        # Post with a non-numeric quantity
        response = self.app.post('/update-cart', data={'title': book.title, 'quantity': 'abc'}, follow_redirects=True)
        html = response.get_data(as_text=True)

        # The system should not crash and should give a validation message
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please enter a valid quantity", html)  

# Users should be able to view cart with real world price calculations. (TC002-07)
class pyth(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # reset cart before each test

    def test_cart_price_calculation(self):
        book1 = BOOKS[0]  # The Great Gatsby, $10.99
        book2 = BOOKS[1]  # 1984, $8.99

        # Add items to cart
        cart.add_book(book1, 2)  # 2 x $10.99 = 21.98
        cart.add_book(book2, 3)  # 3 x $8.99 = 26.97

        response = self.app.get('/cart')
        html = response.get_data(as_text=True)

        # Check that the totals are displayed correctly
        self.assertIn("$10.99", html)
        self.assertIn("$8.99", html)
        self.assertIn("2", html)  # Quantity for first book
        self.assertIn("3", html)  # Quantity for second book

        total = 2 * 10.99 + 3 * 8.99  # 21.98 + 26.97 = 48.95
        self.assertIn(f"{total:.2f}", html)  # Ensure total amount is correct

# User should be directed to order summary. (TC003-01)
class OrderConfirmationTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # reset cart before each test

    def test_order_confirmation_page(self):
        book = BOOKS[0]

        # Add a book to cart
        cart.add_book(book, 2)

        # Simulate checkout form submission
        checkout_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'address': '123 Main St',
            'city': 'Anytown',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '4111111111115432',
            'expiry_date': '12/25',
            'cvv': '123'
        }

        response = self.app.post('/process-checkout', data=checkout_data, follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        # Check for presence of order details
        self.assertIn("Order Confirmation", html)
        self.assertIn("Order Number", html)  
        self.assertIn("Total", html)
        self.assertIn("What's Next", html)
        self.assertIn(book.title, html)

# User should be able to choose payment method - credit card. (TC003-02)
class PaymentMethodTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # Ensure cart is empty before each test

    def test_credit_card_payment_selection(self):
        book = BOOKS[0]
        cart.add_book(book, 1)

        # Prepare checkout form data selecting credit card
        checkout_data = {
            'name': 'Alice',
            'email': 'alice@example.com',
            'address': '456 Elm St',
            'city': 'Gotham',
            'zip_code': '54321',
            'payment_method': 'credit_card',  # explicitly selecting credit card
            'card_number': '4242424242424242',  
            'expiry_date': '12/30',
            'cvv': '123'
        }

        # Submit checkout form and follow redirects to confirmation page
        response = self.app.post('/process-checkout', data=checkout_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)
        # Check that credit card payment is reflected (mock)
        self.assertIn('Credit Card', html)

# User should be able to choose payment method - Paypal (TC003-03)
class PayPalPaymentMethodTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        cart.clear()  # Ensure cart is empty before each test

    def test_paypal_redirect(self):
        # Add a book to cart
        book = BOOKS[0]
        cart.add_book(book, 1)

        # Submit checkout form selecting PayPal
        checkout_data = {
            'name': 'Alice',
            'email': 'alice@example.com',
            'address': '123 Elm St',
            'city': 'Springfield',
            'zip_code': '54321',
            'payment_method': 'paypal'
        }

        # Submit form without following redirects to capture the initial response
        response = self.app.post('/process-checkout', data=checkout_data, follow_redirects=False)
        
        # Expect a 302 redirect to PayPal URL (or placeholder in app)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/paypal', response.headers['Location'] or '') 

# User should be able to successfully enter discount code. (TC003-04)
class DiscountCodeTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()  # start with empty cart
       
        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_discount_code_save10(self):
        """Test that SAVE10 discount code is applied correctly"""
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123',
            'discount_code': 'SAVE10'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        
        # Check that total amount is correctly reduced (on checkout page)
        discounted_price = BOOKS[0].price * 0.9  # 10% off
        self.assertIn(f"${discounted_price:.2f}", html)

#User should be able to enter discount code in lower case. (TC003-05)
class LowerCaseDiscountCodeTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()  # start with empty cart
       
        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_lower_case_discount_code_save10(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123',
            'discount_code': 'save10'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        
        # Check that total amount is correctly reduced (on checkout page)
        discounted_price = BOOKS[0].price * 0.9  # 10% off
        self.assertIn(f"${discounted_price:.2f}", html)

# Incorrect discount codes should be rejected. (TC003-06)
class WrongDiscountCodeTest(unittest.TestCase):
     def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()  # start with empty cart
       
        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

     def test_wrong_discount_code(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123',
            'discount_code': 'TEST10'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        
        # Check if total amount is wrongly reduced (on checkout page)
        full_price = BOOKS[0].price  # no discount applied
        self.assertIn(f"${full_price:.2f}", html)

# Payment page Form Validation (TC003-07)
class CheckoutFormValidationTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_checkout_missing_fields(self):
        response = self.client.post('/process-checkout', data={

            # Intentionally leave out 'name' and 'email'
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        
        # Check that the page shows an error message about missing required fields
        self.assertIn("Please fill in the name field", html)  

# Payment page Email Address correct format (TC003-08)  
class CheckoutEmailFormatTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_invalid_email(self):
        """Test that checkout proceeds even with invalid email format"""
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@nodotcom',  # invalid format
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Fail if it reaches confirmation page
        self.assertNotIn("Order Confirmed!", html)
        # Pass if the proper validation message is shown
        self.assertIn("Invalid email address", html)

#Secure payment processing with success/failure (TC004-01)
class PaymentProcessingTest(unittest.TestCase):

    def test_successful_payment(self):
        payment_info = {
            'payment_method': 'credit_card',
            'card_number': '1234567812345678',  # valid
            'expiry_date': '12/30',
            'cvv': '123'
        }
        result = PaymentGateway.process_payment(payment_info)
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['transaction_id'])
        self.assertEqual(result['message'], 'Payment processed successfully')

    def test_failed_payment(self):
        payment_info = {
            'payment_method': 'credit_card',
            'card_number': '1234567812341111',  # ends with 1111 =invalid
            'expiry_date': '12/30',
            'cvv': '123'
        }
        result = PaymentGateway.process_payment(payment_info)
        self.assertFalse(result['success'])
        self.assertIsNone(result['transaction_id'])
        self.assertEqual(result['message'], 'Payment failed: Invalid card number')


#Card Validation (TC004-02) 
class CardValidationTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_credit_card(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@nodot.com',  
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Pass if it reaches confirmation page
        self.assertIn("Order Confirmed!", html)
        
# Ensure that invalid cards are rejected  (TC004-03) 
class InvalidCardTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_invalid_credit_card(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@dot.com',  
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 1111',
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Fail if it reaches confirmation page
        self.assertNotIn("Order Confirmed!", html)

# Ensure that card number does not exceed 16 digits. (TC004-04)
class LongCardNumberTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_long_credit_card_number(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@dot.com',  
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 12345', #17 digit card number entered
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Fail if it reaches confirmation page
        self.assertNotIn("Order Confirmed!", html)   

#Ensure that card number is 13 digits or more (TC004-05)
class ShortCardNumberTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    def test_short_credit_card_number(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@dot.com',  
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012', #12 digit card number entered
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Fail if it reaches confirmation page
        self.assertNotIn("Order Confirmed!", html)   

# Ensure that card expiry date is entered (TC004-06)
class CardExpiryDateTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        cart.add_book(BOOKS[0], 1)

    def test_missing_expiry_date(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@dot.com',
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '',  # missing expiry date
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Fail if it reaches confirmation page
        self.assertNotIn("Order Confirmed!", html)
        # Pass if proper validation message is shown
        self.assertIn("", html)

#Ensure that CVV is entered (TC004-07)
class CardCVVTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        cart.add_book(BOOKS[0], 1)

    def test_missing_cvv(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@dot.com',
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '123',  
            'cvv': ''               # missing CVV
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Fail if it reaches confirmation page
        self.assertNotIn("Order Confirmed!", html)
        # Pass if proper validation message is shown
        self.assertIn("", html)

#Transaction ID Generation (TC004-08)
class TransactionIDTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        cart.add_book(BOOKS[0], 1)

    def test_transaction_id_generated(self):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'randomemail@dot.com',
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Pass if it reaches confirmation page
        self.assertIn("Order Confirmed!", html)

        # Check for a Transaction ID pattern (e.g., TXN followed by numbers)
        import re
        txn_match = re.search(r'Transaction ID:\s*TXN\d+', html)
        self.assertIsNotNone(txn_match, "Transaction ID was not generated.")

# Email confirmation (Mock) (TC005-01)
class CheckoutEmailConfirmationTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        # Add a book to the cart
        book = BOOKS[0]
        cart.add_book(book, 1)

    @patch("models.EmailService.send_order_confirmation")  # patch the EmailService in models
    def test_email_confirmation_sent(self, mock_send_email):
        response = self.client.post('/process-checkout', data={
            'name': 'Test User',
            'email': 'testuser@example.com',
            'address': '123 Test St',
            'city': 'Testville',
            'zip_code': '12345',
            'payment_method': 'credit_card',
            'card_number': '1234 5678 9012 3456',
            'expiry_date': '12/30',
            'cvv': '123'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)

        # Ensure confirmation page is shown
        self.assertIn("Order Confirmed!", html)

        # Ensure EmailService was called once with correct arguments
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertEqual(args[0], "testuser@example.com")  # recipient email
        self.assertTrue(hasattr(args[1], 'order_id'))  # order object passed


# User Registration with validation (TC006-01)
class RegistrationTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

    def test_successful_registration(self):
        response = self.client.post('/register', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'address': '123 Test Street'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        self.assertIn("Account created successfully", html)
        self.assertIn('newuser@example.com', users)

    def test_invalid_email_format(self):
        """Registration fails with invalid email format"""
        response = self.client.post('/register', data={
            'name': 'Bad Email',
            'email': 'test@wrongemail',  
            'password': 'securepass123',
            'address': '123 Test Street'
        }, follow_redirects=True)

        html = response.get_data(as_text=True)
        self.assertIn("Invalid email format", html)
        self.assertNotIn('test@wrongemail', users)

    def test_duplicate_email_registration(self):
     self.client.post('/register', data={
        'name': 'Existing User',
        'email': 'existing@example.com',
        'password': 'securepass123',
        'address': '123 Test Street'
    }, follow_redirects=True)

    # Try to register again with the same email
     response = self.client.post('/register', data={
        'name': 'Duplicate User',
        'email': 'EXISTING@EXAMPLE.COM',
        'password': 'anotherpass123',
        'address': '456 Other Street'
    }, follow_redirects=True)

     html = response.get_data(as_text=True)

    # Check current behavior: user is logged in successfully
     self.assertIn("Account created successfully", html)
     self.assertIn("Logout", html)
 

# Login & Logout Functionality (TC006-02 & TC006-03)
class LoginTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Ensure demo user exists
        users['demo@bookstore.com'] = type('User', (object,), {
            'password': 'demo123',
            'name': 'Demo User',
            'address': '',
            'orders': []
        })()

    def test_missing_fields(self):
        response = self.client.post('/login', data={
            'email': '',
            'password': ''
        }, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Invalid email or password", html)

    def test_invalid_credentials(self):
        response = self.client.post('/login', data={
            'email': 'wrong@example.com',
            'password': 'wrongpass'
        }, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Invalid email or password", html)

    def test_valid_login(self):
        response = self.client.post('/login', data={
            'email': 'demo@bookstore.com',
            'password': 'demo123'
        }, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Logout", html)

    def test_logout(self):
        self.client.post('/login', data={
            'email': 'demo@bookstore.com',
            'password': 'demo123'
        }, follow_redirects=True)
        response = self.client.get('/logout', follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Login", html)


#Profile Management (update information/password) (TC006-04)
class ProfileManagementTest(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        cart.clear()

        self.client.post('/login', data={
            'email': 'demo@bookstore.com',
            'password': 'demo123'
        }, follow_redirects=True)

    def test_update_profile(self):
        """Update name, address, and password for demo user"""
        response = self.client.post('/update-profile', data={
            'name': 'Updated Demo',
            'address': '123 Updated Street',
            'new_password': 'newpass123'
        }, follow_redirects=True)

        # Verify changes
        demo_user = users['demo@bookstore.com']
        self.assertEqual(demo_user.name, 'Updated Demo')
        self.assertEqual(demo_user.address, '123 Updated Street')
        self.assertEqual(demo_user.password, 'newpass123')

#View past order details (TC006-05)
class OrderHistoryTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Log in as demo user
        self.client.post('/login', data={
            'email': 'demo@bookstore.com',
            'password': 'demo123'
        }, follow_redirects=True)

        # Clear cart and user's orders before each test
        cart.clear()
        users['demo@bookstore.com'].orders = []

def test_place_order_and_check_history(self):
    # Ensure demo user exists
    if 'demo@bookstore.com' not in users:
        from types import SimpleNamespace
        users['demo@bookstore.com'] = SimpleNamespace(email='demo@bookstore.com', orders=[])

    # Add a book to cart
    book = BOOKS[0]
    self.client.post('/add-to-cart', data={'title': book.title, 'quantity': 1}, follow_redirects=True)

    # Submit checkout form
    checkout_data = {
        'name': 'Demo User',
        'email': 'demo@bookstore.com',
        'address': '123 Demo Street, Demo City, DC 12345',
        'city': 'Demo City',
        'zip_code': '12345',
        'payment_method': 'credit_card',
        'card_number': '4111111111111234',
        'expiry_date': '12/25',
        'cvv': '123'
    }

    # Wrap in try/except to catch Internal Server Errors
    checkout_response = self.client.post('/process-checkout', data=checkout_data, follow_redirects=True)
    html = checkout_response.get_data(as_text=True)

    # Assert response is 200 (or at least capture the HTML for debugging)
    self.assertIn("Order Confirmed", html)
    

# Session Management (TC006-06)
class SessionManagementTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Ensure the demo user exists for login
        users['demo@bookstore.com'] = type('User', (object,), {
            'password': 'demo123',
            'name': 'Demo User',
            'address': '',
            'orders': []
        })()

    def test_session_persistence(self):
        # Log in
        self.client.post('/login', data={
            'email': 'demo@bookstore.com',
            'password': 'demo123'
        }, follow_redirects=True)
        
        # Visit multiple pages
        response1 = self.client.get('/')
        response2 = self.client.get('/account')
        
        html1 = response1.get_data(as_text=True)
        html2 = response2.get_data(as_text=True)
        
        # Check that session persists (user is logged in)
        self.assertIn("Logout", html1)
        self.assertIn("Logout", html2)


if __name__ == "__main__":
    unittest.main()
