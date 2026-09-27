"""One-off importer: old-site Blog.csv -> Field Notes (journal.js).

Usage (from the repo root or cms/):

    python cms/import_blog_csv.py
    python cms/import_blog_csv.py --csv "C:\\Users\\TBIL_Manager\\Downloads\\Blog.csv"

Published rows are added. Existing posts (matched by slug or title) are kept
and only filled in (author, date format, slug) — they are not duplicated.
Drafts (no "Published on" value) are skipped.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

CMS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CMS_DIR)

from werkzeug.utils import secure_filename  # noqa: E402

from app import (  # noqa: E402
    ALLOWED_EXT,
    DATA_FILES,
    HEADERS,
    PROJECT_DIR,
    UPLOAD_DIR,
    optimize_image_bytes,
)

DEFAULT_CSV = os.path.join(
    os.path.expanduser("~"), "Downloads", "Blog.csv"
)
WIX_IMAGE_RE = re.compile(r"^wix:image://v1/([^/#]+)(?:/([^#]*))?", re.I)
PLACEHOLDER_RE = re.compile(r"^i['’]m a paragraph", re.I)
SCRIPT_RE = re.compile(r"(?is)<script[^>]*>.*?</script>")
STYLE_RE = re.compile(r"(?is)<style[^>]*>.*?</style>")
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"[ \t\u00a0]+")
NON_SLUG_RE = re.compile(r"[^a-z0-9]+")
USER_AGENT = "EmmaBasicJournalImporter/1.0"


def load_journal():
    path = DATA_FILES["journal"]["file"]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    idx = text.index("=")
    payload = text[idx + 1 :].strip()
    if payload.endswith(";"):
        payload = payload[:-1].strip()
    return json.loads(payload)


def dumps_journal(data):
    body = json.dumps(data, ensure_ascii=False, indent=2)
    return "{header}\n{var} = {body};\n".format(
        header=HEADERS["journal"],
        var=DATA_FILES["journal"]["var"],
        body=body,
    )


def write_journal(data):
    path = DATA_FILES["journal"]["file"]
    text = dumps_journal(data)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def bump_journal_cache():
    stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    pattern = re.compile(r'(src="data/journal\.js)(?:\?v=[^"]*)?(")')
    for name in ("Journal.html", "journal-post.html"):
        path = os.path.join(PROJECT_DIR, name)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new_text = pattern.sub(r"\g<1>?v=%s\2" % stamp, text)
        if new_text != text:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(new_text)
            os.replace(tmp, path)


def clean_text(value):
    text = html.unescape(str(value or ""))
    text = SCRIPT_RE.sub("", text)
    text = STYLE_RE.sub("", text)
    text = TAG_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = WHITESPACE_RE.sub(" ", text)
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln).strip()


def node_text(node):
    if not isinstance(node, dict):
        return ""
    parts = []
    td = node.get("textData") or {}
    if td.get("text"):
        parts.append(str(td["text"]))
    for child in node.get("nodes") or []:
        parts.append(node_text(child))
    return "".join(parts)


def ricos_to_blocks(doc):
    """Turn a Wix Ricos document into journal body blocks (p / h2 / rule)."""
    if isinstance(doc, str):
        try:
            doc = json.loads(doc)
        except json.JSONDecodeError:
            text = clean_text(doc)
            return [{"type": "p", "text": text}] if text else []
    if not isinstance(doc, dict):
        return []

    blocks = []

    def add_p(text):
        text = clean_text(text)
        if text:
            blocks.append({"type": "p", "text": text})

    def add_h2(text):
        text = clean_text(text)
        if text:
            blocks.append({"type": "h2", "text": text})

    def walk_list(node, ordered):
        for i, item in enumerate(node.get("nodes") or [], 1):
            text = clean_text(node_text(item))
            if not text:
                continue
            prefix = "%d. " % i if ordered else "• "
            if not re.match(r"^(\d+\.|•|-)\s", text):
                text = prefix + text
            add_p(text)

    for node in doc.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        kind = str(node.get("type") or "").upper()
        if kind == "PARAGRAPH":
            add_p(node_text(node))
        elif kind == "HEADING":
            add_h2(node_text(node))
        elif kind == "BULLETED_LIST":
            walk_list(node, ordered=False)
        elif kind == "ORDERED_LIST":
            walk_list(node, ordered=True)
        elif kind == "TABLE":
            for row in node.get("nodes") or []:
                cells = []
                for cell in row.get("nodes") or []:
                    cell_text = clean_text(node_text(cell))
                    if cell_text:
                        cells.append(cell_text)
                if cells:
                    add_p(" — ".join(cells))
        elif kind in ("DIVIDER", "HORIZONTAL_RULE"):
            blocks.append({"type": "rule"})
        elif kind in ("IMAGE", "VIDEO", "GALLERY", "FILE"):
            continue
        else:
            add_p(node_text(node))
    return blocks


def slugify(title):
    slug = NON_SLUG_RE.sub("-", (title or "").lower()).strip("-")
    return slug or "post"


def slug_from_row(row):
    path = urllib.parse.unquote((row.get("Blog (Title)") or "").strip())
    path = path.strip("/")
    if path:
        last = urllib.parse.unquote(path.split("/")[-1])
        slug = slugify(last)
        if slug and slug != "post":
            return slug
    return slugify(row.get("Title") or "")


def format_date(iso_value, published_on=""):
    raw = (iso_value or "").strip()
    if raw:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y")
        except ValueError:
            pass
    pub = (published_on or "").strip()
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", pub)
    if m:
        try:
            dt = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            return dt.strftime("%d %b %Y")
        except ValueError:
            pass
    return raw or pub


def parse_display_date(value):
    text = (value or "").strip()
    for fmt in ("%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    if "T" in text:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def norm_title(value):
    text = (value or "").lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def make_excerpt(short, blocks):
    short = clean_text(short)
    if short and not PLACEHOLDER_RE.match(short):
        return short
    for block in blocks:
        if block.get("type") == "p" and block.get("text"):
            text = block["text"]
            if len(text) <= 240:
                return text
            cut = text[:237].rsplit(" ", 1)[0]
            return cut.rstrip(",;:") + "…"
    return ""


def wix_image_url(value):
    value = (value or "").strip()
    if not value:
        return "", ""
    if value.startswith("http://") or value.startswith("https://"):
        name = os.path.basename(urllib.parse.urlparse(value).path)
        return value, urllib.parse.unquote(name)
    match = WIX_IMAGE_RE.match(value)
    if not match:
        return "", ""
    media_id = match.group(1)
    filename = urllib.parse.unquote(match.group(2) or "")
    return "https://static.wixstatic.com/media/" + media_id, filename


def download_image(url, filename, index):
    if not url:
        return "", "no image url"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read()
            content_type = (resp.headers.get("Content-Type") or "").lower()
    except (urllib.error.URLError, TimeoutError) as exc:
        return "", str(exc)

    if not raw or "html" in content_type or raw[:15].lstrip().lower().startswith(b"<!doctype"):
        return "", "not an image"

    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        guessed = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/avif": ".avif",
        }.get(content_type.split(";")[0].strip(), "")
        ext = guessed if guessed in ALLOWED_EXT else ".jpg"
        filename = (filename or "image") + ext

    data, _info = optimize_image_bytes(raw, ext)
    base = secure_filename(os.path.splitext(os.path.basename(filename or "image"))[0]) or "image"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = "%s-%s-%02d%s" % (base, stamp, index, ext)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, name)
    with open(dest, "wb") as fh:
        fh.write(data)
    return "assets/uploads/" + name, ""


def find_existing(posts, slug, title):
    want = norm_title(title)
    want_slug = (slug or "").lower()
    for i, post in enumerate(posts):
        pid = str(post.get("id") or "")
        if pid == slug or pid.lower() == want_slug:
            return i
        if norm_title(pid) == want:
            return i
        if norm_title(post.get("title") or "") == want:
            return i
    return None


def read_csv_rows(path):
    raw = open(path, "rb").read()
    text = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError("Could not decode CSV")
    return list(csv.DictReader(text.splitlines()))


def is_published(row):
    return bool((row.get("Published on") or "").strip())


def unique_slug(slug, taken):
    base = slug or "post"
    candidate = base
    n = 2
    while candidate in taken:
        candidate = "%s-%d" % (base, n)
        n += 1
    return candidate


def import_rows(rows, download=True):
    data = load_journal()
    posts = list(data.get("posts") or [])
    articles = dict(data.get("articles") or {})
    taken = {str(p.get("id") or "") for p in posts}
    taken.update(articles.keys())

    summary = {
        "imported": [],
        "updated": [],
        "skipped": [],
        "images_failed": [],
    }

    for i, row in enumerate(rows):
        title = clean_text(row.get("Title") or "")
        if not title:
            summary["skipped"].append({"title": "(empty title)", "reason": "no title"})
            continue
        if not is_published(row):
            summary["skipped"].append({
                "title": title,
                "reason": "not marked published on the old site",
            })
            continue

        slug = slug_from_row(row)
        author = clean_text(row.get("Author") or "")
        date = format_date(row.get("Date") or "", row.get("Published on") or "")
        blocks = ricos_to_blocks(row.get("Long Description") or "")
        if not blocks:
            summary["skipped"].append({"title": title, "reason": "empty body"})
            continue
        excerpt = make_excerpt(row.get("Short Description") or "", blocks)

        match = find_existing(posts, slug, title)
        if match is not None:
            post = posts[match]
            old_id = post.get("id") or ""
            new_id = old_id
            if " " in old_id or not old_id:
                new_id = unique_slug(slug, taken - {old_id})
            post["id"] = new_id
            post["title"] = post.get("title") or title
            post["date"] = date or post.get("date") or ""
            if author and not post.get("author"):
                post["author"] = author
            elif "author" not in post:
                post["author"] = author
            if not post.get("excerpt"):
                post["excerpt"] = excerpt
            article = articles.pop(old_id, None) or articles.get(new_id) or {}
            article["title"] = article.get("title") or title
            article["date"] = post["date"]
            article["category"] = article.get("category") or post.get("category") or "Ingredient Stories"
            article["author"] = post.get("author") or ""
            if not article.get("body"):
                article["body"] = blocks
            articles[new_id] = article
            taken.discard(old_id)
            taken.add(new_id)
            posts[match] = post
            summary["updated"].append({"title": title, "id": new_id})
            continue

        slug = unique_slug(slug, taken)
        image_path = ""
        if download:
            url, filename = wix_image_url(row.get("Image") or "")
            image_path, err = download_image(url, filename, i)
            if err:
                summary["images_failed"].append({"title": title, "reason": err})
                image_path = ""

        post = {
            "id": slug,
            "category": "Ingredient Stories",
            "date": date,
            "title": title,
            "author": author,
            "excerpt": excerpt,
            "image": image_path,
            "tone": "warm",
            "featured": False,
            "seo": {
                "title": title,
                "description": excerpt,
                "canonical": "https://emmabasic.co.uk/journal-post.html?id=%s" % slug,
                "image": image_path,
                "ogType": "article",
                "noindex": False,
            },
        }
        article = {
            "category": "Ingredient Stories",
            "date": date,
            "readTime": "",
            "title": title,
            "image": image_path,
            "imagePosition": "",
            "intro": "",
            "body": blocks,
            "author": author,
        }
        posts.append(post)
        articles[slug] = article
        taken.add(slug)
        summary["imported"].append({"title": title, "id": slug, "author": author})

    posts.sort(key=lambda p: parse_display_date(p.get("date") or ""), reverse=True)
    data["posts"] = posts
    data["articles"] = articles
    write_journal(data)
    bump_journal_cache()
    return summary, data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import old-site Blog.csv into Field Notes.")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to Blog.csv")
    parser.add_argument("--no-images", action="store_true", help="Skip image downloads")
    args = parser.parse_args(argv)

    csv_path = os.path.abspath(args.csv)
    if not os.path.isfile(csv_path):
        print("CSV not found:", csv_path, file=sys.stderr)
        return 1

    rows = read_csv_rows(csv_path)
    summary, data = import_rows(rows, download=not args.no_images)

    print("Imported %d post(s)" % len(summary["imported"]))
    for item in summary["imported"]:
        print("  + %s [%s] author=%r" % (item["title"], item["id"], item["author"]))
    print("Updated %d existing post(s)" % len(summary["updated"]))
    for item in summary["updated"]:
        print("  ~ %s [%s]" % (item["title"], item["id"]))
    print("Skipped %d row(s)" % len(summary["skipped"]))
    for item in summary["skipped"]:
        print("  - %s (%s)" % (item["title"], item["reason"]))
    if summary["images_failed"]:
        print("Images missing on %d post(s)" % len(summary["images_failed"]))
        for item in summary["images_failed"]:
            print("  ! %s (%s)" % (item["title"], item["reason"]))
    print("Total posts in journal.js:", len(data.get("posts") or []))
    print("Wrote", DATA_FILES["journal"]["file"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
