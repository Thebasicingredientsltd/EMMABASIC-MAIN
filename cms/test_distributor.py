"""Become a Distributor must be a first-class CRM page, like People.

Run with:  python test_distributor.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402


class DistributorPageTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_distributor_page_is_in_the_sidebar_and_has_a_save_form(self):
        response = self.client.get("/distributor")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/distributor", html)
        self.assertIn("Become a Distributor", html)
        self.assertIn("/distributor/save", html)
        self.assertIn("How to order", html)

    def test_dashboard_links_to_distributor(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/distributor", html)
        self.assertIn("Become a Distributor", html)

    def test_save_updates_hero_copy_then_restores(self):
        original = load_data("people")
        marker = "CRM-DISTRIBUTOR-TEST-EYEBROW"
        try:
            payload = _form_from_people(original)
            payload["hero_eyebrow"] = marker
            response = self.client.post("/distributor/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("people")
            self.assertEqual(saved["distributor"]["eyebrow"], marker)
            self.assertEqual(
                saved["trade"]["heading"],
                (original.get("trade") or {}).get("heading"),
            )
        finally:
            with app.app_context():
                save_data("people", original)


def _form_from_people(data):
    hero = data.get("distributor") or {}
    trade = data.get("trade") or {}
    contact = data.get("contact") or {}
    items = trade.get("items") or []
    payload = {
        "hero_eyebrow": hero.get("eyebrow", ""),
        "hero_title": hero.get("title", ""),
        "hero_titleItalic": hero.get("titleItalic", ""),
        "hero_subtitle": hero.get("subtitle", ""),
        "trade_eyebrow": trade.get("eyebrow", ""),
        "trade_heading": trade.get("heading", ""),
        "trade_intro": trade.get("intro", ""),
        "trade_count": str(len(items)),
        "contact_headingLine1": contact.get("headingLine1", ""),
        "contact_headingLine2": contact.get("headingLine2", ""),
        "contact_body": contact.get("body", ""),
        "contact_regionLabel": contact.get("regionLabel", ""),
        "contact_addressLine1": contact.get("addressLine1", ""),
        "contact_addressLine2": contact.get("addressLine2", ""),
        "contact_email": contact.get("email", ""),
        "contact_note": contact.get("note", ""),
    }
    if trade.get("visible") is not False:
        payload["trade_visible"] = "on"
    if contact.get("visible") is not False:
        payload["contact_visible"] = "on"
    for i, item in enumerate(items):
        payload["trade%d_q" % i] = item.get("q", "")
        payload["trade%d_a" % i] = item.get("a", "")
    return payload


if __name__ == "__main__":
    unittest.main()
