"""The Visit the Matcha Lab link is editable and hideable in the CRM.

Run with:  python test_catalog_link.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import (  # noqa: E402
    NUTRITION_KEYS,
    app,
    load_catalog_bundle,
    load_data,
    paras_to_text,
    qa_to_text,
    save_data,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
CATALOG_JSX = os.path.join(PROJECT, "components", "CatalogIndex.jsx")
NAV_JS = os.path.join(PROJECT, "data", "nav.js")


def _checkbox(html, name):
    match = re.search(
        r'<input type="checkbox" name="%s"[^>]*>' % re.escape(name),
        html,
    )
    return match.group(0) if match else ""


def _matcha():
    cats = load_catalog_bundle()["categories"]
    for ci, cat in enumerate(cats):
        if cat.get("id") == "matcha":
            products = cat.get("products") or []
            for pi, prod in enumerate(products):
                if prod.get("id") == "premium-matcha":
                    return ci, pi, cat, prod
            if products:
                return ci, 0, cat, products[0]
            return ci, 0, cat, {}
    raise AssertionError("matcha category missing")


def _category_payload(cat, index):
    link = (cat.get("meta") or {}).get("link") or {}
    payload = {
        "index": str(index),
        "is_new": "0",
        "id": cat.get("id", ""),
        "number": cat.get("number", ""),
        "name": cat.get("name", ""),
        "japanese": cat.get("japanese", ""),
        "blurb": cat.get("blurb", ""),
        "link_label": link.get("label", ""),
        "link_href": link.get("href", ""),
    }
    if link.get("hide"):
        payload["link_hide"] = "on"
    return payload


def _product_payload(prod, ci, pi, cat):
    nutr = prod.get("nutrition") or {}
    edu = prod.get("education") or {}
    link = (cat.get("meta") or {}).get("link") or {}
    payload = {
        "cat_index": str(ci),
        "prod_index": str(pi),
        "is_new": "0",
        "target_cat_index": str(ci),
        "id": prod.get("id", ""),
        "name": prod.get("name", ""),
        "japanese": prod.get("japanese", ""),
        "origin": prod.get("origin", ""),
        "tone": prod.get("tone") or "warm",
        "tagline": prod.get("tagline", ""),
        "amazon": prod.get("amazon", ""),
        "image": prod.get("image", ""),
        "badges": "\n".join(prod.get("badges") or []),
        "pairings": "\n".join(prod.get("pairings") or []),
        "sellingPoints": "\n".join(prod.get("sellingPoints") or []),
        "ingredients": prod.get("ingredients", ""),
        "allergens": prod.get("allergens", ""),
        "nutr_serving": nutr.get("serving", ""),
        "edu_title": edu.get("title", ""),
        "edu_body": paras_to_text(edu.get("body") or []),
        "qa": qa_to_text(prod.get("qa") or []),
        "gallery_path": prod.get("images") or [],
        "link_label": link.get("label", ""),
        "link_href": link.get("href", ""),
    }
    for key, _label in NUTRITION_KEYS:
        val = nutr.get(key)
        if val is not None:
            payload["nutr_" + key] = str(val)
    if link.get("hide"):
        payload["link_hide"] = "on"
    return payload


class CatalogUnderlinkTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_live_catalog_keeps_matcha_lab_link_by_default(self):
        _ci, _pi, cat, _prod = _matcha()
        link = (cat.get("meta") or {}).get("link") or {}
        self.assertEqual(link.get("label"), "Visit the Matcha Lab")
        self.assertEqual(link.get("href"), "Matcha Lab.html")
        self.assertFalse(link.get("hide"))

    def test_category_editor_shows_link_fields(self):
        ci, _pi, cat, _prod = _matcha()
        html = self.client.get("/catalog/category/%d" % ci).get_data(as_text=True)
        self.assertIn("Link under this category", html)
        self.assertIn("Hide this link", html)
        self.assertIn("Visit the Matcha Lab", html)
        self.assertIn("Matcha Lab.html", html)
        box = _checkbox(html, "link_hide")
        self.assertTrue(box)
        self.assertNotIn("checked", box)

    def test_product_editor_shows_link_fields(self):
        ci, pi, _cat, _prod = _matcha()
        html = self.client.get("/catalog/product/%d/%d" % (ci, pi)).get_data(as_text=True)
        self.assertIn("Link under this product", html)
        self.assertIn("Hide this link", html)
        self.assertIn("Visit the Matcha Lab", html)
        self.assertIn("Matcha Lab.html", html)
        box = _checkbox(html, "link_hide")
        self.assertTrue(box)
        self.assertNotIn("checked", box)

    def test_matcha_lab_page_shows_link_fields(self):
        html = self.client.get("/matcha").get_data(as_text=True)
        self.assertIn("Link under Matcha on Our Products", html)
        self.assertIn("Hide this link", html)
        self.assertIn("Visit the Matcha Lab", html)
        self.assertIn("Matcha Lab.html", html)
        box = _checkbox(html, "link_hide")
        self.assertTrue(box)
        self.assertNotIn("checked", box)

    def test_hide_omitted_checkbox_keeps_link_then_can_hide(self):
        original = load_data("catalog")
        ci, _pi, cat, _prod = _matcha()
        try:
            payload = _category_payload(cat, ci)
            payload.pop("link_hide", None)
            response = self.client.post("/catalog/category/save", data=payload)
            self.assertEqual(response.status_code, 302)
            link = (load_catalog_bundle()["categories"][ci].get("meta") or {}).get("link") or {}
            self.assertIs(link.get("hide"), False)
            self.assertEqual(link.get("label"), "Visit the Matcha Lab")
            form = self.client.get("/catalog/category/%d" % ci).get_data(as_text=True)
            self.assertNotIn("checked", _checkbox(form, "link_hide"))

            payload["link_hide"] = "on"
            response = self.client.post("/catalog/category/save", data=payload)
            self.assertEqual(response.status_code, 302)
            link = (load_catalog_bundle()["categories"][ci].get("meta") or {}).get("link") or {}
            self.assertIs(link.get("hide"), True)
            form = self.client.get("/catalog/category/%d" % ci).get_data(as_text=True)
            self.assertIn("checked", _checkbox(form, "link_hide"))
            self.assertIn("Hidden on site", form)
        finally:
            with app.app_context():
                save_data("catalog", original)

    def test_clearing_link_text_saves_empty(self):
        original = load_data("catalog")
        ci, _pi, cat, _prod = _matcha()
        try:
            payload = _category_payload(cat, ci)
            payload["link_label"] = ""
            payload.pop("link_hide", None)
            response = self.client.post("/catalog/category/save", data=payload)
            self.assertEqual(response.status_code, 302)
            link = (load_catalog_bundle()["categories"][ci].get("meta") or {}).get("link") or {}
            self.assertEqual(link.get("label"), "")
            self.assertEqual(link.get("href"), "Matcha Lab.html")
        finally:
            with app.app_context():
                save_data("catalog", original)

    def test_product_save_can_hide_the_category_link(self):
        original = load_data("catalog")
        ci, pi, cat, prod = _matcha()
        try:
            payload = _product_payload(prod, ci, pi, cat)
            payload["link_hide"] = "on"
            response = self.client.post("/catalog/product/save", data=payload)
            self.assertEqual(response.status_code, 302)
            link = (load_catalog_bundle()["categories"][ci].get("meta") or {}).get("link") or {}
            self.assertIs(link.get("hide"), True)
            self.assertEqual(link.get("label"), "Visit the Matcha Lab")
            self.assertEqual(prod.get("name"), load_catalog_bundle()["categories"][ci]["products"][pi]["name"])
        finally:
            with app.app_context():
                save_data("catalog", original)

    def test_matcha_lab_save_can_hide_the_link(self):
        original_matcha = load_data("matcha")
        original_catalog = load_data("catalog")
        try:
            hero = original_matcha.get("hero") or {}
            payload = {
                "hero_eyebrow": hero.get("eyebrow", ""),
                "hero_title": hero.get("title", ""),
                "hero_titleItalic": hero.get("titleItalic", ""),
                "hero_subtitle": hero.get("subtitle", ""),
                "hero_visible": "on",
                "footer_visible": "on",
                "link_label": "Visit the Matcha Lab",
                "link_href": "Matcha Lab.html",
                "link_hide": "on",
            }
            response = self.client.post("/matcha/save", data=payload)
            self.assertEqual(response.status_code, 302)
            _ci, _pi, cat, _prod = _matcha()
            link = (cat.get("meta") or {}).get("link") or {}
            self.assertIs(link.get("hide"), True)
            self.assertEqual(link.get("label"), "Visit the Matcha Lab")
            form = self.client.get("/matcha").get_data(as_text=True)
            self.assertIn("checked", _checkbox(form, "link_hide"))
            self.assertIn("Hidden on site", form)
        finally:
            with app.app_context():
                save_data("matcha", original_matcha)
                save_data("catalog", original_catalog)

    def test_live_page_honours_empty_and_hide(self):
        with open(CATALOG_JSX, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("function categoryUnderlink", source)
        self.assertIn("link.hide === true", source)
        self.assertIn("if (!label || !href) return null", source)

    def test_matcha_lab_not_added_to_public_header(self):
        nav = load_data("nav")
        labels = [item.get("label") for item in (nav.get("left") or []) + (nav.get("right") or [])]
        self.assertNotIn("Matcha Lab", labels)
        with open(NAV_JS, encoding="utf-8") as fh:
            self.assertNotIn("Matcha Lab", fh.read())


if __name__ == "__main__":
    unittest.main()
