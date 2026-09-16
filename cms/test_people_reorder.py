"""Team members must be reorderable by a permutation of their current indices.

Run with:  python test_people_reorder.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, load_data, reorder_by_index, save_data  # noqa: E402


class ReorderByIndexTests(unittest.TestCase):
    def test_reorders_names_into_the_given_order(self):
        members = [{"name": "Emma"}, {"name": "Yoko"}, {"name": "Taiki"}]
        out = reorder_by_index(members, [2, 0, 1])
        self.assertEqual([m["name"] for m in out], ["Taiki", "Emma", "Yoko"])

    def test_rejects_a_list_that_is_not_a_permutation(self):
        with self.assertRaises(ValueError):
            reorder_by_index(["a", "b"], [0, 0])

    def test_rejects_non_integer_order(self):
        with self.assertRaises(ValueError):
            reorder_by_index(["a", "b"], ["0", "1"])


class PeopleReorderEndpointTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_people_page_shows_drag_handles(self):
        response = self.client.get("/people")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("/people/reorder", html)
        self.assertIn("eb-sortable", html)
        self.assertIn("eb-drag-handle", html)
        self.assertIn("Drag the", html)

    def test_post_swaps_the_first_two_members_then_restores(self):
        original = load_data("people")
        names = [m["name"] for m in original["team"]["members"]]
        self.assertGreaterEqual(len(names), 2)
        order = [1, 0] + list(range(2, len(names)))
        try:
            response = self.client.post(
                "/people/reorder",
                json={"kind": "members", "order": order},
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json()["ok"])
            swapped = [m["name"] for m in load_data("people")["team"]["members"]]
            self.assertEqual(swapped[0], names[1])
            self.assertEqual(swapped[1], names[0])
            self.assertEqual(swapped[2:], names[2:])
        finally:
            with app.app_context():
                restored = load_data("people")
                restored["team"]["members"] = original["team"]["members"]
                save_data("people", restored)


if __name__ == "__main__":
    unittest.main()
