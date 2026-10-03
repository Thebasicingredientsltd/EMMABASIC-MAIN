"""Where to find our products must be a first-class CRM page.

Run with:  python test_places.py
"""

import os
import re
import sys
import unittest
from urllib.parse import urlencode

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402


def _checkbox(html, name):
    match = re.search(
        r'<input type="checkbox" name="%s"[^>]*>' % re.escape(name),
        html,
    )
    return match.group(0) if match else ""


def _hide_heading_checkbox(html):
    return _checkbox(html, "featured_hideHeading")


def _directory_hide_heading_checkbox(html):
    return _checkbox(html, "directory_hideHeading")


def _on_checkbox(html, index):
    match = re.search(
        r'<input\b[^>]*\bname="on"[^>]*\bvalue="%s"[^>]*>' % index,
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
        featured = (load_data("places").get("featured") or {})
        if featured.get("heading"):
            self.assertIn(featured["heading"], html)
        if featured.get("headingItalic"):
            self.assertIn(featured["headingItalic"], html)
        box = _hide_heading_checkbox(html)
        self.assertTrue(box)
        self.assertNotIn("checked", box)

    def test_form_shows_shop_list_heading(self):
        html = self.client.get("/places").get_data(as_text=True)
        self.assertIn("The heading above the shop list", html)
        self.assertIn("Line one", html)
        self.assertIn("Line two", html)
        self.assertIn("directory_hideHeading", html)
        self.assertIn('name="directory_heading"', html)
        self.assertIn('name="directory_headingItalic"', html)
        featured_italic = (load_data("places").get("directory") or {}).get("headingItalic") or ""
        if featured_italic:
            self.assertIn(featured_italic, html)
        box = _directory_hide_heading_checkbox(html)
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

    def test_hide_directory_heading_omitted_checkbox_stays_visible_then_can_hide(self):
        original = load_data("places")
        try:
            payload = _form_from_places(original)
            payload.pop("directory_hideHeading", None)
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("places")["directory"].get("hideHeading"), False)
            form = self.client.get("/places").get_data(as_text=True)
            self.assertNotIn("checked", _directory_hide_heading_checkbox(form))

            payload["directory_hideHeading"] = "on"
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertIs(load_data("places")["directory"].get("hideHeading"), True)
            form = self.client.get("/places").get_data(as_text=True)
            self.assertIn("checked", _directory_hide_heading_checkbox(form))
            self.assertIn("Hidden on site", form)
        finally:
            with app.app_context():
                save_data("places", original)

    def test_clearing_directory_heading_saves_empty_not_fallback(self):
        original = load_data("places")
        try:
            payload = _form_from_places(original)
            payload["directory_heading"] = ""
            payload["directory_headingItalic"] = ""
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            directory = load_data("places")["directory"]
            self.assertEqual(directory.get("heading"), "")
            self.assertEqual(directory.get("headingItalic"), "")
        finally:
            with app.app_context():
                save_data("places", original)

    def test_highlight_checkbox_sets_and_clears_without_losing_the_shop(self):
        original = load_data("places")
        try:
            before = (original.get("shops") or [])[0]
            payload = _form_from_places(original)
            payload["shop0_highlight"] = "on"
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("places")["shops"][0]
            self.assertIs(saved.get("highlight"), True)
            self.assertEqual(saved.get("name"), before.get("name"))
            self.assertEqual(saved.get("lat"), before.get("lat"))
            self.assertEqual(saved.get("lng"), before.get("lng"))
            self.assertEqual(saved.get("postcode"), before.get("postcode"))
            form = self.client.get("/places").get_data(as_text=True)
            self.assertIn("Highlight on the map", form)
            self.assertIn("checked", _on_checkbox(form, "0"))

            payload = _form_from_places(load_data("places"))
            payload.pop("shop0_highlight", None)
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            cleared = load_data("places")["shops"][0]
            self.assertNotIn("highlight", cleared)
            self.assertEqual(cleared.get("lat"), before.get("lat"))
            self.assertEqual(cleared.get("lng"), before.get("lng"))
            form = self.client.get("/places").get_data(as_text=True)
            self.assertNotIn("checked", _on_checkbox(form, "0"))
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

    def test_live_directory_honours_empty_and_hide(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        jsx = os.path.join(
            root,
            "Emma-Basic-The-Basic-Ingredients",
            "project",
            "components",
            "SupplierMap.jsx",
        )
        with open(jsx, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("cms.hideHeading", source)
        self.assertIn("cmsCopy", source)
        self.assertIn("EB_PLACES.directory", source)
        self.assertIn('!_hideHeading && (_heading || _headingItalic)', source)
        self.assertIn('Where to find us.', source)
        self.assertIn("Stocked across the UK.", source)

    def test_live_directory_is_a_map_of_the_cms_stockists(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project = os.path.join(root, "Emma-Basic-The-Basic-Ingredients", "project")
        with open(os.path.join(project, "components", "SupplierMap.jsx"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("EB_PLACES.shops", source)
        self.assertIn("L.map(", source)
        self.assertIn("bindPopup", source)
        self.assertNotIn("const STOCKISTS", source)
        with open(os.path.join(project, "Places.html"), encoding="utf-8") as fh:
            places = fh.read()
        self.assertIn("leaflet", places.lower())
        self.assertIn("postcodes.io", source)
        self.assertIn("Search by shop, town or postcode", source)
        self.assertIn("is-highlight", source)
        self.assertIn("s.highlight", source)
        order = [places.index(tag) for tag in (
            "<StockistCarousel", "<SupplierMap", "<HowToOrder",
        )]
        self.assertEqual(order, sorted(order))
        self.assertNotIn("NearestShopFinder", places)
        self.assertIn("SupplierMap.jsx?v=8", places)
        self.assertNotIn("SupplierMap.jsx?v=5", places)

    def test_hq_map_is_on_people_not_find_us(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project = os.path.join(root, "Emma-Basic-The-Basic-Ingredients", "project")
        with open(os.path.join(project, "Places.html"), encoding="utf-8") as fh:
            places = fh.read()
        with open(os.path.join(project, "People & Places.html"), encoding="utf-8") as fh:
            people = fh.read()
        self.assertNotIn("LocationMap.jsx", places)
        self.assertNotIn("<LocationMap", places)
        self.assertIn("LocationMap.jsx", people)
        self.assertIn("<LocationMap", people)
        self.assertIn("data/places.js", people)
        self.assertIn("leaflet", people.lower())

    def test_highlight_save_does_not_post_the_directory(self):
        original = load_data("places")
        shops = original.get("shops") or []
        self.assertGreater(len(shops), 2)
        before = shops[0]
        address = before.get("address") or ""
        self.assertTrue(address)
        page = self.client.get("/places").get_data(as_text=True)
        self.assertIn("/places/highlights", page)
        self.assertIn("Save highlights", page)
        self.assertIn("Save this shop", page)
        self.assertNotIn('name="shop0_name"', page)
        self.assertNotIn('name="shop0_address"', page)
        self.assertNotIn('name="shop_count"', page)
        try:
            turned_on = {"id": ["1"], "on": ["1"]}
            body = urlencode(turned_on, doseq=True).encode("utf-8")
            self.assertLess(len(body), 20000)
            self.assertNotIn(address.encode("utf-8"), body)
            self.assertNotIn(b"shop0_", body)
            response = self.client.post("/places/highlights", data=turned_on)
            self.assertEqual(response.status_code, 302)
            saved = load_data("places")["shops"]
            self.assertIs(saved[1].get("highlight"), True)
            self.assertEqual(saved[1].get("lat"), shops[1].get("lat"))
            self.assertEqual(saved[1].get("lng"), shops[1].get("lng"))
            self.assertEqual(saved[1].get("postcode"), shops[1].get("postcode"))
            self.assertEqual(saved[1].get("name"), shops[1].get("name"))
            self.assertEqual(saved[0].get("highlight"), before.get("highlight"))
            self.assertEqual(saved[2], shops[2])

            only_first = {"id": ["0"], "on": ["0"]}
            response = self.client.post("/places/highlights", data=only_first)
            self.assertEqual(response.status_code, 302)
            saved = load_data("places")["shops"]
            self.assertIs(saved[0].get("highlight"), True)
            self.assertEqual(saved[0].get("lat"), before.get("lat"))
            self.assertEqual(saved[0].get("lng"), before.get("lng"))
            self.assertEqual(saved[0].get("postcode"), before.get("postcode"))
            self.assertEqual(saved[0].get("address"), address)
            self.assertIs(saved[1].get("highlight"), True)
            self.assertEqual(saved[2], shops[2])
            form = self.client.get("/places").get_data(as_text=True)
            self.assertIn("checked", _on_checkbox(form, "0"))

            response = self.client.post("/places/highlights", data={"id": ["0"]})
            self.assertEqual(response.status_code, 302)
            cleared = load_data("places")["shops"]
            self.assertNotIn("highlight", cleared[0])
            self.assertEqual(cleared[0].get("lat"), before.get("lat"))
            self.assertEqual(cleared[0].get("lng"), before.get("lng"))
            self.assertEqual(cleared[0].get("postcode"), before.get("postcode"))
            self.assertEqual(cleared[0].get("address"), address)
            self.assertIs(cleared[1].get("highlight"), True)
            self.assertEqual(len(cleared), len(shops))
            form = self.client.get("/places").get_data(as_text=True)
            self.assertNotIn("checked", _on_checkbox(form, "0"))
        finally:
            with app.app_context():
                save_data("places", original)

    def test_saving_one_shop_leaves_the_others_alone(self):
        original = load_data("places")
        shops = original.get("shops") or []
        before = shops[0]
        payload = {
            "name": before.get("name") or "",
            "city": before.get("city") or "",
            "address": before.get("address") or "",
            "postcode": before.get("postcode") or "",
            "url": before.get("url") or "",
            "phone": before.get("phone") or "",
            "lat": "" if before.get("lat") is None else str(before.get("lat")),
            "lng": "" if before.get("lng") is None else str(before.get("lng")),
            "highlight": "on",
        }
        self.assertFalse(any(key.startswith("shop") for key in payload))
        try:
            response = self.client.post("/places/shop/0", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("places")["shops"]
            self.assertIs(saved[0].get("highlight"), True)
            self.assertEqual(saved[0].get("name"), before.get("name"))
            self.assertEqual(saved[0].get("lat"), before.get("lat"))
            self.assertEqual(saved[0].get("lng"), before.get("lng"))
            self.assertEqual(saved[0].get("postcode"), before.get("postcode"))
            self.assertEqual(saved[1], shops[1])
            self.assertEqual(len(saved), len(shops))

            payload["highlight"] = ""
            response = self.client.post("/places/shop/0", data=payload)
            self.assertEqual(response.status_code, 302)
            cleared = load_data("places")["shops"]
            self.assertNotIn("highlight", cleared[0])
            self.assertEqual(cleared[0].get("lat"), before.get("lat"))
            self.assertEqual(cleared[1], shops[1])
        finally:
            with app.app_context():
                save_data("places", original)

    def test_page_save_without_stockist_fields_keeps_every_shop(self):
        original = load_data("places")
        try:
            payload = _form_from_places(original)
            for key in list(payload):
                if key.startswith("shop"):
                    payload.pop(key)
            self.assertNotIn("shop_count", payload)
            self.assertNotIn("shop0_name", payload)
            response = self.client.post("/places/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(load_data("places").get("shops"), original.get("shops"))
        finally:
            with app.app_context():
                save_data("places", original)

    def test_add_and_remove_shop_touch_only_that_row(self):
        from unittest import mock
        import stockists_import as si
        original = load_data("places")

        def fake(postcodes):
            return {"BS1 4DJ": (51.4545, -2.5879)}

        try:
            with mock.patch.object(si, "lookup_postcodes", fake):
                response = self.client.post("/places/shop/add", data={
                    "name": "Pin Lookup Shop",
                    "city": "Bristol",
                    "address": "27 Philpot Ln",
                    "postcode": "bs1 4dj",
                    "url": "",
                    "phone": "",
                    "lat": "",
                    "lng": "",
                })
            self.assertEqual(response.status_code, 302)
            shops = load_data("places")["shops"]
            self.assertEqual(len(shops), len(original["shops"]) + 1)
            self.assertEqual(shops[0], original["shops"][0])
            added = shops[-1]
            self.assertEqual(added["name"], "Pin Lookup Shop")
            self.assertEqual(added["postcode"], "BS1 4DJ")
            self.assertEqual((added["lat"], added["lng"]), (51.4545, -2.5879))
            self.assertNotIn("highlight", added)

            response = self.client.post("/places/shop/0/remove")
            self.assertEqual(response.status_code, 302)
            shops = load_data("places")["shops"]
            self.assertEqual(shops[0], original["shops"][1])
            self.assertEqual(shops[-1]["name"], "Pin Lookup Shop")
        finally:
            with app.app_context():
                save_data("places", original)


def _form_from_places(data):
    hero = data.get("hero") or {}
    featured = data.get("featured") or {}
    directory = data.get("directory") or {}
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
        "directory_heading": directory.get("heading", "Where to find us."),
        "directory_headingItalic": directory.get("headingItalic", "Stocked across the UK."),
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
    if directory.get("hideHeading"):
        payload["directory_hideHeading"] = "on"
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
        if item.get("highlight"):
            payload["shop%d_highlight" % i] = "on"
    return payload


if __name__ == "__main__":
    unittest.main()
