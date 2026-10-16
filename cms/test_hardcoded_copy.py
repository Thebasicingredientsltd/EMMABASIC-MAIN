"""Public-site copy that was hardcoded now has a CMS field and a live bind.

Run with:  python test_hardcoded_copy.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402
from test_homepage_social import _form_from_homepage  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")


class ProductRailHeadingTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_rail_page_has_heading_field(self):
        html = self.client.get("/products").get_data(as_text=True)
        self.assertIn('name="rail_heading"', html)
        self.assertTrue(
            "Our team's staples." in html or "Our team&#39;s staples." in html,
            html[html.find("rail_heading"): html.find("rail_heading") + 80] if "rail_heading" in html else html[:200],
        )

    def test_save_round_trips_rail_heading(self):
        original = load_data("homepage")
        try:
            response = self.client.post("/products/rail/save", data={
                "rail_heading": "CRM rail heading marker",
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                (load_data("homepage").get("productRail") or {}).get("heading"),
                "CRM rail heading marker",
            )
        finally:
            with app.app_context():
                save_data("homepage", original)

    def test_live_rail_reads_homepage_json(self):
        path = os.path.join(PROJECT, "components", "ProductRail.jsx")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("EB_HOME", src)
        self.assertIn("productRail", src)
        self.assertIn("Our team's staples.", src)


class ShelfTagTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_comparison_has_tag_fields(self):
        html = self.client.get("/homepage").get_data(as_text=True)
        self.assertIn('name="shelf_theirsTag"', html)
        self.assertIn('name="shelf_oursTag"', html)
        self.assertIn('name="shelf_oursSignoff"', html)

    def test_save_keeps_tags_and_homepage_save_without_them_leaves_them(self):
        original = load_data("homepage")
        try:
            payload = _form_from_homepage(original)
            payload["shelf_theirsTag"] = "CRM theirs tag"
            payload["shelf_oursTag"] = "CRM ours tag"
            payload["shelf_oursSignoff"] = "— CRM"
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            shelf = load_data("homepage").get("shelfTest") or {}
            self.assertEqual(shelf.get("theirsTag"), "CRM theirs tag")
            self.assertEqual(shelf.get("oursTag"), "CRM ours tag")
            self.assertEqual(shelf.get("oursSignoff"), "— CRM")

            payload = _form_from_homepage(load_data("homepage"))
            payload.pop("shelf_theirsTag", None)
            payload.pop("shelf_oursTag", None)
            payload.pop("shelf_oursSignoff", None)
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            shelf = load_data("homepage").get("shelfTest") or {}
            self.assertEqual(shelf.get("theirsTag"), "CRM theirs tag")
        finally:
            with app.app_context():
                save_data("homepage", original)

    def test_live_shelf_reads_tag_fields(self):
        path = os.path.join(PROJECT, "components", "ShelfTest.jsx")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("theirsTag", src)
        self.assertIn("oursTag", src)
        self.assertIn("Nothing else.", src)


class SiteMenuTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_has_public_menu_fields(self):
        html = self.client.get("/homepage").get_data(as_text=True)
        self.assertIn('data-cms-card="homepage.menu"', html)
        self.assertIn('name="nav_wordmark"', html)
        self.assertIn('name="nav_left0_label"', html)
        self.assertIn('name="nav_right0_label"', html)
        self.assertIn("Products Without E-Numbers", html)

    def test_nav_save_round_trips(self):
        original = load_data("nav")
        try:
            response = self.client.post("/nav/save", data={
                "nav_wordmark": "CRM Wordmark",
                "nav_left0_label": "CRM Left",
                "nav_left0_href": "Our Products.html",
                "nav_right0_label": "CRM Right",
                "nav_right0_href": "Journal.html",
            })
            self.assertEqual(response.status_code, 302)
            nav = load_data("nav")
            self.assertEqual(nav.get("wordmark"), "CRM Wordmark")
            self.assertEqual((nav.get("left") or [])[0].get("label"), "CRM Left")
            self.assertEqual((nav.get("right") or [])[0].get("label"), "CRM Right")
        finally:
            with app.app_context():
                save_data("nav", original)

    def test_live_topnav_reads_wordmark(self):
        path = os.path.join(PROJECT, "components", "TopNav.jsx")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("nav.wordmark", src)


class MatchaContentTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_matcha_editor_shows_page_copy_fields(self):
        html = self.client.get("/matcha").get_data(as_text=True)
        self.assertIn('name="pouch_heading"', html)
        self.assertIn('name="usp0_heading"', html)
        self.assertIn('name="nutrition0_label"', html)
        self.assertIn("100% Pure Matcha", html)

    def test_matcha_save_round_trips_usp(self):
        original = load_data("matcha")
        try:
            hero = original.get("hero") or {}
            payload = {
                "hero_eyebrow": hero.get("eyebrow", ""),
                "hero_title": hero.get("title", ""),
                "hero_titleItalic": hero.get("titleItalic", ""),
                "hero_subtitle": hero.get("subtitle", ""),
                "hero_visible": "on",
                "footer_visible": "on",
                "pouch_heading": "What's in",
                "pouch_headingItalic": "the pouch.",
                "pouch_body": "CRM pouch marker",
                "usp0_number": "01",
                "usp0_heading": "CRM USP heading",
                "usp0_body": "CRM USP body",
            }
            response = self.client.post("/matcha/save", data=payload)
            self.assertEqual(response.status_code, 302)
            data = load_data("matcha")
            self.assertEqual((data.get("pouch") or {}).get("body"), "CRM pouch marker")
            self.assertEqual((data.get("usps") or {}).get("items")[0]["heading"], "CRM USP heading")
        finally:
            with app.app_context():
                save_data("matcha", original)

    def test_matcha_save_without_copy_fields_leaves_usps(self):
        original = load_data("matcha")
        try:
            data = dict(original)
            data["usps"] = {
                "items": [{"number": "01", "heading": "must-survive", "body": "x"}],
            }
            with app.app_context():
                save_data("matcha", data)
            hero = data.get("hero") or {}
            response = self.client.post("/matcha/save", data={
                "hero_eyebrow": hero.get("eyebrow", ""),
                "hero_title": hero.get("title", ""),
                "hero_titleItalic": hero.get("titleItalic", ""),
                "hero_subtitle": hero.get("subtitle", ""),
                "hero_visible": "on",
                "footer_visible": "on",
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                ((load_data("matcha").get("usps") or {}).get("items") or [{}])[0].get("heading"),
                "must-survive",
            )
        finally:
            with app.app_context():
                save_data("matcha", original)

    def test_live_matcha_reads_eb_matcha(self):
        path = os.path.join(PROJECT, "Matcha Lab.html")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("EB_MATCHA", src)
        self.assertIn("usps", src)
        self.assertIn("100% Pure Matcha", src)


class JournalCategoryTests(unittest.TestCase):
    def test_journal_index_reads_categories_from_posts(self):
        path = os.path.join(PROJECT, "components", "Journal.jsx")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("JOURNAL_POSTS", src)
        self.assertNotIn(
            'const CATEGORIES = ["All", "Recipes", "Ingredient Stories", "Behind the Product", "The Grit"];',
            src,
        )


if __name__ == "__main__":
    unittest.main()
