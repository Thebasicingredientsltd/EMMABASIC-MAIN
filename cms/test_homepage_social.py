"""Homepage grit social section is CMS-editable and wired into the live page.

Run with:  python test_homepage_social.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
HOMEPAGE_HTML = os.path.join(PROJECT, "Emma Basic Homepage.html")
APP_JSX = os.path.join(PROJECT, "components", "App.jsx")
SOCIAL_JSX = os.path.join(PROJECT, "components", "SocialFeed.jsx")


class HomepageSocialTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_crm_homepage_has_social_media_fields(self):
        response = self.client.get("/homepage")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Social media", html)
        self.assertIn("social_linkedin_href", html)
        self.assertIn("social_instagram_href", html)
        self.assertIn("social_linkedin_posts", html)

    def test_save_persists_social_urls_then_restores(self):
        original = load_data("homepage")
        marker = "https://www.linkedin.com/company/crm-social-test"
        try:
            payload = _form_from_homepage(original)
            payload["social_linkedin_href"] = marker
            payload["social_linkedin_posts"] = (
                "https://www.linkedin.com/feed/update/urn:li:activity:1234567890\n"
                "https://www.linkedin.com/posts/example-activity-9876543210-AbCd"
            )
            payload["social_instagram_href"] = "https://www.instagram.com/emmabasic.london/"
            payload["social_visible"] = "on"
            payload["social_instagram_enabled"] = "on"
            payload["social_linkedin_enabled"] = "on"
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("homepage")
            social = saved.get("social") or {}
            linkedin = social.get("linkedin") or {}
            self.assertEqual(linkedin.get("href"), marker)
            self.assertEqual(len(linkedin.get("posts") or []), 2)
            self.assertTrue(social.get("visible"))
            self.assertEqual(
                (saved.get("hero") or {}).get("headlineLine1"),
                (original.get("hero") or {}).get("headlineLine1"),
            )
        finally:
            with app.app_context():
                save_data("homepage", original)

    def test_site_loads_social_feed_after_grit(self):
        with open(HOMEPAGE_HTML, encoding="utf-8") as f:
            html = f.read()
        with open(APP_JSX, encoding="utf-8") as f:
            app_src = f.read()
        with open(SOCIAL_JSX, encoding="utf-8") as f:
            social_src = f.read()
        self.assertIn("SocialFeed.jsx", html)
        self.assertIn("<SocialFeed", app_src)
        self.assertIn("LifestyleGrid", app_src)
        grit_at = app_src.find("<LifestyleGrid")
        social_at = app_src.find("<SocialFeed")
        self.assertGreater(grit_at, 0)
        self.assertGreater(social_at, grit_at)
        self.assertIn("instagram.com", social_src)
        self.assertIn("linkedin.com/embed", social_src)
        self.assertIn("eb-social-carousel", social_src)
        self.assertIn("is-pair", social_src)
        self.assertIn("prefers-reduced-motion", social_src)
        self.assertNotIn("scrap", social_src.lower())


def _form_from_homepage(data):
    hero = data.get("hero") or {}
    buttons = hero.get("buttons") or []
    banner = data.get("banner") or {}
    founder = data.get("founder") or {}
    shelf = data.get("shelfTest") or {}
    lifestyle = data.get("lifestyle") or {}
    social = data.get("social") or {}
    ig = social.get("instagram") or {}
    li = social.get("linkedin") or {}
    fb = social.get("facebook") or {}
    x = social.get("x") or {}
    payload = {
        "hero_image": hero.get("image", ""),
        "hero_headlineLine1": hero.get("headlineLine1", ""),
        "hero_headlineLine2": hero.get("headlineLine2", ""),
        "hero_body": hero.get("body", ""),
        "hero_btn1_label": buttons[0]["label"] if buttons else "",
        "hero_btn1_href": buttons[0]["href"] if buttons else "",
        "hero_btn2_label": buttons[1]["label"] if len(buttons) > 1 else "",
        "hero_btn2_href": buttons[1]["href"] if len(buttons) > 1 else "",
        "banner_text": banner.get("text", ""),
        "banner_tag": banner.get("tag", ""),
        "founder_image": founder.get("image", ""),
        "founder_introLine": founder.get("introLine", ""),
        "founder_paragraphs": "\n\n".join(founder.get("paragraphs") or []),
        "shelf_headingLine1": shelf.get("headingLine1", ""),
        "shelf_headingLine2": shelf.get("headingLine2", ""),
        "shelf_subtitle": shelf.get("subtitle", ""),
        "shelf_theirs": "\n".join(shelf.get("theirs") or []),
        "shelf_ours": "\n".join(shelf.get("ours") or []),
        "shelf_closingLine1": shelf.get("closingLine1", ""),
        "shelf_closingLine2": shelf.get("closingLine2", ""),
        "life_headingLine1": lifestyle.get("headingLine1", ""),
        "life_headingLine2": lifestyle.get("headingLine2", ""),
        "life_handle": lifestyle.get("handle", ""),
        "life_followHref": lifestyle.get("followHref", ""),
        "tile_count": "0",
        "social_eyebrow": social.get("eyebrow", ""),
        "social_headingLine1": social.get("headingLine1", ""),
        "social_headingLine2": social.get("headingLine2", ""),
        "social_intro": social.get("intro", ""),
        "social_instagram_handle": ig.get("handle", ""),
        "social_instagram_href": ig.get("href", ""),
        "social_linkedin_href": li.get("href", ""),
        "social_linkedin_posts": "\n".join(li.get("posts") or []),
        "social_facebook_href": fb.get("href", ""),
        "social_x_href": x.get("href", ""),
    }
    if hero.get("visible") is not False:
        payload["hero_visible"] = "on"
    if social.get("visible", True) is not False:
        payload["social_visible"] = "on"
    if ig.get("enabled", True) is not False:
        payload["social_instagram_enabled"] = "on"
    if li.get("enabled", True) is not False:
        payload["social_linkedin_enabled"] = "on"
    if fb.get("enabled") is True:
        payload["social_facebook_enabled"] = "on"
    if x.get("enabled") is True:
        payload["social_x_enabled"] = "on"
    return payload


if __name__ == "__main__":
    unittest.main()
