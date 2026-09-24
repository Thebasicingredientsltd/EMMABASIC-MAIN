"""Search & sharing (SEO) helpers for the Emma Basic CMS.

Each public page stores an optional `seo` object on its CMS data file.
On save, those fields are written into the page's HTML <head> so Google and
link previews see the tags without waiting for JavaScript.
"""

from __future__ import annotations

import re
from html import escape, unescape
from urllib.parse import quote

SITE_ORIGIN = "https://emmabasic.co.uk"
SITE_NAME = "Emma Basic"

SEO_START = "<!--cms-seo-start-->"
SEO_END = "<!--cms-seo-end-->"

TITLE_RE = re.compile(r"<title\b[^>]*>.*?</title>", re.IGNORECASE | re.DOTALL)
DATA_SCRIPT_RE = re.compile(
    r'<script\b[^>]*\bsrc=["\']data/[^"\']+["\'][^>]*>\s*</script>',
    re.IGNORECASE,
)
SEO_SCRIPT_RE = re.compile(
    r"\s*<script\b[^>]*\bsrc=['\"]components/seo\.js[^'\"]*['\"][^>]*>\s*</script>",
    re.IGNORECASE,
)

# Public pages the CMS already edits. `file` is the HTML filename in project/.
# `seo_path` is the dotted location of the seo object on that page's data file.
PAGES = [
    {
        "id": "homepage",
        "data_key": "homepage",
        "file": "Emma Basic Homepage.html",
        "url_path": "/",
        "default_title": "Emma Basic",
        "seo_path": ("seo",),
        "script_id": "homepage",
        "fallback_desc_paths": (("hero", "body"), ("banner", "text")),
        "fallback_image_paths": (("hero", "image"),),
    },
    {
        "id": "index",
        "data_key": "homepage",
        "file": "index.html",
        "url_path": "/",
        "default_title": "Emma Basic",
        "seo_path": ("seo",),
        "script_id": None,
        "fallback_desc_paths": (("hero", "body"), ("banner", "text")),
        "fallback_image_paths": (("hero", "image"),),
    },
    {
        "id": "catalog",
        "data_key": "catalog",
        "file": "Our Products.html",
        "url_path": "/Our%20Products.html",
        "default_title": "Our Products — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "catalog",
        "fallback_desc_paths": (("hero", "subtitle"),),
    },
    {
        "id": "product",
        "data_key": "catalog",
        "file": "product.html",
        "url_path": "/product.html",
        "default_title": "Emma Basic — Product",
        "seo_path": ("seo",),
        "script_id": "product",
        "fallback_desc_paths": (("hero", "subtitle"),),
    },
    {
        "id": "journal",
        "data_key": "journal",
        "file": "Journal.html",
        "url_path": "/Journal.html",
        "default_title": "Field Notes — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "journal",
        "fallback_desc_paths": (("hero", "subtitle"),),
    },
    {
        "id": "journal_post",
        "data_key": "journal",
        "file": "journal-post.html",
        "url_path": "/journal-post.html",
        "default_title": "Journal — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "journal_post",
        "fallback_desc_paths": (("hero", "subtitle"),),
        "default_og_type": "article",
    },
    {
        "id": "story",
        "data_key": "story",
        "file": "Our Story.html",
        "url_path": "/Our%20Story.html",
        "default_title": "Our Story — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "story",
        "fallback_desc_paths": (("hero", "subtitle"),),
    },
    {
        "id": "people",
        "data_key": "people",
        "file": "People & Places.html",
        "url_path": "/People%20%26%20Places.html",
        "default_title": "People — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "people",
        "fallback_desc_paths": (("hero", "subtitle"), ("founder", "introLine")),
        "fallback_image_paths": (("founder", "image"),),
    },
    {
        "id": "places",
        "data_key": "places",
        "file": "Places.html",
        "url_path": "/Places.html",
        "default_title": "Places — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "places",
        "fallback_desc_paths": (("hero", "subtitle"),),
    },
    {
        "id": "distributor",
        "data_key": "people",
        "file": "Become a Distributor.html",
        "url_path": "/Become%20a%20Distributor.html",
        "default_title": "Become a Distributor — Emma Basic",
        "seo_path": ("distributor", "seo"),
        "script_id": "distributor",
        "fallback_desc_paths": (("distributor", "title"),),
    },
    {
        "id": "company",
        "data_key": "company",
        "file": "The Basic Ingredients.html",
        "url_path": "/The%20Basic%20Ingredients.html",
        "default_title": "The Basic Ingredients — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "company",
        "fallback_desc_paths": (("about", "body"), ("hero", "subtitle")),
    },
    {
        "id": "matcha",
        "data_key": "matcha",
        "file": "Matcha Lab.html",
        "url_path": "/Matcha%20Lab.html",
        "default_title": "Matcha Lab — Emma Basic",
        "seo_path": ("seo",),
        "script_id": "matcha",
        "fallback_desc_paths": (("hero", "subtitle"),),
    },
]


