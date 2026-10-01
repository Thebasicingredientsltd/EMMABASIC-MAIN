"""Homepage hero buttons (FIND US / FOR SHOPKEEPERS) can be hidden in the CRM.

Run with:  python test_homepage_hero_buttons.py
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402
from test_homepage_social import _form_from_homepage  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
HERO_JSX = os.path.join(PROJECT, "components", "Hero.jsx")


def _checkbox(html, name):
    match = re.search(
        r'<input type="checkbox" name="%s"[^>]*>' % re.escape(name),
        html,
    )
    return match.group(0) if match else ""


def _buttons():
    return (load_data("homepage").get("hero") or {}).get("buttons") or []


class HeroButtonsTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_live_homepage_keeps_both_buttons_by_default(self):
        buttons = _buttons()
        self.assertEqual([b.get("label") for b in buttons[:2]], ["FIND US", "FOR SHOPKEEPERS"])
        self.assertFalse(any(b.get("hide") for b in buttons))

    def test_editor_shows_hide_boxes_unticked(self):
        html = self.client.get("/homepage").get_data(as_text=True)
        self.assertIn("Hero buttons", html)
        self.assertIn("Hide this button", html)
        self.assertIn("FIND US", html)
        self.assertIn("FOR SHOPKEEPERS", html)
        for name in ("hero_btn1_hide", "hero_btn2_hide"):
            box = _checkbox(html, name)
            self.assertTrue(box, name)
            self.assertNotIn("checked", box)

    def test_hide_persists_then_unticked_box_unhides(self):
        original = load_data("homepage")
        try:
            payload = _form_from_homepage(original)
            payload["hero_btn1_hide"] = "on"
            payload["hero_btn2_hide"] = "on"
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            buttons = _buttons()
            self.assertEqual(len(buttons), 2)
            self.assertTrue(all(b.get("hide") is True for b in buttons))
            self.assertEqual(buttons[0].get("label"), "FIND US")
            form = self.client.get("/homepage").get_data(as_text=True)
            self.assertIn("checked", _checkbox(form, "hero_btn1_hide"))
            self.assertIn("checked", _checkbox(form, "hero_btn2_hide"))

            # Saving again with the hide boxes still ticked keeps them hidden.
            response = self.client.post("/homepage/save", data=_form_from_homepage(load_data("homepage")))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(all(b.get("hide") is True for b in _buttons()))

            # Unticked boxes are omitted from POST and must un-hide.
            payload = _form_from_homepage(load_data("homepage"))
            payload.pop("hero_btn1_hide", None)
            payload.pop("hero_btn2_hide", None)
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            buttons = _buttons()
            self.assertTrue(all(b.get("hide") is False for b in buttons))
            self.assertEqual(buttons[1].get("label"), "FOR SHOPKEEPERS")
            form = self.client.get("/homepage").get_data(as_text=True)
            self.assertNotIn("checked", _checkbox(form, "hero_btn1_hide"))
        finally:
            with app.app_context():
                save_data("homepage", original)

    def test_clearing_both_labels_does_not_restore_old_buttons(self):
        original = load_data("homepage")
        try:
            payload = _form_from_homepage(original)
            for i in (1, 2):
                payload["hero_btn%d_label" % i] = ""
                payload["hero_btn%d_href" % i] = ""
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            self.assertEqual([b.get("label") for b in _buttons()], ["", ""])
        finally:
            with app.app_context():
                save_data("homepage", original)

    def test_live_hero_honours_hidden_and_empty(self):
        with open(HERO_JSX, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("b.hide !== true", source)
        self.assertIn("heroButtons.length > 0 &&", source)
        self.assertNotIn("Browse the Collection", source)
        self.assertIn('fontSize: "clamp(56px, 10vw, 160px)"', source)


if __name__ == "__main__":
    unittest.main()
