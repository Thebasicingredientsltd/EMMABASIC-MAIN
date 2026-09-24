"""CMS Search & sharing (SEO) fields persist and reach public HTML.

Run with:  python test_seo.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import seo  # noqa: E402
from app import app, load_data, save_data  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
HOMEPAGE_HTML = os.path.join(PROJECT, "Emma Basic Homepage.html")
PRODUCT_HTML = os.path.join(PROJECT, "product.html")
JOURNAL_POST_HTML = os.path.join(PROJECT, "journal-post.html")


class SeoHelperTests(unittest.TestCase):
    def test_inject_replaces_title_and_is_idempotent(self):
        html = "<html><head><title>Old</title></head><body></body></html>"
        block = seo.render_head_block({
            "title": "Emma Basic",
            "description": "A quiet description.",
            "canonical": "https://emmabasic.co.uk/",
            "image": "assets/hero.jpg",
            "ogType": "website",
            "noindex": False,
        })
        once = seo.inject_head_block(html, block)
        twice = seo.inject_head_block(once, block)
        self.assertEqual(once.count("<!--cms-seo-start-->"), 1)
        self.assertEqual(twice.count("<!--cms-seo-start-->"), 1)
        self.assertIn('meta name="description"', once)
        self.assertIn("og:title", once)
        self.assertIn("A quiet description.", once)
        self.assertNotIn("<title>Old</title>", once)

    def test_noindex_adds_robots(self):
        block = seo.render_head_block({
            "title": "Hidden",
            "description": "",
            "canonical": "https://emmabasic.co.uk/Places.html",
            "image": "",
            "ogType": "website",
            "noindex": True,
        })
        self.assertIn('name="robots"', block)
        self.assertIn("noindex", block)

    def test_resolve_uses_stored_description(self):
        page = seo.page_by_id("homepage")
        data = {
            "hero": {"body": "Fallback body", "image": "assets/hero.jpg"},
            "seo": {"description": "Stored description", "title": "Stored title"},
        }
        resolved = seo.resolve_seo(page, data)
        self.assertEqual(resolved["title"], "Stored title")
        self.assertEqual(resolved["description"], "Stored description")
        self.assertTrue(resolved["canonical"].startswith("https://emmabasic.co.uk"))

    def test_blank_seo_detection(self):
        self.assertTrue(seo.seo_is_blank({"title": "", "ogType": "website", "noindex": False}))
        self.assertFalse(seo.seo_is_blank({"title": "", "noindex": True}))
        self.assertFalse(seo.seo_is_blank({"description": "Hello"}))


class SeoCmsTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_every_site_page_form_has_seo_section(self):
        urls = [
            "/homepage", "/catalog", "/journal", "/story", "/people",
            "/places", "/distributor", "/company", "/matcha",
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            html = response.get_data(as_text=True)
            self.assertIn("Search &amp; sharing (SEO)", html, url)
            self.assertIn("seo_description", html, url)
            self.assertIn("seo_noindex", html, url)
            self.assertIn("Google and WhatsApp/Facebook", html, url)

    def test_journal_and_product_editors_have_seo(self):
        journal = self.client.get("/journal/0")
        self.assertEqual(journal.status_code, 200)
        self.assertIn("seo_title", journal.get_data(as_text=True))
        catalog_html = self.client.get("/catalog").get_data(as_text=True)
        self.assertIn("/catalog/product/", catalog_html)

    def test_homepage_save_writes_js_and_html_then_restores(self):
        original = load_data("homepage")
        marker = "CRM-SEO-TEST-DESCRIPTION"
        try:
            hero = original.get("hero") or {}
            payload = {
                "hero_headlineLine1": hero.get("headlineLine1", ""),
                "hero_headlineLine2": hero.get("headlineLine2", ""),
                "hero_body": hero.get("body", ""),
                "hero_image": hero.get("image", ""),
                "hero_visible": "on",
                "footer_visible": "on",
                "seo_title": "Emma Basic test title",
                "seo_description": marker,
                "seo_canonical": "https://emmabasic.co.uk/",
                "seo_og_type": "website",
            }
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("homepage")
            self.assertEqual(saved.get("seo", {}).get("description"), marker)
            self.assertFalse(saved.get("seo", {}).get("noindex"))
            with open(HOMEPAGE_HTML, encoding="utf-8") as fh:
                html = fh.read()
            self.assertIn(marker, html)
            self.assertIn("<!--cms-seo-start-->", html)
            self.assertIn('property="og:title"', html)
            self.assertIn("components/seo.js", html)
        finally:
            with app.app_context():
                save_data("homepage", original)

    def test_catalog_product_editor_has_seo(self):
        response = self.client.get("/catalog/product/0/0")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Search &amp; sharing (SEO)", html)
        self.assertIn("seo_description", html)

    def test_noindex_unchecked_stays_off(self):
        original = load_data("story")
        try:
            hero = original.get("hero") or {}
            payload = {
                "hero_eyebrow": hero.get("eyebrow", ""),
                "hero_title": hero.get("title", ""),
                "hero_titleItalic": hero.get("titleItalic", ""),
                "hero_subtitle": hero.get("subtitle", ""),
                "hero_visible": "on",
                "footer_visible": "on",
                "seo_title": "Our Story",
                "seo_description": "Story description for SEO test.",
                "seo_og_type": "website",
            }
            response = self.client.post("/story/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertFalse(load_data("story").get("seo", {}).get("noindex"))
        finally:
            with app.app_context():
                save_data("story", original)


if __name__ == "__main__":
    unittest.main()
