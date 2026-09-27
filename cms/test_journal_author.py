"""Author belongs on Field Notes cards, the article page, and the CMS form.

Run with:  python test_journal_author.py
"""

import os
import unittest

import import_blog_csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.join(ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
CMS = os.path.join(ROOT, "cms")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class JournalAuthorTests(unittest.TestCase):
    def test_cms_edit_form_has_author_field(self):
        html = read(os.path.join(CMS, "templates", "journal_edit.html"))
        self.assertIn(">Author</label>", html)
        self.assertIn('name="author"', html)

    def test_cms_list_can_show_author(self):
        html = read(os.path.join(CMS, "templates", "journal.html"))
        self.assertIn("p.author", html)

    def test_journal_save_persists_author(self):
        source = read(os.path.join(CMS, "app.py"))
        save = source.split("def journal_save", 1)[1].split("def journal_delete", 1)[0]
        self.assertIn('request.form.get("author"', save)
        self.assertIn('"author": post["author"]', save)

    def test_listing_shows_author_near_date(self):
        source = read(os.path.join(PROJECT, "components", "Journal.jsx"))
        self.assertIn("post.author", source)
        self.assertIn("function postByline", source)

    def test_article_page_shows_author(self):
        source = read(os.path.join(PROJECT, "components", "JournalPost.jsx"))
        self.assertIn("listing.author", source)
        self.assertIn("author", source)

    def test_ricos_paragraphs_become_body_blocks(self):
        doc = {
            "nodes": [
                {
                    "type": "PARAGRAPH",
                    "nodes": [{"type": "TEXT", "textData": {"text": "Hello soy."}}],
                },
                {
                    "type": "BULLETED_LIST",
                    "nodes": [
                        {
                            "type": "LIST_ITEM",
                            "nodes": [{"type": "TEXT", "textData": {"text": "One"}}],
                        }
                    ],
                },
            ]
        }
        blocks = import_blog_csv.ricos_to_blocks(doc)
        self.assertEqual(blocks[0], {"type": "p", "text": "Hello soy."})
        self.assertEqual(blocks[1]["type"], "p")
        self.assertIn("One", blocks[1]["text"])

    def test_slug_from_old_url(self):
        slug = import_blog_csv.slug_from_row({
            "Blog (Title)": "/news-2/what-makes-a-good-soy-sauce",
            "Title": "What makes a good Soy Sauce",
        })
        self.assertEqual(slug, "what-makes-a-good-soy-sauce")


if __name__ == "__main__":
    unittest.main()
