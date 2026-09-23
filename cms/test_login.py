"""CMS login must require both username and password.

Run with:  python test_login.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module  # noqa: E402
from app import app  # noqa: E402


class LoginTests(unittest.TestCase):
    def setUp(self):
        self._user = app_module.CMS_USERNAME
        self._password = app_module.CMS_PASSWORD
        app_module.CMS_USERNAME = "editor"
        app_module.CMS_PASSWORD = "s3cret"
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        self.client = app.test_client()

    def tearDown(self):
        app_module.CMS_USERNAME = self._user
        app_module.CMS_PASSWORD = self._password

    def test_login_form_has_username_and_password(self):
        html = self.client.get("/login").get_data(as_text=True)
        self.assertIn('name="username"', html)
        self.assertIn('name="password"', html)
        self.assertIn('type="password"', html)

    def test_pages_redirect_to_login_when_credentials_are_set(self):
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

    def test_wrong_username_is_rejected(self):
        response = self.client.post("/login", data={
            "username": "not-the-user",
            "password": "s3cret",
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Incorrect username or password", response.get_data(as_text=True))
        guarded = self.client.get("/", follow_redirects=False)
        self.assertEqual(guarded.status_code, 302)

    def test_wrong_password_is_rejected(self):
        response = self.client.post("/login", data={
            "username": "editor",
            "password": "wrong",
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Incorrect username or password", response.get_data(as_text=True))

    def test_correct_username_and_password_signs_in(self):
        response = self.client.post("/login", data={
            "username": "editor",
            "password": "s3cret",
            "next": "/",
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        dashboard = self.client.get("/", follow_redirects=False)
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("Dashboard", dashboard.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
