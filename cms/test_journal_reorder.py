"""Field Notes must be drag-reorderable, with earliest date first as the default.

Run with:  python test_journal_reorder.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import (  # noqa: E402
    app,
    insert_post_by_date,
    load_data,
    parse_journal_date,
    save_data,
    sort_posts_earliest_first,
)


class ParseJournalDateTests(unittest.TestCase):
    def test_reads_abbreviated_month(self):
        self.assertEqual(parse_journal_date("14 Apr 2026").date().isoformat(), "2026-04-14")

    def test_reads_full_month_name(self):
        self.assertEqual(parse_journal_date("02 June 2024").date().isoformat(), "2024-06-02")

    def test_blank_dates_sort_after_real_ones(self):
        self.assertGreater(parse_journal_date(""), parse_journal_date("14 Apr 2026"))


class SortAndInsertByDateTests(unittest.TestCase):
    def test_sorts_earliest_date_first(self):
        posts = [
            {"id": "new", "date": "14 Apr 2026"},
            {"id": "old", "date": "02 June 2018"},
            {"id": "mid", "date": "10 Mar 2025"},
        ]
        ordered = sort_posts_earliest_first(posts)
        self.assertEqual([p["id"] for p in ordered], ["old", "mid", "new"])

    def test_inserts_a_new_post_in_date_order(self):
        posts = [
            {"id": "old", "date": "02 June 2018"},
            {"id": "new", "date": "14 Apr 2026"},
        ]
        insert_post_by_date(posts, {"id": "mid", "date": "10 Mar 2025"})
        self.assertEqual([p["id"] for p in posts], ["old", "mid", "new"])


class JournalReorderEndpointTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_journal_page_shows_drag_handles(self):
        response = self.client.get("/journal")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/journal/reorder", html)
        self.assertIn("eb-sortable", html)
        self.assertIn("eb-drag-handle", html)
        self.assertIn("Drag the", html)

    def test_post_swaps_the_first_two_posts_then_restores(self):
        original = load_data("journal")
        ids = [p["id"] for p in original.get("posts", [])]
        self.assertGreaterEqual(len(ids), 2)
        order = [1, 0] + list(range(2, len(ids)))
        try:
            response = self.client.post(
                "/journal/reorder",
                json={"kind": "posts", "order": order},
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json()["ok"])
            swapped = [p["id"] for p in load_data("journal")["posts"]]
            self.assertEqual(swapped[0], ids[1])
            self.assertEqual(swapped[1], ids[0])
            self.assertEqual(swapped[2:], ids[2:])
        finally:
            with app.app_context():
                save_data("journal", original)
