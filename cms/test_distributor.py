"""Become a Distributor follows the How to Place Your First Order sheet.

Run with:  python test_distributor.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")


class DistributorPageTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_distributor_page_is_in_the_sidebar_and_has_a_save_form(self):
        response = self.client.get("/distributor")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/distributor", html)
        self.assertIn("Become a Distributor", html)
        self.assertIn("/distributor/save", html)
        self.assertIn("How to Place Your First Order", html)
        self.assertIn("Open a Trade Account", html)
        self.assertIn("Other Ways to Receive Your Order", html)
        self.assertIn('name="banner_title"', html)
        self.assertIn('name="hero_visible"', html)
        self.assertIn("Show this page header on the live site", html)
        self.assertIn("Show footer on this page", html)

    def test_dashboard_links_to_distributor(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/distributor", html)
        self.assertIn("Become a Distributor", html)

    def test_save_updates_banner_and_leaves_people_contact_alone(self):
        original = load_data("people")
        marker = "CRM-DISTRIBUTOR-TEST-TITLE"
        try:
            payload = _form_from_distributor(original)
            payload["banner_title"] = marker
            payload["banner_email"] = "test-order@example.com"
            response = self.client.post("/distributor/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("people")
            self.assertEqual(saved["distributor"]["title"], marker)
            self.assertEqual(saved["distributor"]["email"], "test-order@example.com")
            self.assertEqual(
                saved["contact"]["email"],
                (original.get("contact") or {}).get("email"),
            )
            self.assertEqual(
                saved["trade"]["heading"],
                (original.get("trade") or {}).get("heading"),
            )
        finally:
            with app.app_context():
                save_data("people", original)

    def test_uncheck_banner_and_step_stay_off(self):
        original = load_data("people")
        try:
            payload = _form_from_distributor(original)
            payload.pop("hero_visible", None)
            payload.pop("step0_visible", None)
            payload.pop("other_visible", None)
            response = self.client.post("/distributor/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("people")
            self.assertIs(saved["distributor"]["visible"], False)
            steps = saved["distributor"].get("steps") or []
            self.assertTrue(steps)
            self.assertIs(steps[0].get("visible"), False)
            self.assertIs(saved["distributor"]["otherWays"]["visible"], False)
            html = self.client.get("/distributor").get_data(as_text=True)
            self.assertNotIn('name="hero_visible" value="on" style="width:auto;" checked', html)
        finally:
            with app.app_context():
                save_data("people", original)

    def test_live_page_uses_how_to_order_sheet(self):
        path = os.path.join(PROJECT, "Become a Distributor.html")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("HowToOrder", src)
        self.assertIn("EB_PEOPLE.distributor", src)
        self.assertNotIn("<OrderSection", src)


def _form_from_distributor(data):
    dist = data.get("distributor") or {}
    steps = dist.get("steps") or []
    other = dist.get("otherWays") or {}
    collect = other.get("collect") or {}
    own = other.get("ownDistributor") or {}
    sheet = dist.get("sheetFooter") or {}
    payload = {
        "banner_title": dist.get("title", ""),
        "banner_email": dist.get("email", ""),
        "step_count": str(len(steps)),
        "other_heading": other.get("heading", ""),
        "collect_title": collect.get("title", ""),
        "collect_lines": "\n".join(collect.get("lines") or []),
        "own_title": own.get("title", ""),
        "own_lines": "\n".join(own.get("lines") or []),
        "sheet_footer_text": sheet.get("text", ""),
    }
    if dist.get("visible") is not False:
        payload["hero_visible"] = "on"
    if (data.get("distributorFooter") or {}).get("visible") is not False:
        payload["footer_visible"] = "on"
    if other.get("visible") is not False:
        payload["other_visible"] = "on"
    if sheet.get("visible") is not False:
        payload["sheet_footer_visible"] = "on"
    for i, step in enumerate(steps):
        payload["step%d_icon" % i] = step.get("icon", "")
        payload["step%d_number" % i] = step.get("number", "")
        payload["step%d_title" % i] = step.get("title", "")
        payload["step%d_bullets" % i] = "\n".join(step.get("bullets") or [])
        if step.get("visible") is not False:
            payload["step%d_visible" % i] = "on"
    return payload


if __name__ == "__main__":
    unittest.main()
