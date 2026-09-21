"""Every public website page must be reachable from the CRM sidebar.

Run with:  python test_site_pages.py
"""

import html
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import CMS_SITE_PAGES, app, load_data, save_data  # noqa: E402

EXPECTED = [
    ("/homepage", "Homepage"),
    ("/catalog", "Our Products"),
    ("/journal", "Field Notes"),
    ("/story", "Our Story"),
    ("/people", "People & Places"),
    ("/places", "Where to find our products"),
    ("/distributor", "Become a Distributor"),
    ("/company", "The Basic Ingredients"),
    ("/matcha", "Matcha Lab"),
]


class SitePagesSidebarTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_registry_covers_every_public_page(self):
        labels = [p["label"] for p in CMS_SITE_PAGES]
        for _url, label in EXPECTED:
            self.assertIn(label, labels)

    def test_each_page_loads_and_appears_in_the_sidebar(self):
        for url, label in EXPECTED:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            html_text = html.unescape(response.get_data(as_text=True))
            self.assertIn(label, html_text)
            for _u, other in EXPECTED:
                self.assertIn(other, html_text)

    def test_new_pages_have_save_forms(self):
        checks = {
            "/story": "/story/save",
            "/matcha": "/matcha/save",
            "/company": "/company/save",
            "/places": "/places/save",
            "/distributor": "/distributor/save",
        }
        for url, action in checks.items():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertIn(action, response.get_data(as_text=True))

    def test_dashboard_cards_include_every_new_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html_text = html.unescape(response.get_data(as_text=True))
        for _url, label in EXPECTED:
            self.assertIn(label, html_text)

    def test_story_and_matcha_save_then_restore(self):
        for key, endpoint in (("story", "/story/save"), ("matcha", "/matcha/save")):
            original = load_data(key)
            marker = "CRM-%s-TEST-EYEBROW" % key.upper()
            try:
                hero = original.get("hero") or {}
                payload = {
                    "hero_eyebrow": marker,
                    "hero_title": hero.get("title", ""),
                    "hero_titleItalic": hero.get("titleItalic", ""),
                    "hero_subtitle": hero.get("subtitle", ""),
                    "hero_visible": "on",
                    "footer_visible": "on",
                }
                response = self.client.post(endpoint, data=payload)
                self.assertEqual(response.status_code, 302, endpoint)
                self.assertEqual(load_data(key)["hero"]["eyebrow"], marker)
            finally:
                with app.app_context():
                    save_data(key, original)

    def test_company_save_then_restore(self):
        original = load_data("company")
        marker = "CRM-COMPANY-TEST-HEADING"
        try:
            hero = original.get("hero") or {}
            about = original.get("about") or {}
            contact = original.get("contact") or {}
            payload = {
                "hero_eyebrow": hero.get("eyebrow", ""),
                "hero_title": hero.get("title", ""),
                "hero_titleItalic": hero.get("titleItalic", ""),
                "hero_subtitle": hero.get("subtitle", ""),
                "hero_visible": "on",
                "footer_visible": "on",
                "about_heading": marker,
                "about_headingItalic": about.get("headingItalic", ""),
                "about_body": about.get("body", ""),
                "about_buttonLabel": about.get("buttonLabel", ""),
                "about_buttonHref": about.get("buttonHref", ""),
                "contact_headingLine1": contact.get("headingLine1", ""),
                "contact_headingLine2": contact.get("headingLine2", ""),
                "contact_body": contact.get("body", ""),
                "contact_regionLabel": contact.get("regionLabel", ""),
                "contact_email": contact.get("email", ""),
                "contact_addressLine1": contact.get("addressLine1", ""),
                "contact_addressLine2": contact.get("addressLine2", ""),
                "contact_note": contact.get("note", ""),
            }
            if contact.get("visible", True) is not False:
                payload["contact_visible"] = "on"
            response = self.client.post("/company/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(load_data("company")["about"]["heading"], marker)
        finally:
            with app.app_context():
                save_data("company", original)


if __name__ == "__main__":
    unittest.main()
