"""The CRM is laid out like the website: menu pages first, then the rest.

The grouping is written down in app.CMS_SITE_PAGES rather than read from
data/nav.js on every request (online that would be a GitHub API call per page
view). These tests are what keeps the two honest: change the site's menu and
the CRM grouping has to follow, or this file fails.

Run with:  python test_cms_nav.py
"""

import html
import os
import re
import sys
import unittest
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import CMS_SITE_PAGES, app, cms_page_groups, load_data  # noqa: E402

PROJECT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Emma-Basic-The-Basic-Ingredients",
    "project",
)


def _menu_entries():
    """(label, file) for every link in the website's own top menu."""
    nav = load_data("nav")
    items = (nav.get("left") or []) + (nav.get("right") or [])
    return [(item.get("label"), unquote(item.get("href") or "")) for item in items]


def _group(label):
    for group in cms_page_groups():
        if group["label"] == label:
            return group
    raise AssertionError("no %r group in the sidebar" % label)


class PageRegistryTests(unittest.TestCase):
    def test_every_page_names_the_file_it_edits(self):
        for page in CMS_SITE_PAGES:
            self.assertTrue(page.get("file"), page["label"])
            self.assertTrue(
                os.path.exists(os.path.join(PROJECT, page["file"])),
                "%s edits a file that is not in the project: %s" % (page["label"], page["file"]),
            )
            self.assertTrue(page.get("summary"), page["label"])
            self.assertTrue(page.get("icon"), page["label"])

    def test_main_menu_group_matches_the_live_site_menu(self):
        menu = _menu_entries()
        grouped = [(p["menu_label"], p["file"]) for p in _group("Main menu")["pages"]]
        self.assertEqual(grouped, menu)

    def test_other_pages_group_is_everything_not_in_the_menu(self):
        menu_files = {file for _label, file in _menu_entries()}
        others = _group("Other pages")["pages"]
        self.assertTrue(others)
        for page in others:
            self.assertNotIn(page["file"], menu_files)
            self.assertIsNone(page.get("menu_label"))

    def test_groups_between_them_hold_every_page_exactly_once(self):
        grouped = [p for group in cms_page_groups() for p in group["pages"]]
        self.assertEqual(
            sorted(p["label"] for p in grouped),
            sorted(p["label"] for p in CMS_SITE_PAGES),
        )


class SidebarTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _sidebar(self, url="/"):
        page = html.unescape(self.client.get(url).get_data(as_text=True))
        match = re.search(r'<nav class="sidebar-nav">(.*?)</nav>', page, re.S)
        self.assertTrue(match, "no sidebar on %s" % url)
        return match.group(1)

    def test_sidebar_groups_the_pages_instead_of_one_flat_list(self):
        sidebar = self._sidebar()
        self.assertIn(">Main menu<", sidebar)
        self.assertIn(">Other pages<", sidebar)
        self.assertIn(">Tools<", sidebar)
        self.assertNotIn(">Website pages<", sidebar)
        self.assertLess(sidebar.index("Main menu"), sidebar.index("Other pages"))
        self.assertLess(sidebar.index("Other pages"), sidebar.index("Tools"))

    def test_menu_pages_are_named_the_way_the_website_names_them(self):
        sidebar = self._sidebar()
        for label, _file in _menu_entries():
            self.assertIn(label, sidebar)
        # The CRM's own name stays alongside it when the two differ.
        self.assertIn("Products Without E-Numbers", sidebar)
        self.assertIn('class="sub">Our Products<', sidebar)
        self.assertIn('class="sub">People &amp; Places<', self._sidebar().replace("&", "&amp;"))

    def test_under_construction_stays_its_own_entry_under_tools(self):
        sidebar = self._sidebar()
        self.assertIn("Under construction", sidebar)
        self.assertGreater(sidebar.index("Under construction"), sidebar.index("Tools"))
        for page in CMS_SITE_PAGES:
            self.assertNotEqual(page["label"], "Under construction")

    def test_every_page_is_still_one_click_away(self):
        sidebar = self._sidebar()
        with app.test_request_context():
            from flask import url_for
            for page in CMS_SITE_PAGES:
                self.assertIn('href="%s"' % url_for(page["endpoint"]), sidebar)
            for endpoint in ("index", "products", "visual_editor", "maintenance_page"):
                self.assertIn('href="%s"' % url_for(endpoint), sidebar)

    def test_each_page_carries_an_icon_with_its_label(self):
        sidebar = self._sidebar()
        # One <svg> per link: icon-only or label-only navigation is harder to scan.
        links = re.findall(r"<a\b.*?</a>", sidebar, re.S)
        self.assertGreaterEqual(len(links), len(CMS_SITE_PAGES) + 4)
        for link in links:
            self.assertIn("<svg", link)
            self.assertIn('class="lbl"', link)


class DashboardTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_dashboard_uses_the_same_groups_and_says_what_each_page_holds(self):
        page = html.unescape(self.client.get("/").get_data(as_text=True))
        for group in cms_page_groups():
            self.assertIn(">%s</h2>" % group["label"], page)
        self.assertIn(">Tools</h2>", page)
        for entry in CMS_SITE_PAGES:
            self.assertIn(entry["summary"], page)
            self.assertIn(entry["file"], page)
            self.assertIn(entry["label"], page)


class PageIndexTests(unittest.TestCase):
    """Each editor page builds its own "On this page" list from its cards."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_every_editor_page_has_enough_headings_to_index(self):
        # The builder needs three named blocks before it shows anything, so a
        # page whose cards stop carrying <h2> titles would quietly lose its
        # index. The catalog's category names are headings for this reason.
        for page in CMS_SITE_PAGES:
            with app.test_request_context():
                from flask import url_for
                url = url_for(page["endpoint"])
            body = self.client.get(url).get_data(as_text=True)
            content = body.split('<div class="content-inner">', 1)[-1]
            self.assertGreaterEqual(
                content.count("<h2"), 3,
                "%s has too few card headings to build a page index" % page["label"],
            )

    def test_the_index_is_built_in_the_shared_layout(self):
        # The list is assembled in the browser from the cards actually on the
        # page, so what the server ships is the builder plus its styles.
        body = self.client.get("/places").get_data(as_text=True)
        self.assertIn('nav.className = "page-index"', body)
        self.assertIn('label.textContent = "On this page"', body)
        self.assertIn(".page-index a.current", body)


class CollapsedEditorSectionsTests(unittest.TestCase):
    """Editor cards start collapsed so you open one section instead of scrolling."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_shared_layout_collapses_h2_cards_by_default(self):
        body = self.client.get("/journal").get_data(as_text=True)
        self.assertIn("function ebCollapseEditorSections", body)
        self.assertIn("ebCollapseEditorSections(inner)", body)
        self.assertIn('classList.add("card-section")', body)
        self.assertIn('summary.className = "card-section-summary"', body)

    def test_collapse_keeps_show_on_site_with_the_heading(self):
        """Page footer only has a visibility checkbox. If wrapAsDetails leaves
        that box in the closed details body, the collapsed card looks empty.
        Lift the card's own show-on-site label into the summary next to the h2.
        """
        body = self.client.get("/homepage").get_data(as_text=True)
        wrap = body.split("function wrapAsDetails", 1)[1].split(
            "function isFollowOnSection", 1
        )[0]
        self.assertIn("function ebLiftShowOnSite", wrap)
        self.assertIn('label.section-vis', wrap)
        self.assertIn("summary.appendChild(vis)", wrap)

    def test_page_index_jump_opens_the_collapsed_section(self):
        body = self.client.get("/places").get_data(as_text=True)
        self.assertIn("item.card.open = true", body)

    def test_journal_posts_list_has_a_heading_so_it_can_collapse(self):
        html = self.client.get("/journal").get_data(as_text=True)
        content = html.split('<div class="content-inner">', 1)[-1]
        self.assertRegex(content, r"<h2[^>]*>\s*Posts\s*<")

    def test_save_bars_stay_outside_cards(self):
        from html.parser import HTMLParser

        void = {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        }

        class Nesting(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack = []
                self.card_depth = 0
                self.save_inside = False
                self.save_outside = False

            def handle_starttag(self, tag, attrs):
                classes = dict(attrs).get("class", "").split()
                is_card = "card" in classes
                if "save-bar" in classes:
                    if self.card_depth:
                        self.save_inside = True
                    else:
                        self.save_outside = True
                if tag in void:
                    return
                self.stack.append(is_card)
                if is_card:
                    self.card_depth += 1

            def handle_endtag(self, tag):
                if tag in void or not self.stack:
                    return
                if self.stack.pop():
                    self.card_depth -= 1

        for url in ("/journal", "/places", "/homepage"):
            html = self.client.get(url).get_data(as_text=True)
            content = html.split('<div class="content-inner">', 1)[-1]
            parser = Nesting()
            parser.feed(content)
            self.assertTrue(parser.save_outside, "%s has no save bar outside cards" % url)
            self.assertFalse(parser.save_inside, "%s traps a save bar inside a card" % url)


if __name__ == "__main__":
    unittest.main()
