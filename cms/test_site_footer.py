"""The CMS Page footer card edits the shared live SiteFooter, stored in site.js.

Run with:  python test_site_footer.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import _find_cms_cards, app, load_data, save_data  # noqa: E402
from test_homepage_social import _form_from_homepage  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
SECTIONS_JSX = os.path.join(PROJECT, "components", "Sections.jsx")

LIVE_CONTACT_BODY = (
    "If any Emma Basic product does not live up to your expectations, "
    "reach out and we will make every effort to arrange a replacement or refund."
)
LIVE_EMAIL = "Boris@thebasicingredients.com"
LIVE_LONDON = "4 New Concordia Wharf"
LIVE_ROTTERDAM = "Westplein 12–14"


def _homepage_footer_card(html):
    hits = {
        card_id: html[start:end]
        for card_id, start, end in _find_cms_cards(html)
    }
    return hits.get("homepage.footer") or ""


def _full_footer_form(overrides=None):
    """Homepage save payload plus the shared site-footer fields."""
    payload = _form_from_homepage(load_data("homepage"))
    payload.update({
        "site_footer_contact_heading": "Get in touch",
        "site_footer_contact_body": LIVE_CONTACT_BODY,
        "site_footer_email_label": "Email",
        "site_footer_email": LIVE_EMAIL,
        "site_footer_london_heading": "London",
        "site_footer_london_lines": (
            "The Basic Ingredients Ltd\n"
            "4 New Concordia Wharf\n"
            "Mill Street\n"
            "London SE1 2BB"
        ),
        "site_footer_rotterdam_heading": "Rotterdam",
        "site_footer_rotterdam_lines": (
            "The Basic Ingredients B.V.\n"
            "Westplein 12–14\n"
            "3016BM Rotterdam\n"
            "The Netherlands"
        ),
        "site_footer_wordmark": "Emma\nBasic.",
        "site_footer_browse_heading": "Browse",
        "site_footer_browse0_label": "Matcha",
        "site_footer_browse0_href": "Our Products.html#cat-matcha",
        "site_footer_browse1_label": "Oils",
        "site_footer_browse1_href": "Our Products.html#cat-oils",
        "site_footer_browse2_label": "Pantry",
        "site_footer_browse2_href": "Our Products.html#cat-pantry",
        "site_footer_browse3_label": "Full Collection",
        "site_footer_browse3_href": "Our Products.html",
        "site_footer_company_heading": "Company",
        "site_footer_company0_label": "Our Story",
        "site_footer_company0_href": "Our Story.html",
        "site_footer_company1_label": "People & Places",
        "site_footer_company1_href": "People%20%26%20Places.html",
        "site_footer_company2_label": "Find us",
        "site_footer_company2_href": "Places.html",
        "site_footer_company3_label": "Journal",
        "site_footer_company3_href": "Journal.html",
        "site_footer_legal_left": "© The Basic Ingredients Ltd · MMXXVI",
        "site_footer_legal_center": "No Additives. Ever.",
        "site_footer_legal_right": "London · Rotterdam",
    })
    if overrides:
        payload.update(overrides)
    return payload


class SiteFooterCmsTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_page_footer_card_shows_live_footer_fields(self):
        html = self.client.get("/homepage").get_data(as_text=True)
        card = _homepage_footer_card(html)
        self.assertIn('data-cms-card="homepage.footer"', card)
        self.assertIn('name="footer_visible"', card)
        self.assertIn("Show footer on this page", card)
        self.assertIn("shared site footer", card.lower())
        for name in (
            "site_footer_contact_heading",
            "site_footer_contact_body",
            "site_footer_email_label",
            "site_footer_email",
            "site_footer_london_heading",
            "site_footer_london_lines",
            "site_footer_rotterdam_heading",
            "site_footer_rotterdam_lines",
            "site_footer_wordmark",
            "site_footer_browse_heading",
            "site_footer_browse0_label",
            "site_footer_company_heading",
            "site_footer_company0_label",
            "site_footer_legal_left",
        ):
            self.assertIn('name="%s"' % name, card, name)
        self.assertIn(LIVE_EMAIL, card)
        self.assertIn(LIVE_LONDON, card)
        self.assertIn(LIVE_ROTTERDAM, card)
        self.assertIn("Get in touch", card)
        self.assertIn("Matcha", card)
        self.assertIn("Our Story", card)

    def test_save_round_trips_site_footer_without_writing_homepage_copy(self):
        home_original = load_data("homepage")
        site_original = load_data("site")
        marker = "CRM footer round-trip marker — unique"
        try:
            payload = _full_footer_form({
                "site_footer_contact_body": marker,
                "site_footer_email": "roundtrip@example.com",
            })
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            footer = (load_data("site").get("footer") or {})
            self.assertEqual(footer.get("contactBody"), marker)
            self.assertEqual(footer.get("email"), "roundtrip@example.com")
            self.assertEqual(footer.get("londonLines")[1], LIVE_LONDON)
            browse = footer.get("browseLinks") or []
            self.assertEqual(browse[0].get("label"), "Matcha")
            home_footer = load_data("homepage").get("footer") or {}
            self.assertNotIn("contactBody", home_footer)
            self.assertIsNot(home_footer.get("visible"), False)
            html = self.client.get("/homepage").get_data(as_text=True)
            self.assertIn(marker, _homepage_footer_card(html))
        finally:
            with app.app_context():
                save_data("homepage", home_original)
                save_data("site", site_original)

    def test_homepage_save_without_footer_copy_leaves_site_footer(self):
        site_original = load_data("site")
        home_original = load_data("homepage")
        try:
            data = dict(load_data("site"))
            footer = dict(data.get("footer") or {})
            footer["contactBody"] = "must-survive-homepage-save"
            data["footer"] = footer
            with app.app_context():
                save_data("site", data)
            payload = _form_from_homepage(load_data("homepage"))
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                (load_data("site").get("footer") or {}).get("contactBody"),
                "must-survive-homepage-save",
            )
        finally:
            with app.app_context():
                save_data("homepage", home_original)
                save_data("site", site_original)

    def test_visual_preview_still_loads_site_js(self):
        html = self.client.get("/preview/home").get_data(as_text=True)
        self.assertIn("site.js", html)
        self.assertNotIn("maintenance.js", html)

    def test_live_site_footer_reads_eb_site_with_hardcoded_fallback(self):
        with open(SECTIONS_JSX, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("function SiteFooter", src)
        self.assertIn("EB_SITE", src)
        self.assertIn(LIVE_EMAIL, src)
        self.assertIn(LIVE_CONTACT_BODY, src)
        self.assertIn(LIVE_LONDON, src)
        self.assertIn(LIVE_ROTTERDAM, src)


if __name__ == "__main__":
    unittest.main()
