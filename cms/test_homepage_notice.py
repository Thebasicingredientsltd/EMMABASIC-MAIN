"""Homepage customer notice: CRM fields, PDF upload, and the live page.

Run with:  python test_homepage_notice.py
"""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, save_data  # noqa: E402
from test_homepage_social import _form_from_homepage  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
HOMEPAGE_HTML = os.path.join(PROJECT, "Emma Basic Homepage.html")
APP_JSX = os.path.join(PROJECT, "components", "App.jsx")
NOTICE_JSX = os.path.join(PROJECT, "components", "CustomerNotice.jsx")
SEEDED_PDF = os.path.join(
    PROJECT, "assets", "notices", "Emma-Basic-Japanese-Style-Curry-FSA-AA-49-2026.pdf"
)


class HomepageNoticeTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.original = load_data("homepage")

    def tearDown(self):
        with app.app_context():
            save_data("homepage", self.original)

    def test_crm_homepage_has_notice_fields(self):
        response = self.client.get("/homepage")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Customer notice", html)
        self.assertIn("notice_title", html)
        self.assertIn("notice_file", html)
        self.assertIn("Emma Basic Japanese Style Curry", html)
        self.assertIn('name="notice_present"', html)

    def test_save_persists_notice_and_can_hide_it(self):
        payload = _form_from_homepage(self.original)
        payload.update({
            "notice_present": "1",
            "notice_eyebrow": "A note",
            "notice_title": "Kitchen closed Friday",
            "notice_body": "Orders placed Friday ship on Monday.",
            "notice_link_label": "Read more",
            "notice_href": "https://emmabasic.co.uk/notes",
        })
        payload.pop("notice_visible", None)
        response = self.client.post("/homepage/save", data=payload)
        self.assertEqual(response.status_code, 302)
        saved = load_data("homepage")
        notice = saved.get("notice") or {}
        self.assertEqual(notice.get("title"), "Kitchen closed Friday")
        self.assertEqual(notice.get("eyebrow"), "A note")
        self.assertEqual(notice.get("href"), "https://emmabasic.co.uk/notes")
        self.assertFalse(notice.get("visible"))
        self.assertEqual(
            (saved.get("hero") or {}).get("headlineLine1"),
            (self.original.get("hero") or {}).get("headlineLine1"),
        )

    def test_save_without_notice_card_leaves_it(self):
        payload = _form_from_homepage(self.original)
        payload.pop("notice_present", None)
        payload["notice_title"] = "Should not stick"
        response = self.client.post("/homepage/save", data=payload)
        self.assertEqual(response.status_code, 302)
        saved = load_data("homepage")
        self.assertEqual(
            (saved.get("notice") or {}).get("title"),
            (self.original.get("notice") or {}).get("title"),
        )

    def test_javascript_link_is_dropped(self):
        payload = _form_from_homepage(self.original)
        payload.update({
            "notice_present": "1",
            "notice_visible": "on",
            "notice_title": (self.original.get("notice") or {}).get("title", ""),
            "notice_body": (self.original.get("notice") or {}).get("body", ""),
            "notice_eyebrow": (self.original.get("notice") or {}).get("eyebrow", ""),
            "notice_link_label": "Read the full notice",
            "notice_href": "javascript:alert(1)",
        })
        response = self.client.post("/homepage/save", data=payload)
        self.assertEqual(response.status_code, 302)
        saved = load_data("homepage")
        self.assertEqual((saved.get("notice") or {}).get("href"), "")

    def test_pdf_upload_replaces_the_link(self):
        payload = _form_from_homepage(self.original)
        payload.update({
            "notice_present": "1",
            "notice_visible": "on",
            "notice_eyebrow": "Product recall",
            "notice_title": "Uploaded notice",
            "notice_body": "See the attached PDF.",
            "notice_link_label": "Read the full notice",
            "notice_href": "https://example.com/old.pdf",
            "notice_file": (io.BytesIO(b"%PDF-1.4\n% notice\n"), "curry-recall.pdf"),
        })
        uploaded = None
        try:
            response = self.client.post("/homepage/save", data=payload)
            self.assertEqual(response.status_code, 302)
            saved = load_data("homepage")
            href = (saved.get("notice") or {}).get("href") or ""
            self.assertTrue(href.startswith("assets/notices/"))
            self.assertTrue(href.endswith(".pdf"))
            uploaded = os.path.join(PROJECT, href)
            self.assertTrue(os.path.isfile(uploaded))
            with open(uploaded, "rb") as handle:
                self.assertTrue(handle.read(5).startswith(b"%PDF"))
        finally:
            if uploaded and os.path.isfile(uploaded):
                os.remove(uploaded)

    def test_non_pdf_upload_keeps_the_previous_file(self):
        payload = _form_from_homepage(self.original)
        previous = (self.original.get("notice") or {}).get("href", "")
        payload.update({
            "notice_present": "1",
            "notice_visible": "on",
            "notice_title": "Still the curry recall",
            "notice_href": previous,
            "notice_file": (io.BytesIO(b"not a pdf"), "notes.pdf"),
        })
        response = self.client.post("/homepage/save", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("That file is not a PDF.", page)
        saved = load_data("homepage")
        self.assertEqual((saved.get("notice") or {}).get("href"), previous)
        self.assertEqual((saved.get("notice") or {}).get("title"), "Still the curry recall")

    def test_homepage_renders_notice_before_the_hero(self):
        with open(HOMEPAGE_HTML, encoding="utf-8") as handle:
            html = handle.read()
        with open(APP_JSX, encoding="utf-8") as handle:
            app_src = handle.read()
        with open(NOTICE_JSX, encoding="utf-8") as handle:
            notice_src = handle.read()
        self.assertIn("CustomerNotice.jsx", html)
        self.assertLess(html.find("CustomerNotice.jsx"), html.find("App.jsx"))
        self.assertLess(app_src.find("<CustomerNotice"), app_src.find("<Hero"))
        self.assertIn('role="region"', notice_src)
        self.assertIn("visible === false", notice_src)
        self.assertIn("assets/notices/", (self.original.get("notice") or {}).get("href", ""))
        self.assertTrue((self.original.get("notice") or {}).get("visible"))
        with open(SEEDED_PDF, "rb") as handle:
            self.assertTrue(handle.read(5).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
