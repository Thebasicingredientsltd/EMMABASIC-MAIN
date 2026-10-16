"""CMS sidebar groups: pick which page sits under which menu.

Nested page groups start collapsed. The group that contains the page you
are on opens so you can still see where you are. Section headers (Main
menu, Other pages, Tools) stay expanded so every page is one click away.

Run with:  python test_cms_menu.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, cms_sidebar_tree, load_site, save_data  # noqa: E402


def _sidebar(html):
    match = re.search(r'<nav class="sidebar-nav">(.*?)</nav>', html, re.S)
    return match.group(1) if match else html


class CmsMenuTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.original_site = load_site()

    def tearDown(self):
        with app.app_context():
            save_data("site", self.original_site)

    def test_settings_page_lists_every_website_page(self):
        html = self.client.get("/cms-menu").get_data(as_text=True)
        self.assertEqual(self.client.get("/cms-menu").status_code, 200)
        self.assertIn('name="parent_story"', html)
        self.assertIn('name="parent_places"', html)
        self.assertIn("Our Story", html)
        self.assertIn("Find us", html)
        self.assertIn("Top of the sidebar", html)

    def test_save_nests_a_page_under_a_menu(self):
        response = self.client.post("/cms-menu/save", data={
            "parent_story": "people",
            "parent_matcha": "catalog",
        })
        self.assertEqual(response.status_code, 302)
        parents = (load_site().get("cmsMenu") or {}).get("parents") or {}
        self.assertEqual(parents.get("story"), "people")
        self.assertEqual(parents.get("matcha"), "catalog")

    def test_sidebar_nests_and_starts_collapsed_on_the_dashboard(self):
        with app.app_context():
            data = dict(load_site())
            data["cmsMenu"] = {"parents": {"story": "people"}}
            save_data("site", data)

        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Our Story", html)
        self.assertIn("People &amp; Places", html)
        self.assertIn('class="nav-group"', html)
        self.assertNotIn('class="nav-group" open', html)
        people_at = html.find("People &amp; Places")
        story_at = html.find("Our Story")
        self.assertGreater(story_at, people_at)

    def test_current_page_group_opens_when_you_are_on_the_nested_page(self):
        with app.app_context():
            data = dict(load_site())
            data["cmsMenu"] = {"parents": {"story": "people"}}
            save_data("site", data)

        html = self.client.get("/story").get_data(as_text=True)
        self.assertIn('class="nav-group" open', html)

    def test_two_level_nesting_is_flattened_to_one(self):
        response = self.client.post("/cms-menu/save", data={
            "parent_people": "homepage",
            "parent_story": "people",
        })
        self.assertEqual(response.status_code, 302)
        parents = (load_site().get("cmsMenu") or {}).get("parents") or {}
        self.assertEqual(parents.get("people"), "homepage")
        self.assertNotEqual(parents.get("story"), "people")

    def test_tree_helper_groups_children_under_parent(self):
        with app.app_context():
            data = dict(load_site())
            data["cmsMenu"] = {"parents": {"story": "people", "matcha": "catalog"}}
            save_data("site", data)
        tree = cms_sidebar_tree("story")
        people = next(n for n in tree["pages"] if n["endpoint"] == "people")
        self.assertEqual([c["endpoint"] for c in people["children"]], ["story"])
        self.assertTrue(people["open"])
        catalog = next(n for n in tree["pages"] if n["endpoint"] == "catalog")
        self.assertEqual([c["endpoint"] for c in catalog["children"]], ["matcha"])
        self.assertFalse(catalog["open"])
        self.assertFalse(any(n["endpoint"] == "story" for n in tree["pages"]))

    def test_sidebar_lists_pages_without_collapsing_menu_groups(self):
        html = self.client.get("/journal").get_data(as_text=True)
        sidebar = _sidebar(html)
        self.assertNotIn('class="nav-section"', sidebar)
        self.assertIn("Field Notes", sidebar)
        self.assertIn("Our Products", sidebar)
        self.assertIn("Find us", sidebar)
        self.assertIn(">Main menu<", sidebar)
        self.assertIn(">Other pages<", sidebar)
        self.assertIn(">Tools<", sidebar)

    def test_nested_group_stays_collapsed_when_another_page_is_open(self):
        with app.app_context():
            data = dict(load_site())
            data["cmsMenu"] = {"parents": {"story": "people"}}
            save_data("site", data)

        html = self.client.get("/catalog").get_data(as_text=True)
        self.assertIn('class="nav-group"', html)
        self.assertNotIn('class="nav-group" open', html)

    def test_nested_page_opens_its_parent_group(self):
        with app.app_context():
            data = dict(load_site())
            data["cmsMenu"] = {"parents": {"story": "people"}}
            save_data("site", data)

        html = self.client.get("/story").get_data(as_text=True)
        self.assertIn('class="nav-group" open', html)
        self.assertNotIn('class="nav-section"', _sidebar(html))

    def test_phone_hamburger_collapses_nested_page_groups_only(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('querySelectorAll("details.nav-group")', html)
        self.assertNotIn("details.nav-section", html)
