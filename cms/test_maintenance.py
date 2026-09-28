"""The under-construction switch: gate injection, the CRM screen, and the
guarantee that the website stays up unless it is deliberately taken down.

Run with:  python test_maintenance.py
"""

import html
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import maintenance  # noqa: E402
from app import PROJECT_DIR, app, load_data, load_site, save_data  # noqa: E402
from visual import draft_site_page, rewrite_preview_html  # noqa: E402

PUBLIC_PAGES = [
    "Emma Basic Homepage.html",
    "Our Products.html",
    "Journal.html",
    "journal-post.html",
    "Our Story.html",
    "People & Places.html",
    "Places.html",
    "Become a Distributor.html",
    "The Basic Ingredients.html",
    "Matcha Lab.html",
    "product.html",
    "index.html",
    "instagram.html",
]


def read_page(name):
    with open(os.path.join(PROJECT_DIR, name), "r", encoding="utf-8") as fh:
        return fh.read()


class SettingsTests(unittest.TestCase):
    def test_only_an_explicit_true_hides_the_site(self):
        # A missing, stale or malformed data file must never take the site down.
        for payload in (None, {}, {"enabled": False}, {"enabled": "yes"},
                        {"enabled": 1}, {"enabled": None}, "nonsense"):
            self.assertFalse(maintenance.normalize(payload)["enabled"], payload)
        self.assertTrue(maintenance.normalize({"enabled": True})["enabled"])

    def test_from_data_falls_back_to_defaults(self):
        self.assertFalse(maintenance.is_enabled({}))
        self.assertFalse(maintenance.is_enabled(None))
        self.assertEqual(
            maintenance.from_data({})["heading"], maintenance.DEFAULTS["heading"]
        )

    def test_stored_copy_wins_over_defaults(self):
        settings = maintenance.from_data({"maintenance": {"heading": "Back soon"}})
        self.assertEqual(settings["heading"], "Back soon")
        # Untouched fields keep their default rather than going blank.
        self.assertEqual(settings["eyebrow"], maintenance.DEFAULTS["eyebrow"])

    def test_preview_keys_are_random(self):
        keys = {maintenance.new_preview_key() for _ in range(20)}
        self.assertEqual(len(keys), 20)


class GateInjectionTests(unittest.TestCase):
    def test_gate_lands_in_the_head_before_the_content(self):
        page = '<!doctype html>\n<html>\n<head>\n<meta charset="utf-8"/>\n' \
               '<title>x</title>\n</head>\n<body></body>\n</html>'
        gated = maintenance.ensure_gate(page)
        self.assertIn('<script src="data/site.js"></script>', gated)
        self.assertIn("components/maintenance.js", gated)
        self.assertLess(gated.index("maintenance.js"), gated.index("<title>"))

    def test_gate_precedes_a_meta_refresh(self):
        # index.html bounces to the homepage; the gate has to win that race.
        page = '<head><meta charset="utf-8"/>' \
               '<meta http-equiv="refresh" content="0; url=Home.html"/></head>'
        gated = maintenance.ensure_gate(page)
        self.assertLess(gated.index("maintenance.js"), gated.index("http-equiv"))

    def test_injection_is_idempotent(self):
        once = maintenance.ensure_gate("<head><meta charset=\"utf-8\"/></head>")
        self.assertEqual(maintenance.ensure_gate(once), once)
        self.assertEqual(once.count(maintenance.GATE_START), 1)

    def test_gate_survives_a_page_with_no_charset(self):
        gated = maintenance.ensure_gate("<html><head><title>x</title></head></html>")
        self.assertIn("maintenance.js", gated)

    def test_strip_gate_is_the_inverse(self):
        page = '<head><meta charset="utf-8"/><title>x</title></head>'
        self.assertEqual(
            maintenance.strip_gate(maintenance.ensure_gate(page)).replace("\n", ""),
            page,
        )

    def test_apply_to_html_leaves_the_holding_page_ungated(self):
        page = '<head><meta charset="utf-8"/></head>'
        result = maintenance.apply_to_html(page, maintenance.PAGE_FILE, "site", {})
        self.assertNotIn("components/maintenance.js", result)

    def test_apply_to_html_gates_every_other_page(self):
        page = '<head><meta charset="utf-8"/></head>'
        result = maintenance.apply_to_html(page, "Journal.html", "journal", {})
        self.assertIn("components/maintenance.js", result)


