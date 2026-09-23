"""Visual CRM editor: JSON path patching, extra sections, and new pages.

Run with:  python test_visual.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module  # noqa: E402
import storage  # noqa: E402
from app import app  # noqa: E402
from visual import (  # noqa: E402
    add_custom_section,
    add_site_page,
    draft_site_page,
    get_path,
    parse_path,
    set_path,
    slugify,
)


class PathTests(unittest.TestCase):
    def test_parse_dotted_and_index_paths(self):
        self.assertEqual(parse_path("hero.title"), ["hero", "title"])
        self.assertEqual(
            parse_path("team.members[0].image"),
            ["team", "members", 0, "image"],
        )

    def test_set_path_updates_nested_value(self):
        data = {"hero": {"title": "Old"}, "team": {"members": [{"name": "Emma"}]}}
        set_path(data, "hero.title", "New")
        set_path(data, "team.members[0].name", "Emma Basic")
        self.assertEqual(get_path(data, "hero.title"), "New")
        self.assertEqual(get_path(data, "team.members[0].name"), "Emma Basic")

    def test_set_path_creates_missing_objects(self):
        data = {}
        set_path(data, "hero.subtitle", "Hello")
        self.assertEqual(data["hero"]["subtitle"], "Hello")


class SectionAndPageTests(unittest.TestCase):
    def test_add_custom_section_appends_visible_block(self):
        data = {"hero": {"title": "People"}}
        added = add_custom_section(data, heading="New block", body="Some copy")
        self.assertEqual(added["heading"], "New block")
        self.assertTrue(added["visible"])
        self.assertEqual(len(data["extraSections"]), 1)

    def test_slugify_page_title(self):
        self.assertEqual(slugify("Matcha Lab Notes"), "matcha-lab-notes")

    def test_add_site_page_writes_html_and_nav(self):
        tmp = tempfile.mkdtemp(prefix="cms-visual-")
        try:
            project = os.path.join(tmp, "project")
            os.makedirs(project)
            nav = {"left": [], "right": [{"label": "People", "href": "People & Places.html"}]}
            result = add_site_page(
                project_dir=project,
                title="Our Studio",
                heading="Our Studio",
                body="A short story about the studio.",
                nav=nav,
            )
            self.assertTrue(os.path.isfile(os.path.join(project, result["filename"])))
            with open(os.path.join(project, result["filename"]), encoding="utf-8") as fh:
                html = fh.read()
            self.assertIn("Our Studio", html)
            self.assertIn('id="root"', html)
            self.assertEqual(nav["right"][-1]["label"], "Our Studio")
            self.assertEqual(nav["right"][-1]["href"], result["filename"])
            self.assertIn("Our Studio", result["html"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_draft_site_page_avoids_existing_names(self):
        nav = {"left": [], "right": []}
        first = draft_site_page("Notes", "Notes", "Hi", nav, [])
        second = draft_site_page("Notes", "Notes", "Hi", {"left": [], "right": []}, [first["filename"]])
        self.assertEqual(first["filename"], "notes.html")
        self.assertEqual(second["filename"], "notes-2.html")


class PreviewRouteTests(unittest.TestCase):
    def setUp(self):
        self._password = app_module.CMS_PASSWORD
        self._backend = storage.BACKEND
        app_module.CMS_PASSWORD = ""
        storage.BACKEND = "local"
        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        app_module.CMS_PASSWORD = self._password
        storage.BACKEND = self._backend

    def test_preview_home_returns_rewritten_html(self):
        response = self.client.get("/preview/home")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/preview-static/", html)
        self.assertIn("cms-visual.js", html)

    def test_preview_people_handles_spaces_in_filename(self):
        response = self.client.get("/preview/people")
        self.assertEqual(response.status_code, 200)
        self.assertIn("cms-visual.js", response.get_data(as_text=True))

    def test_preview_missing_page_is_404(self):
        response = self.client.get("/preview/not-a-real-page")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
