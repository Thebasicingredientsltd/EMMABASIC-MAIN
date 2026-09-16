"""Where to find our products must be a first-class CRM page.

Run with:  python test_places.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402


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
