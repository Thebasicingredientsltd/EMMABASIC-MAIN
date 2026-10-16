"""Editor cards can sit on a different CRM page than the one they belong to.

Each collapsed card has a Show under control (same idea as the CMS menu).
By default a card stays on its own page. After you pick another menu, it
renders on that page's editor — still saving through its original form.

Run with:  python test_cms_cards.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_site, save_data  # noqa: E402

SEO_CARD = 'data-cms-card="journal.seo"'


class CmsCardHomeTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.original_site = load_site()
        data = dict(self.original_site)
        menu = dict(data.get("cmsMenu") or {})
        menu.pop("cards", None)
        if menu:
            data["cmsMenu"] = menu
        else:
            data.pop("cmsMenu", None)
        with app.app_context():
            save_data("site", data)

    def tearDown(self):
        with app.app_context():
            save_data("site", self.original_site)

    def _set_cards(self, cards):
        with app.app_context():
            data = dict(load_site())
            menu = dict(data.get("cmsMenu") or {})
            menu["cards"] = cards
            data["cmsMenu"] = menu
            save_data("site", data)

    def test_cards_stay_on_their_own_page_by_default(self):
        journal = self.client.get("/journal").get_data(as_text=True)
        story = self.client.get("/story").get_data(as_text=True)
        self.assertIn(SEO_CARD, journal)
        self.assertNotIn(SEO_CARD, story)
        self.assertIn("Search &amp; sharing (SEO)", journal)

    def test_save_assigns_a_card_to_another_menu(self):
        response = self.client.post("/cms-menu/cards/save", data={
            "card": "journal.seo",
            "parent": "story",
        })
        self.assertEqual(response.status_code, 302)
        cards = (load_site().get("cmsMenu") or {}).get("cards") or {}
        self.assertEqual(cards.get("journal.seo"), "story")

    def test_card_appears_on_the_destination_page(self):
        self._set_cards({"journal.seo": "story"})
        story = self.client.get("/story").get_data(as_text=True)
        self.assertIn(SEO_CARD, story)
        self.assertIn("Field Notes — Emma Basic", story)
        self.assertIn("/journal/hero/save", story)

    def test_card_is_missing_from_its_original_page(self):
        self._set_cards({"journal.seo": "story"})
        journal = self.client.get("/journal").get_data(as_text=True)
        self.assertNotIn(SEO_CARD, journal)
        self.assertNotIn("Field Notes — Emma Basic", journal)
        self.assertIn(">Posts<", journal)

    def test_invalid_parent_is_ignored(self):
        response = self.client.post("/cms-menu/cards/save", data={
            "card": "journal.seo",
            "parent": "not-a-menu",
        })
        self.assertEqual(response.status_code, 302)
        cards = (load_site().get("cmsMenu") or {}).get("cards") or {}
        self.assertNotEqual(cards.get("journal.seo"), "not-a-menu")
        journal = self.client.get("/journal").get_data(as_text=True)
        self.assertIn(SEO_CARD, journal)
        story = self.client.get("/story").get_data(as_text=True)
        self.assertNotIn(SEO_CARD, story)

    def test_saving_the_page_menu_keeps_card_homes(self):
        self._set_cards({"journal.seo": "story"})
        response = self.client.post("/cms-menu/save", data={
            "parent_story": "people",
        })
        self.assertEqual(response.status_code, 302)
        menu = load_site().get("cmsMenu") or {}
        self.assertEqual((menu.get("cards") or {}).get("journal.seo"), "story")
        self.assertEqual((menu.get("parents") or {}).get("story"), "people")

    def test_layout_injects_show_under_on_collapsed_cards(self):
        html = self.client.get("/journal").get_data(as_text=True)
        self.assertIn("Show under", html)
        self.assertIn("card-home", html)
        self.assertIn("/cms-menu/cards/save", html)


if __name__ == "__main__":
    unittest.main()