def page_by_id(page_id):
    for page in PAGES:
        if page["id"] == page_id:
            return page
    return None


def pages_for_data_key(data_key):
    return [page for page in PAGES if page["data_key"] == data_key]


def page_for_file(filename):
    for page in PAGES:
        if page["file"] == filename:
            return page
    return None


def default_canonical(page):
    path = page.get("url_path") or "/"
    if path == "/":
        return SITE_ORIGIN + "/"
    if path.startswith("http"):
        return path
    return SITE_ORIGIN + path


def item_canonical(page_id, item_id):
    if page_id == "product":
        return "%s/product.html?id=%s" % (SITE_ORIGIN, quote(str(item_id or ""), safe=""))
    if page_id == "journal_post":
        return "%s/journal-post.html?id=%s" % (SITE_ORIGIN, quote(str(item_id or ""), safe=""))
    page = page_by_id(page_id)
    return default_canonical(page) if page else SITE_ORIGIN + "/"


def plain_text(value):
    text = unescape(str(value or ""))
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _dig(data, path):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(key)
    if cur is None or isinstance(cur, (list, dict)):
        return ""
    return plain_text(cur)


def _nested(data, path):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return {}
        cur = cur.get(key)
    return cur if isinstance(cur, dict) else {}


def stored_seo(page, data):
    return _nested(data, page.get("seo_path") or ("seo",))


def fallback_description(page, data):
    for path in page.get("fallback_desc_paths") or ():
        text = _dig(data, path)
        if text:
            return text
    return ""


def fallback_image(page, data):
    for path in page.get("fallback_image_paths") or ():
        text = _dig(data, path)
        if text:
            return text
    return ""


def absolute_url(path):
    raw = (path or "").strip()
    if not raw:
        return ""
    if re.match(r"^https?:\/\/", raw, re.IGNORECASE):
        return raw
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("/"):
        return SITE_ORIGIN + raw
    return SITE_ORIGIN + "/" + raw.lstrip("./")


def resolve_seo(page, data, item=None):
    """Merge stored fields with quiet fallbacks for the public <head>."""
    stored = dict(stored_seo(page, data) or {})
    extra = {}
    if isinstance(item, dict):
        extra = dict(item.get("seo") or {})
        if not extra.get("title"):
            extra["title"] = extra.get("title") or item.get("title") or item.get("name") or ""
        if not extra.get("description"):
            extra["description"] = item.get("excerpt") or item.get("tagline") or extra.get("description") or ""
        if not extra.get("image"):
            extra["image"] = item.get("image") or extra.get("image") or ""
        if not extra.get("canonical") and item.get("id"):
            extra["canonical"] = item_canonical(page["id"], item.get("id"))

    def pick(key, fallback=""):
        return plain_text(extra.get(key) or stored.get(key) or fallback)

    title = pick("title", page.get("default_title") or SITE_NAME)
    description = pick("description", fallback_description(page, data))
    canonical = pick("canonical", default_canonical(page))
    image = pick("image", fallback_image(page, data))
    og_type = plain_text(extra.get("ogType"))
    if not og_type and page.get("default_og_type"):
        og_type = page["default_og_type"]
    if not og_type:
        og_type = pick("ogType", "website") or "website"
    noindex = bool(extra.get("noindex") if "noindex" in extra else stored.get("noindex"))
    return {
        "title": title or SITE_NAME,
        "description": description,
        "canonical": canonical,
        "image": image,
        "ogType": og_type,
        "noindex": noindex,
    }


