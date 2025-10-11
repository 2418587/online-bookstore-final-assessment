import subprocess, unittest
import sys
from models import User

# Secure Password Storage(TC009-01)
class TestSecurePasswordStorage(unittest.TestCase):
    def test_password_is_not_plain_text(self):
        password = "mypassword123"
        user = User(email="test@example.com", password=password)

        self.assertNotEqual(
            user.password,
            password,
        )

# Static Code Security Analysis (TC009-02)
def static_code_security_analysis():

    try:
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", ".", "-ll"],
            capture_output=True,
            text=True
        )
        print(result.stdout)

        if "No issues identified." in result.stdout:
            print("No security issues detected by Bandit.")
        else:
            print("Security issues found by Bandit. Review the warnings above.")

    except FileNotFoundError:
        print("Error: Bandit is not installed. Please install it with 'pip install bandit'.")

if __name__ == "__main__":
    static_code_security_analysis()
