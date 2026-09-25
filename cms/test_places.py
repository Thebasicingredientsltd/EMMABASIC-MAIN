"""Where to find our products must be a first-class CRM page.

Run with:  python test_places.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402


def _hide_heading_checkbox(html):
    match = re.search(
        r'<input type="checkbox" name="featured_hideHeading"[^>]*>',
        html,
    )
    return match.group(0) if match else ""


class PlacesPageTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_places_page_is_in_the_sidebar_and_has_a_save_form(self):
        response = self.client.get("/places")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/places", html)
        self.assertIn("Where to find our products", html)
        self.assertIn("/places/save", html)

    def test_dashboard_links_to_places(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/places", html)
        self.assertIn("Where to find our products", html)

    def test_save_updates_hero_copy_then_restores(self):
        original = load_data("places")
        marker = "CRM-PLACES-TEST-EYEBROW"
        try:
            payload = _form_from_places(original)
            payload["hero_eyebrow"] = marker
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("places")
            self.assertEqual(saved["hero"]["eyebrow"], marker)
            featured = (original.get("featured") or {}).get("retailers") or []
            if featured:
                self.assertEqual(
                    saved["featured"]["retailers"][0]["name"],
                    featured[0]["name"],
                )
        finally:
            with app.app_context():
                save_data("places", original)

    def test_form_shows_find_us_section_heading(self):
        html = self.client.get("/places").get_data(as_text=True)
        self.assertIn("The heading on the Find Us page", html)
        self.assertIn("Section heading", html)
        self.assertIn("Hide this heading", html)
        self.assertIn("featured_hideHeading", html)
        self.assertIn("Listed at a", html)
        self.assertIn("few good places.", html)
        box = _hide_heading_checkbox(html)
        self.assertTrue(box)
        self.assertNotIn("checked", box)

    def test_hide_heading_omitted_checkbox_stays_visible_then_can_hide(self):
        original = load_data("places")
        try:
            payload = _form_from_places(original)
            payload.pop("featured_hideHeading", None)
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("places")["featured"].get("hideHeading"), False)
            form = self.client.get("/places").get_data(as_text=True)
            self.assertNotIn("checked", _hide_heading_checkbox(form))

            payload["featured_hideHeading"] = "on"
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("places")["featured"].get("hideHeading"), True)
            form = self.client.get("/places").get_data(as_text=True)
            self.assertIn("checked", _hide_heading_checkbox(form))
            self.assertIn("Hidden on site", form)
        finally:
            with app.app_context():
                save_data("places", original)

    def test_clearing_section_heading_saves_empty_not_fallback(self):
        original = load_data("places")
        try:
            payload = _form_from_places(original)
            payload["featured_heading"] = ""
            payload["featured_headingItalic"] = ""
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            featured = load_data("places")["featured"]
            self.assertEqual(featured.get("heading"), "")
            self.assertEqual(featured.get("headingItalic"), "")
        finally:
            with app.app_context():
                save_data("places", original)

    def test_live_carousel_honours_empty_and_hide(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        jsx = os.path.join(
            root,
            "Emma-Basic-The-Basic-Ingredients",
            "project",
            "components",
            "StockistCarousel.jsx",
        )
        with open(jsx, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("cms.hideHeading", source)
        self.assertIn("cmsCopy", source)
        self.assertIn('!_hideHeading && (_heading || _headingItalic)', source)


def _form_from_places(data):
    hero = data.get("hero") or {}
    featured = data.get("featured") or {}
    retailers = featured.get("retailers") or []
    shops = data.get("shops") or []
    hq = data.get("hq") or {}
    payload = {
        "hero_eyebrow": hero.get("eyebrow", ""),
        "hero_title": hero.get("title", ""),
        "hero_titleItalic": hero.get("titleItalic", ""),
        "hero_subtitle": hero.get("subtitle", ""),
        "featured_eyebrow": featured.get("eyebrow", ""),
        "featured_heading": featured.get("heading", ""),
        "featured_headingItalic": featured.get("headingItalic", ""),
        "retailer_count": str(len(retailers)),
        "shop_count": str(len(shops)),
        "hq_label": hq.get("label", ""),
        "hq_addressLine1": hq.get("addressLine1", ""),
        "hq_addressLine2": hq.get("addressLine2", ""),
        "hq_lat": "" if hq.get("lat") is None else str(hq.get("lat")),
        "hq_lng": "" if hq.get("lng") is None else str(hq.get("lng")),
    }
    if hero.get("visible") is not False:
        payload["hero_visible"] = "on"
    if (data.get("footer") or {}).get("visible") is not False:
        payload["footer_visible"] = "on"
    if featured.get("hideHeading"):
        payload["featured_hideHeading"] = "on"
    for i, item in enumerate(retailers):
        payload["retailer%d_name" % i] = item.get("name", "")
        payload["retailer%d_city" % i] = item.get("city", "")
        payload["retailer%d_url" % i] = item.get("url", "")
        payload["retailer%d_style" % i] = item.get("style", "")
    for i, item in enumerate(shops):
        payload["shop%d_name" % i] = item.get("name", "")
        payload["shop%d_city" % i] = item.get("city", "")
        payload["shop%d_address" % i] = item.get("address", "")
        payload["shop%d_lat" % i] = "" if item.get("lat") is None else str(item.get("lat"))
        payload["shop%d_lng" % i] = "" if item.get("lng") is None else str(item.get("lng"))
    return payload


if __name__ == "__main__":
    unittest.main()
