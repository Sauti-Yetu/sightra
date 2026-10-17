from django.test import SimpleTestCase

from apps.accounts.auth_messages import auth_error_message


class AuthMessageTests(SimpleTestCase):
    def test_rate_limit_message(self):
        msg = auth_error_message({"_status": 429, "msg": "email rate limit exceeded"})
        self.assertIn("Too many", msg)

    def test_invalid_login_message(self):
        msg = auth_error_message({"error_description": "Invalid login credentials"})
        self.assertIn("Incorrect email or password", msg)
