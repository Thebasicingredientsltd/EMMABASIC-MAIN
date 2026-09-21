"""Per-page footer visibility is CMS-controlled and persists when unchecked.

Run with:  python test_footer_visibility.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")

CMS_PAGES = (
    "/people",
    "/homepage",
    "/catalog",
    "/journal",
    "/story",
    "/places",
    "/distributor",
    "/company",
    "/matcha",
)


def _footer_checkbox(html):
    match = re.search(r'<input type="checkbox" name="footer_visible"[^>]*>', html)
    return match.group(0) if match else ""


class FooterVisibilityTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_every_cms_page_form_has_footer_checkbox(self):
        for path in CMS_PAGES:
            html = self.client.get(path).get_data(as_text=True)
            self.assertIn("footer_visible", html, path)
            self.assertIn("Show footer on this page", html, path)

    def test_people_uncheck_stays_off_and_homepage_keeps_footer(self):
        from test_people_founder import _form_from_people
        from test_homepage_social import _form_from_homepage

        people_original = load_data("people")
        home_original = load_data("homepage")
        try:
            payload = _form_from_people(people_original)
            payload.pop("footer_visible", None)
            response = self.client.post("/people/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("people")["footer"].get("visible"), False)
            box = _footer_checkbox(self.client.get("/people").get_data(as_text=True))
            self.assertTrue(box)
            self.assertNotIn("checked", box)

            home = load_data("homepage")
            self.assertIsNot(home.get("footer", {}).get("visible"), False)

            payload["footer_visible"] = "on"
            response = self.client.post("/people/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("people")["footer"].get("visible"), True)
            self.assertIn("checked", _footer_checkbox(self.client.get("/people").get_data(as_text=True)))
        finally:
            with app.app_context():
                save_data("people", people_original)
                save_data("homepage", home_original)

    def test_live_people_page_wires_footer_visibility(self):
        people_html = os.path.join(PROJECT, "People & Places.html")
        with open(people_html, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("SiteFooter", src)
        self.assertTrue(
            "footer.visible" in src or "footer || {}).visible" in src or "EB_PEOPLE.footer" in src,
            "People page must pass footer visibility into SiteFooter",
        )
        home_jsx = os.path.join(PROJECT, "components", "App.jsx")
        with open(home_jsx, encoding="utf-8") as fh:
            app_src = fh.read()
        self.assertIn("EB_HOME", app_src)
        self.assertIn("footer", app_src)


if __name__ == "__main__":
    unittest.main()