class ShippedFileTests(unittest.TestCase):
    """The gate only works if it is actually present on the pages."""

    def test_every_public_page_carries_the_gate(self):
        for name in PUBLIC_PAGES:
            page = read_page(name)
            self.assertIn(maintenance.GATE_START, page, name)
            self.assertIn('src="data/site.js', page, name)
            self.assertIn("components/maintenance.js", page, name)

    def test_the_gate_runs_before_any_other_script(self):
        for name in PUBLIC_PAGES:
            page = read_page(name)
            first = page.index("components/maintenance.js")
            for other in ("react.development.js", "babel.min.js", 'id="root"'):
                if other in page:
                    self.assertLess(first, page.index(other), "%s / %s" % (name, other))

    def test_the_holding_page_is_not_gated(self):
        page = read_page(maintenance.PAGE_FILE)
        self.assertNotIn(maintenance.GATE_START, page)
        self.assertNotIn('src="components/maintenance.js', page)
        # It still needs the settings so it can bounce back once the site is up.
        self.assertIn('src="data/site.js', page)
        self.assertIn(maintenance.NOTICE_START, page)

    def test_holding_page_is_kept_out_of_search_results(self):
        self.assertIn('name="robots"', read_page(maintenance.PAGE_FILE))

    def test_new_pages_are_gated_from_the_start(self):
        drafted = draft_site_page("Test Page", "Heading", "Body", {"right": []}, set())
        self.assertIn("components/maintenance.js", drafted["html"])

    def test_gate_script_fails_open(self):
        with open(os.path.join(PROJECT_DIR, "components", "maintenance.js"),
                  "r", encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("settings.enabled !== true", source)
        self.assertIn(maintenance.PAGE_FILE, source)


class NoticeTests(unittest.TestCase):
    def test_notice_renders_the_stored_copy(self):
        block = maintenance.render_notice(maintenance.normalize({
            "eyebrow": "Emma Basic",
            "heading": "Under construction",
            "headingItalic": "back shortly.",
            "body": "We are updating the site.",
            "note": "Still on the shelves.",
            "email": "hello@example.com",
        }))
        for text in ("Emma Basic", "Under construction", "back shortly.",
                     "We are updating the site.", "Still on the shelves."):
            self.assertIn(text, block)
        self.assertIn('href="mailto:hello@example.com"', block)

    def test_blank_fields_are_dropped_rather_than_left_empty(self):
        block = maintenance.render_notice(maintenance.normalize({
            "eyebrow": "", "heading": "Back soon", "headingItalic": "",
            "body": "", "note": "", "email": "",
        }))
        self.assertIn("Back soon", block)
        self.assertNotIn("uc-eyebrow", block)
        self.assertNotIn("mailto:", block)
        self.assertNotIn("uc-body", block)

    def test_copy_is_escaped(self):
        block = maintenance.render_notice(maintenance.normalize(
            {"heading": '<script>alert("x")</script>'}
        ))
        self.assertNotIn("<script>", block)
        self.assertIn("&lt;script&gt;", block)

    def test_apply_notice_replaces_only_the_marked_block(self):
        page = "<body>before\n%s\nold\n%s\nafter</body>" % (
            maintenance.NOTICE_START, maintenance.NOTICE_END,
        )
        result = maintenance.apply_notice(page, maintenance.normalize({"heading": "New"}))
        self.assertIn("before", result)
        self.assertIn("after", result)
        self.assertIn("New", result)
        self.assertNotIn("old", result)
        self.assertEqual(result.count(maintenance.NOTICE_START), 1)


class PreviewTests(unittest.TestCase):
    def test_the_visual_editor_preview_is_never_gated(self):
        # Editing a page while the site is hidden is the main reason to hide it.
        page = maintenance.ensure_gate(
            '<head><meta charset="utf-8"/></head><body></body>'
        )
        preview = rewrite_preview_html(page, "Journal.html")
        self.assertNotIn("maintenance.js", preview)
        self.assertNotIn(maintenance.GATE_START, preview)


class CmsScreenTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.original = load_site()

    def tearDown(self):
        with app.app_context():
            save_data("site", self.original)

    def payload(self, **overrides):
        data = {
            "eyebrow": "Emma Basic",
            "heading": "Under construction",
            "headingItalic": "back shortly.",
            "body": "We are updating the site.",
            "note": "",
            "email": "hello@example.com",
        }
        data.update(overrides)
        return data

    def test_screen_loads_and_is_linked_from_the_sidebar(self):
        response = self.client.get("/maintenance")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("/maintenance/save", body)
        self.assertIn("maintenance_enabled", body)

    def test_dashboard_links_to_the_screen(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("/maintenance", body)
        self.assertIn("Under construction", body)

    def test_saving_turns_the_site_off_and_back_on(self):
        response = self.client.post(
            "/maintenance/save", data=self.payload(maintenance_enabled="on")
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(maintenance.is_enabled(load_data("site")))

        # An unticked box is omitted from the POST — that has to mean "visible".
        response = self.client.post("/maintenance/save", data=self.payload())
        self.assertEqual(response.status_code, 302)
        self.assertFalse(maintenance.is_enabled(load_data("site")))

    def test_saving_stores_the_copy(self):
        self.client.post("/maintenance/save", data=self.payload(heading="Back Tuesday"))
        self.assertEqual(
            maintenance.from_data(load_data("site"))["heading"], "Back Tuesday"
        )

    def test_saving_writes_the_copy_into_the_holding_page(self):
        self.client.post("/maintenance/save", data=self.payload(heading="Back Tuesday"))
        self.assertIn("Back Tuesday", read_page(maintenance.PAGE_FILE))

    def test_a_preview_key_always_exists(self):
        self.client.post("/maintenance/save", data=self.payload())
        key = maintenance.from_data(load_data("site"))["previewKey"]
        self.assertTrue(key)

        body = self.client.get("/maintenance").get_data(as_text=True)
        self.assertIn("preview=" + key, body)

    def test_a_new_key_can_be_issued(self):
        self.client.post("/maintenance/save", data=self.payload())
        first = maintenance.from_data(load_data("site"))["previewKey"]
        payload = self.payload(new_preview_key="1")
        self.client.post("/maintenance/save", data=payload)
        second = maintenance.from_data(load_data("site"))["previewKey"]
        self.assertTrue(second)
        self.assertNotEqual(first, second)

    def test_issuing_a_new_key_keeps_the_site_hidden(self):
        self.client.post("/maintenance/save", data=self.payload(maintenance_enabled="on"))
        self.client.post(
            "/maintenance/save",
            data=self.payload(maintenance_enabled="on", new_preview_key="1"),
        )
        self.assertTrue(maintenance.is_enabled(load_data("site")))

    def test_every_page_warns_while_the_site_is_hidden(self):
        self.client.post("/maintenance/save", data=self.payload(maintenance_enabled="on"))
        for url in ("/", "/homepage", "/catalog", "/journal"):
            body = html.unescape(self.client.get(url).get_data(as_text=True))
            self.assertIn("The website is hidden from visitors.", body, url)
            self.assertIn("/maintenance/off", body, url)

    def test_no_warning_while_the_site_is_live(self):
        self.client.post("/maintenance/save", data=self.payload())
        body = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("The website is hidden from visitors.", body)

    def test_one_click_puts_the_site_back_up(self):
        self.client.post("/maintenance/save", data=self.payload(maintenance_enabled="on"))
        response = self.client.post("/maintenance/off")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(maintenance.is_enabled(load_data("site")))

    def test_turning_it_off_keeps_the_copy(self):
        self.client.post(
            "/maintenance/save",
            data=self.payload(maintenance_enabled="on", heading="Back Tuesday"),
        )
        self.client.post("/maintenance/off")
        settings = maintenance.from_data(load_data("site"))
        self.assertFalse(settings["enabled"])
        self.assertEqual(settings["heading"], "Back Tuesday")


if __name__ == "__main__":
    unittest.main()
