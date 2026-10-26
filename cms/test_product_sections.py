"""Product pages hide ingredients, allergens, and pairs-with.
Homepage staples link to the product page instead of the side panel.

Run with:  python test_product_sections.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")


def _read(name):
    with open(os.path.join(PROJECT, name), encoding="utf-8") as handle:
        return handle.read()


class ProductSectionTests(unittest.TestCase):
    def test_product_page_does_not_render_those_blocks(self):
        src = _read("components/ProductDetail.jsx")
        html = _read("product.html")
        self.assertNotIn(">Ingredients<", src)
        self.assertNotIn(">Allergens<", src)
        self.assertNotIn(">Pairs with<", src)
        self.assertNotIn("product.ingredients", src)
        self.assertNotIn("product.allergens", src)
        self.assertNotIn("product.pairings", src)
        self.assertIn("product.warning", src)
        self.assertIn("ProductDetail.jsx?v=29", html)

    def test_homepage_staples_link_to_the_product_page(self):
        rail = _read("components/ProductRail.jsx")
        app = _read("components/App.jsx")
        home = _read("Emma Basic Homepage.html")
        self.assertIn('product.html?id=', rail)
        self.assertIn("dragRef.current.moved", rail)
        self.assertNotIn("onOpen", rail)
        self.assertNotIn("SlideOutPanel", app)
        self.assertNotIn("openId", app)
        self.assertIn("<ProductRail", app)
        self.assertNotIn("SlideOutPanel.jsx", home)
        self.assertIn("ProductRail.jsx?v=11", home)
        self.assertFalse(os.path.exists(os.path.join(PROJECT, "components", "SlideOutPanel.jsx")))


if __name__ == "__main__":
    unittest.main()
