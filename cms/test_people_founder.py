"""People page founder photo/letter must be editable in the CRM.

Run with:  python test_people_founder.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
PEOPLE_HTML = os.path.join(PROJECT, "People & Places.html")


class PeopleFounderEditorTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_crm_people_page_has_founder_fields(self):
        response = self.client.get("/people")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Founder photo", html)
        self.assertIn("founder_image", html)
        self.assertIn("founder_introLine", html)
        self.assertIn("founder_paragraphs", html)
        self.assertIn("founder_image_file", html)
        self.assertIn("A small operation", html)
        self.assertIn("hero_title", html)
        self.assertIn("First line", html)
        self.assertIn("Page header", html)

    def test_save_updates_founder_copy_then_restores(self):
        original = load_data("people")
        marker = "CRM-PEOPLE-FOUNDER-TEST-INTRO"
        members_before = [m["name"] for m in (original.get("team") or {}).get("members") or []]
        try:
            payload = _form_from_people(original)
            payload["founder_introLine"] = marker
            response = self.client.post("/people/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("people")
            founder = saved.get("founder") or {}
            self.assertEqual(founder.get("introLine"), marker)
            self.assertEqual(
                founder.get("image"),
                (original.get("founder") or {}).get("image"),
            )
            self.assertEqual(
                [m["name"] for m in (saved.get("team") or {}).get("members") or []],
                members_before,
            )
        finally:
            with app.app_context():
                save_data("people", original)

    def test_people_page_reads_founder_from_people_data(self):
        with open(PEOPLE_HTML, encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("EB_PEOPLE.founder", html)
        self.assertIn("introLine={founder.introLine}", html)
        self.assertIn("paragraphs={founder.paragraphs}", html)
        self.assertIn("image={founder.image", html)
        self.assertNotIn('image="assets/homepage/founder-mum-daughter.jpg"', html)


def _on(payload, name, section):
    if (section or {}).get("visible", True) is not False:
        payload[name] = "on"


def _form_from_people(data):
    hero = data.get("hero") or {}
    founder = data.get("founder") or {}
    team = data.get("team") or {}
    members = team.get("members") or []
    intro = data.get("intro") or {}
    services = data.get("services") or {}
    cards = services.get("cards") or []
    contact = data.get("contact") or {}
    payload = {
        "hero_eyebrow": hero.get("eyebrow", ""),
        "hero_title": hero.get("title", ""),
        "hero_titleItalic": hero.get("titleItalic", ""),
        "hero_subtitle": hero.get("subtitle", ""),
        "founder_image": founder.get("image", ""),
        "founder_introLine": founder.get("introLine", ""),
        "founder_paragraphs": "\n\n".join(founder.get("paragraphs") or []),
        "team_headingLine1": team.get("headingLine1", ""),
        "team_headingLine2": team.get("headingLine2", ""),
        "team_intro": team.get("intro", ""),
        "member_count": str(len(members)),
        "intro_heading": intro.get("heading", ""),
        "intro_headingAccent": intro.get("headingAccent", ""),
        "intro_paragraphs": "\n\n".join(intro.get("paragraphs") or []),
        "services_eyebrow": services.get("eyebrow", ""),
        "services_heading": services.get("heading", ""),
        "services_closing": services.get("closing", ""),
        "card_count": str(len(cards)),
        "contact_headingLine1": contact.get("headingLine1", ""),
        "contact_headingLine2": contact.get("headingLine2", ""),
        "contact_body": contact.get("body", ""),
        "contact_regionLabel": contact.get("regionLabel", ""),
        "contact_email": contact.get("email", ""),
        "contact_addressLine1": contact.get("addressLine1", ""),
        "contact_addressLine2": contact.get("addressLine2", ""),
        "contact_note": contact.get("note", ""),
    }
    _on(payload, "hero_visible", hero)
    _on(payload, "founder_visible", founder)
    _on(payload, "team_visible", team)
    _on(payload, "intro_visible", intro)
    _on(payload, "services_visible", services)
    _on(payload, "contact_visible", contact)
    for i, member in enumerate(members):
        payload["member%d_name" % i] = member.get("name", "")
        payload["member%d_role" % i] = member.get("role", "")
        payload["member%d_bio" % i] = member.get("bio", "")
        payload["member%d_tone" % i] = member.get("tone", "warm")
        payload["member%d_image" % i] = member.get("image", "")
        payload["member%d_image2" % i] = member.get("image2", "")
        payload["member%d_phone" % i] = member.get("phone", "")
        payload["member%d_email" % i] = member.get("email", "")
        payload["member%d_imagePosition" % i] = member.get("imagePosition", "")
        zoom = member.get("imageZoom")
        payload["member%d_imageZoom" % i] = "" if zoom is None else str(zoom)
    for i, card in enumerate(cards):
        payload["card%d_title" % i] = card.get("title", "")
        payload["card%d_body" % i] = card.get("body", "")
    return payload


if __name__ == "__main__":
    unittest.main()
