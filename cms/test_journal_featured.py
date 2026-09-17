"""The Field Notes featured slot must only appear when a post is marked featured.

Run with:  python test_journal_featured.py
"""

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL_JSX = os.path.join(
    ROOT,
    "Emma-Basic-The-Basic-Ingredients",
    "project",
    "components",
    "Journal.jsx",
)


def pick_featured(posts):
    """Same rule the Journal page must use: only an explicitly featured post."""
    return next((p for p in posts if p.get("featured")), None)


class JournalFeaturedTests(unittest.TestCase):
    def test_no_featured_flag_means_no_large_post(self):
        posts = [
            {"id": "a", "featured": False},
            {"id": "b", "featured": False},
        ]
        self.assertIsNone(pick_featured(posts))

    def test_checked_post_is_the_large_post(self):
        posts = [
            {"id": "a", "featured": False},
            {"id": "b", "featured": True},
        ]
        self.assertEqual(pick_featured(posts)["id"], "b")

    def test_jsx_does_not_fall_back_to_the_first_post(self):
        with open(JOURNAL_JSX, encoding="utf-8") as f:
            source = f.read()
        assignment = re.search(
            r"const featured = ([^;]+);",
            source,
        )
        self.assertIsNotNone(assignment, "featured assignment missing")
        expr = assignment.group(1)
        self.assertNotIn(
            "filtered[0]",
            expr,
            "Journal still treats the first post as featured when none are checked",
        )
        self.assertIn("p.featured", expr)


if __name__ == "__main__":
    unittest.main()
