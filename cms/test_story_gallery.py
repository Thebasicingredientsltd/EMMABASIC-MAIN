"""Our Story CMS page must let you edit the 'in the wild' photo gallery.

The live gallery at the bottom of Our Story used to be a hardcoded list in
the HTML, so the CRM had nowhere to add, replace, or remove those photos.

Run with:  python test_story_gallery.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402

STORY_HTML = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Emma-Basic-The-Basic-Ingredients",
    "project",
    "Our Story.html",
)


def _hero_payload(data):
    hero = data.get("hero") or {}
    gallery = data.get("gallery") or {}
    payload = {
        "hero_eyebrow": hero.get("eyebrow", ""),
        "hero_title": hero.get("title", ""),
        "hero_titleItalic": hero.get("titleItalic", ""),
        "hero_subtitle": hero.get("subtitle", ""),
        "gallery_heading": gallery.get("heading", ""),
        "gallery_headingItalic": gallery.get("headingItalic", ""),
        "gallery_photos_editor": "1",
    }
    if hero.get("visible", True) is not False:
        payload["hero_visible"] = "on"
    if (data.get("footer") or {}).get("visible", True) is not False:
        payload["footer_visible"] = "on"
    return payload


class StoryGalleryTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.original = load_data("story")

    def tearDown(self):
        with app.app_context():
            save_data("story", self.original)

    def test_story_cms_shows_in_the_wild_photo_editor(self):
        data = load_data("story")
        gallery = data.setdefault("gallery", {})
        gallery["photos"] = [
            "assets/team-photos/CD04.jpg",
            "assets/team-photos/DSC01812.jpg",
        ]
        with app.app_context():
            save_data("story", data)

        html = self.client.get("/story").get_data(as_text=True)
        self.assertIn("Photos — in the wild", html)
        self.assertIn('name="gallery_path"', html)
        self.assertIn("assets/team-photos/CD04.jpg", html)
        self.assertIn("assets/team-photos/DSC01812.jpg", html)
        self.assertIn("+ Add image", html)

    def test_story_save_replaces_gallery_photos(self):
        data = load_data("story")
        payload = _hero_payload(data)
        payload["gallery_path"] = [
            "assets/team-photos/DSC02366.jpg",
            "assets/uploads/new-wild.jpg",
        ]
        response = self.client.post("/story/save", data=payload)
        self.assertEqual(response.status_code, 302)
        saved = (load_data("story").get("gallery") or {}).get("photos")
        self.assertEqual(saved, [
            "assets/team-photos/DSC02366.jpg",
            "assets/uploads/new-wild.jpg",
        ])

    def test_story_save_without_editor_marker_leaves_photos_alone(self):
        data = load_data("story")
        gallery = data.setdefault("gallery", {})
        gallery["photos"] = ["assets/team-photos/CD04.jpg"]
        with app.app_context():
            save_data("story", data)

        payload = _hero_payload(data)
        payload.pop("gallery_photos_editor")
        payload.pop("gallery_path", None)
        response = self.client.post("/story/save", data=payload)
        self.assertEqual(response.status_code, 302)
        saved = (load_data("story").get("gallery") or {}).get("photos")
        self.assertEqual(saved, ["assets/team-photos/CD04.jpg"])

    def test_our_story_page_reads_gallery_photos_from_cms(self):
        with open(STORY_HTML, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("gallery.photos", source)
        self.assertIn('data-cms-key="story"', source)
        self.assertIn("gallery.photos[", source)
