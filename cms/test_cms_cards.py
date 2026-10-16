"""Editor cards can sit on a different CRM page than the one they belong to.

Each collapsed card has a Show under control (same idea as the CMS menu).
By default a card stays on its own page. After you pick another menu, it
renders on that page's editor — still saving through its original form.

Run with:  python test_cms_cards.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_site, save_data  # noqa: E402

SEO_CARD = 'data-cms-card="journal.seo"'


def _content_card_ids(html):
    chunk = html.split('<div class="content-inner">', 1)[-1]
    return re.findall(r'\sdata-cms-card="([^"]+)"', chunk)


class CmsCardHomeTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.original_site = load_site()
        data = dict(self.original_site)
        menu = dict(data.get("cmsMenu") or {})
        menu.pop("cards", None)
        menu.pop("cardOrder", None)
        if menu:
            data["cmsMenu"] = menu
        else:
            data.pop("cmsMenu", None)
        with app.app_context():
            save_data("site", data)

    def tearDown(self):
        with app.app_context():
            save_data("site", self.original_site)

    def _set_menu(self, **parts):
        with app.app_context():
            data = dict(load_site())
            menu = dict(data.get("cmsMenu") or {})
            menu.update(parts)
            data["cmsMenu"] = menu
            save_data("site", data)

    def _set_cards(self, cards):
        self._set_menu(cards=cards)

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

    def test_collapsed_cards_show_a_drag_handle(self):
        html = self.client.get("/story").get_data(as_text=True)
        self.assertIn("/cms-menu/cards/order", html)
        self.assertIn("eb-drag-handle", html)
        self.assertIn("Drag the", html)
        self.assertIn('handle.className = "eb-drag-handle"', html)

    def test_post_saves_card_order_for_the_page(self):
        order = ["journal.posts", "journal.header", "journal.footer", "journal.seo"]
        response = self.client.post(
            "/cms-menu/cards/order",
            json={"page": "journal", "order": order + ["not-a-card"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        saved = ((load_site().get("cmsMenu") or {}).get("cardOrder") or {})
        self.assertEqual(saved.get("journal"), order)
        self.assertNotIn("not-a-card", saved.get("journal") or [])

    def test_saved_order_applies_on_reload(self):
        order = ["journal.posts", "journal.header", "journal.footer", "journal.seo"]
        self._set_menu(cardOrder={"journal": order})
        ids = _content_card_ids(self.client.get("/journal").get_data(as_text=True))
        self.assertEqual(ids[:4], order)
        self.assertLess(ids.index("journal.posts"), ids.index("journal.header"))

    def test_moved_card_appends_at_end_unless_ordered(self):
        self._set_cards({"journal.seo": "story"})
        story_ids = _content_card_ids(self.client.get("/story").get_data(as_text=True))
        self.assertEqual(story_ids[-1], "journal.seo")
        self.assertNotIn("journal.seo", _content_card_ids(
            self.client.get("/journal").get_data(as_text=True)
        ))

        self._set_menu(
            cards={"journal.seo": "story"},
            cardOrder={"story": ["journal.seo"]},
        )
        ordered = _content_card_ids(self.client.get("/story").get_data(as_text=True))
        self.assertEqual(ordered[0], "journal.seo")

    def test_saving_card_home_keeps_card_order(self):
        self._set_menu(cardOrder={"journal": ["journal.posts", "journal.header"]})
        response = self.client.post("/cms-menu/cards/save", data={
            "card": "journal.seo",
            "parent": "story",
        })
        self.assertEqual(response.status_code, 302)
        menu = load_site().get("cmsMenu") or {}
        self.assertEqual((menu.get("cardOrder") or {}).get("journal"), [
            "journal.posts", "journal.header",
        ])
        self.assertEqual((menu.get("cards") or {}).get("journal.seo"), "story")

    def test_saving_the_page_menu_keeps_card_order(self):
        self._set_menu(
            cards={"journal.seo": "story"},
            cardOrder={"journal": ["journal.posts"]},
        )
        response = self.client.post("/cms-menu/save", data={
            "parent_story": "people",
        })
        self.assertEqual(response.status_code, 302)
        menu = load_site().get("cmsMenu") or {}
        self.assertEqual((menu.get("cardOrder") or {}).get("journal"), ["journal.posts"])
        self.assertEqual((menu.get("cards") or {}).get("journal.seo"), "story")
        self.assertEqual((menu.get("parents") or {}).get("story"), "people")


if __name__ == "__main__":
    unittest.main()
