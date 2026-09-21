"""Page headers for People, Our Products, and Field Notes are CMS-editable.

Run with:  python test_page_headers.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_catalog_bundle, load_data, save_data  # noqa: E402


class PageHeaderEditorTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_people_form_names_the_live_headline(self):
        html = self.client.get("/people").get_data(as_text=True)
        self.assertIn("Page header", html)
        self.assertIn("A small operation", html)
        self.assertIn("by design.", html)
        self.assertIn("hero_title", html)
        self.assertIn("hero_titleItalic", html)

    def test_catalog_form_has_products_headline(self):
        html = self.client.get("/catalog").get_data(as_text=True)
        self.assertIn("Small shelf", html)
        self.assertIn("hero_title", html)
        self.assertIn("/catalog/hero/save", html)
        bundle = load_catalog_bundle()
        self.assertIn("categories", bundle)
        self.assertTrue(len(bundle["categories"]) >= 1)
        self.assertEqual(bundle["hero"].get("title"), "Small shelf,")

    def test_catalog_hero_save_then_restore(self):
        original = load_data("catalog")
        try:
            response = self.client.post(
                "/catalog/hero/save",
                data={
                    "hero_eyebrow": "CRM-PRODUCTS-TEST",
                    "hero_title": "Small shelf,",
                    "hero_titleItalic": "big intention.",
                    "hero_subtitle": "test",
                },
            )
            self.assertEqual(response.status_code, 302)
            saved = load_catalog_bundle()
            self.assertEqual(saved["hero"]["eyebrow"], "CRM-PRODUCTS-TEST")
            self.assertTrue(len(saved["categories"]) >= 1)
        finally:
            with app.app_context():
                save_data("catalog", original)

    def test_journal_form_has_field_notes_headline(self):
        html = self.client.get("/journal").get_data(as_text=True)
        self.assertIn("Field Notes", html)
        self.assertIn("hero_subtitle", html)
        self.assertIn("/journal/hero/save", html)


if __name__ == "__main__":
    unittest.main()