def render_head_block(seo):
    """Return the inner HTML for the CMS-SEO marker block (no wrapper comments)."""
    title = seo.get("title") or SITE_NAME
    description = seo.get("description") or ""
    canonical = seo.get("canonical") or default_canonical({"url_path": "/"})
    image = absolute_url(seo.get("image") or "")
    og_type = seo.get("ogType") or "website"
    lines = [
        "<title>%s</title>" % escape(title),
    ]
    if description:
        desc = escape(description, quote=True)
        lines.append('<meta name="description" content="%s"/>' % desc)
        lines.append('<meta property="og:description" content="%s"/>' % desc)
        lines.append('<meta name="twitter:description" content="%s"/>' % desc)
    lines.append('<link rel="canonical" href="%s"/>' % escape(canonical, quote=True))
    lines.append('<meta property="og:title" content="%s"/>' % escape(title, quote=True))
    lines.append('<meta property="og:url" content="%s"/>' % escape(canonical, quote=True))
    lines.append('<meta property="og:type" content="%s"/>' % escape(og_type, quote=True))
    lines.append('<meta property="og:site_name" content="%s"/>' % escape(SITE_NAME, quote=True))
    if image:
        img = escape(image, quote=True)
        lines.append('<meta property="og:image" content="%s"/>' % img)
        lines.append('<meta name="twitter:image" content="%s"/>' % img)
        lines.append('<meta name="twitter:card" content="summary_large_image"/>')
    else:
        lines.append('<meta name="twitter:card" content="summary"/>')
    lines.append('<meta name="twitter:title" content="%s"/>' % escape(title, quote=True))
    if seo.get("noindex"):
        lines.append('<meta name="robots" content="noindex, nofollow"/>')
    return "\n".join(lines)


def inject_head_block(html, block):
    wrapped = "%s\n%s\n%s" % (SEO_START, block.strip(), SEO_END)
    start = html.find(SEO_START)
    end = html.find(SEO_END)
    if start != -1 and end != -1 and end > start:
        end += len(SEO_END)
        return html[:start] + wrapped + html[end:]
    match = TITLE_RE.search(html)
    if match:
        return html[: match.start()] + wrapped + html[match.end():]
    close = re.search(r"</head>", html, re.IGNORECASE)
    if close:
        return html[: close.start()] + wrapped + "\n" + html[close.start():]
    return wrapped + "\n" + html


def ensure_seo_script(html, script_id):
    if not script_id:
        return SEO_SCRIPT_RE.sub("", html)
    tag = '<script src="components/seo.js" data-eb-seo="%s"></script>' % script_id
    if "components/seo.js" in html:
        html = SEO_SCRIPT_RE.sub("", html)
    matches = list(DATA_SCRIPT_RE.finditer(html))
    if matches:
        last = matches[-1]
        return html[: last.end()] + "\n" + tag + html[last.end():]
    close = re.search(r"</head>", html, re.IGNORECASE)
    if close:
        return html[: close.start()] + tag + "\n" + html[close.start():]
    return html + "\n" + tag + "\n"


def apply_to_html(html, filename, data_key, data):
    """Inject SEO for this HTML file when it belongs to the saved data key."""
    page = page_for_file(filename)
    if not page or page["data_key"] != data_key:
        return html
    if not isinstance(data, dict):
        return html
    resolved = resolve_seo(page, data)
    html = inject_head_block(html, render_head_block(resolved))
    html = ensure_seo_script(html, page.get("script_id"))
    return html


def seo_is_blank(seo):
    if not isinstance(seo, dict):
        return True
    if seo.get("noindex"):
        return False
    for key in ("title", "description", "canonical", "image"):
        if plain_text(seo.get(key)):
            return False
    og_type = plain_text(seo.get("ogType"))
    if og_type and og_type != "website":
        return False
    return True
