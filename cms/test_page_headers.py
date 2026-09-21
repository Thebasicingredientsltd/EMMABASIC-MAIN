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
                    "hero_visible": "on",
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

    def test_page_header_forms_have_visibility_checkbox(self):
        for path in (
            "/people",
            "/catalog",
            "/journal",
            "/homepage",
            "/story",
            "/places",
            "/distributor",
            "/company",
            "/matcha",
        ):
            html = self.client.get(path).get_data(as_text=True)
            self.assertIn("hero_visible", html, path)
            self.assertIn("Show this page header on the live site", html, path)

    def test_people_header_can_hide_then_restore(self):
        original = load_data("people")
        from test_people_founder import _form_from_people
        try:
            payload = _form_from_people(original)
            payload.pop("hero_visible", None)
            response = self.client.post("/people/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("people")["hero"].get("visible"), False)
            payload["hero_visible"] = "on"
            response = self.client.post("/people/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("people")["hero"].get("visible"), True)
        finally:
            with app.app_context():
                save_data("people", original)

    def test_catalog_header_can_hide_then_restore(self):
        original = load_data("catalog")
        hero = (original.get("hero") if isinstance(original, dict) else None) or {}
        try:
            response = self.client.post(
                "/catalog/hero/save",
                data={
                    "hero_eyebrow": hero.get("eyebrow", ""),
                    "hero_title": hero.get("title", ""),
                    "hero_titleItalic": hero.get("titleItalic", ""),
                    "hero_subtitle": hero.get("subtitle", ""),
                },
            )
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_catalog_bundle()["hero"].get("visible"), False)
            response = self.client.post(
                "/catalog/hero/save",
                data={
                    "hero_eyebrow": hero.get("eyebrow", ""),
                    "hero_title": hero.get("title", ""),
                    "hero_titleItalic": hero.get("titleItalic", ""),
                    "hero_subtitle": hero.get("subtitle", ""),
                    "hero_visible": "on",
                },
            )
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_catalog_bundle()["hero"].get("visible"), True)
        finally:
            with app.app_context():
                save_data("catalog", original)

    def test_live_pages_wire_header_visibility(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project = os.path.join(root, "Emma-Basic-The-Basic-Ingredients", "project")
        people_html = os.path.join(project, "People & Places.html")
        products_html = os.path.join(project, "Our Products.html")
        with open(people_html, encoding="utf-8") as fh:
            self.assertIn("visible={hero.visible}", fh.read())
        with open(products_html, encoding="utf-8") as fh:
            self.assertIn("visible={hero.visible}", fh.read())
        visual = self.client.get("/visual?page=people").get_data(as_text=True)
        self.assertIn("hero.visible", visual)
        self.assertIn("Page header", visual)


if __name__ == "__main__":
    unittest.main()
