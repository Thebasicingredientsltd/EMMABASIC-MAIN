"""
Emma Basic — local CMS admin panel.

A small Flask app that lets you edit the website's products, blog posts and
homepage content through web forms, upload images, and publish changes to
GitHub with one click.

The website stores its content in three data files:
    Emma-Basic-The-Basic-Ingredients/project/data/products.js
    Emma-Basic-The-Basic-Ingredients/project/data/journal.js
    Emma-Basic-The-Basic-Ingredients/project/data/homepage.js

Each file is a single assignment of the form `window.EB_XXX = <JSON>;`.
This app reads the JSON payload, presents it as forms, and writes it back.

Run:
    python app.py
then open http://localhost:5000
"""

import hmac
import io
import json
import mimetypes
import os
import re
import subprocess
from datetime import datetime, timezone
from html import escape as html_escape
from html.parser import HTMLParser

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

import maintenance
import seo
import stockists_import
import storage

try:
    from PIL import Image, ImageOps
    # This is a local tool where the owner uploads their own photos, so lift
    # Pillow's decompression-bomb guard to allow very large source images.
    Image.MAX_IMAGE_PIXELS = None
    HAVE_PIL = True
except Exception:  # Pillow not installed
    HAVE_PIL = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CMS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CMS_DIR)
PROJECT_DIR = os.path.join(REPO_ROOT, "Emma-Basic-The-Basic-Ingredients", "project")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
UPLOAD_DIR = os.path.join(ASSETS_DIR, "uploads")

DATA_FILES = {
    "products": {"file": os.path.join(DATA_DIR, "products.js"), "var": "window.EB_PRODUCTS"},
    "journal": {"file": os.path.join(DATA_DIR, "journal.js"), "var": "window.EB_JOURNAL"},
    "homepage": {"file": os.path.join(DATA_DIR, "homepage.js"), "var": "window.EB_HOME"},
    "catalog": {"file": os.path.join(DATA_DIR, "catalog.js"), "var": "window.EB_CATALOG"},
    "people": {"file": os.path.join(DATA_DIR, "people.js"), "var": "window.EB_PEOPLE"},
    "nav": {"file": os.path.join(DATA_DIR, "nav.js"), "var": "window.EB_NAV"},
    "places": {"file": os.path.join(DATA_DIR, "places.js"), "var": "window.EB_PLACES"},
    "story": {"file": os.path.join(DATA_DIR, "story.js"), "var": "window.EB_STORY"},
    "company": {"file": os.path.join(DATA_DIR, "company.js"), "var": "window.EB_COMPANY"},
    "matcha": {"file": os.path.join(DATA_DIR, "matcha.js"), "var": "window.EB_MATCHA"},
    "site": {"file": os.path.join(DATA_DIR, "site.js"), "var": "window.EB_SITE"},
}

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"}

# Image optimization settings. Uploaded photos are scaled down to at most
# MAX_DIM on the longest edge and re-encoded to shed file size — the main
# cause of a slow site is oversized source images.
MAX_DIM = 2000
JPEG_QUALITY = 82
WEBP_QUALITY = 82

# Portraits are often exported with a flat white margin baked into the frame.
# The team cards crop to a square, so that margin would survive as bars along
# the edges. These bounds decide when a margin is deliberate padding rather
# than part of the photograph: it has to be near-white, and it has to arrive
# as an evenly matched pair of opposite edges, no deeper than MAX_FRACTION.
BORDER_TRIM_TOLERANCE = 12
BORDER_TRIM_MIN_LIGHTNESS = 235
BORDER_TRIM_MIN_FRACTION = 0.005
BORDER_TRIM_MAX_FRACTION = 0.45
BORDER_TRIM_SYMMETRY = 0.25
BORDER_TRIM_EDGE_CONTENT = 0.15

HEADERS = {
    "products": "/* Emma Basic — product data (CMS-managed). The payload below is strict JSON. */",
    "journal": "/* Emma Basic — journal / blog data (CMS-managed). The payload below is strict JSON. */",
    "homepage": "/* Emma Basic — homepage content (CMS-managed). The payload below is strict JSON. */",
    "catalog": "/* Emma Basic — full product catalog (CMS-managed). The payload below is strict JSON. */",
    "people": "/* Emma Basic — People & Places page content (CMS-managed). The payload below is strict JSON. */",
    "nav": "/* Emma Basic — site navigation (CMS-managed). The payload below is strict JSON. */",
    "places": "/* Emma Basic — Where to find our products (CMS-managed). The payload below is strict JSON. */",
    "story": "/* Emma Basic — Our Story page content (CMS-managed). The payload below is strict JSON. */",
    "company": "/* Emma Basic — The Basic Ingredients page content (CMS-managed). The payload below is strict JSON. */",
    "matcha": "/* Emma Basic — Matcha Lab page content (CMS-managed). The payload below is strict JSON. */",
    "site": "/* Emma Basic — site-wide settings (CMS-managed). The payload below is strict JSON. */",
}

app = Flask(__name__)
# In production (online) a stable secret must be provided so signed session
# cookies survive across serverless instances. Locally it falls back to a
# fixed dev value.
app.secret_key = os.environ.get("CMS_SECRET") or "emma-basic-cms-local"

# Project directory as a repo-relative path (forward slashes) — the storage
# layer addresses everything relative to the repo root.
PROJECT_REL = "Emma-Basic-The-Basic-Ingredients/project"


def _rel(abs_path):
    """Convert an absolute path under the repo into a repo-relative path."""
    return os.path.relpath(abs_path, storage.REPO_ROOT).replace(os.sep, "/")


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
# A login is enforced whenever the CMS is online (GitHub backend) or whenever a
# CMS_PASSWORD is configured. Local runs without a password stay frictionless.
# Online, both CMS_USERNAME and CMS_PASSWORD must be set (Vercel env vars).
CMS_USERNAME = os.environ.get("CMS_USERNAME", "admin").strip() or "admin"
CMS_PASSWORD = os.environ.get("CMS_PASSWORD", "")


def _auth_required():
    return storage.is_github() or bool(CMS_PASSWORD)


def _credentials_match(supplied, expected):
    left = (supplied or "").encode("utf-8")
    right = (expected or "").encode("utf-8")
    if not right or len(left) != len(right):
        hmac.compare_digest(right or b"x", right or b"x")
        return False
    return hmac.compare_digest(left, right)


@app.before_request
def _require_login():
    if not _auth_required():
        return
    if request.endpoint in ("login", "static"):
        return
    if session.get("cms_auth"):
        return
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "Please sign in again, then retry the upload."}), 401
    return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    if not _auth_required():
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        user_ok = _credentials_match(request.form.get("username", "").strip(), CMS_USERNAME)
        pass_ok = _credentials_match(request.form.get("password", ""), CMS_PASSWORD)
        if user_ok and pass_ok:
            session["cms_auth"] = True
            session.permanent = True
            return redirect(request.form.get("next") or url_for("index"))
        error = ("Incorrect username or password." if CMS_PASSWORD
                 else "No CMS_PASSWORD is configured on the server.")
    return render_template("login.html", error=error, next=request.args.get("next", ""))


@app.route("/logout")
def logout():
    session.pop("cms_auth", None)
    flash("Signed out.", "ok")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Data file helpers
# ---------------------------------------------------------------------------
def load_data(key):
    """Read a data file and return the parsed JSON payload."""
    info = DATA_FILES[key]
    text = storage.read_text(_rel(info["file"]))
    # Strip everything up to the first '=' then trailing ';'
    idx = text.index("=")
    payload = text[idx + 1:].strip()
    if payload.endswith(";"):
        payload = payload[:-1].strip()
    return json.loads(payload)


def save_data(key, data):
    """Write the JSON payload back into the `window.EB_X = ...;` wrapper.

    Everything is persisted through the storage layer in a single batch:
      - the data file itself,
      - any images uploaded during this request (staged via `_stage_file`),
      - the refreshed ?v= cache-buster on the site's HTML pages.

    On the local backend that means writing the files to disk (you publish
    later with the Publish button). On the GitHub backend it becomes one atomic
    commit, which auto-deploys the live site.
    """
    info = DATA_FILES[key]
    body = json.dumps(data, ensure_ascii=False, indent=2)
    text = "{header}\n{var} = {body};\n".format(
        header=HEADERS[key], var=info["var"], body=body
    )
    changes = _drain_staged_files()
    changes.append((_rel(info["file"]), text, False))
    changes.extend(_html_publish_changes(key, data))
    storage.persist(changes, message="CMS: update %s" % key)


def load_catalog_bundle():
    """Catalog file is `{hero, categories}`. Older array-only files still load."""
    data = load_data("catalog")
    if isinstance(data, list):
        return {"hero": {}, "categories": data}
    data.setdefault("hero", {})
    data.setdefault("categories", [])
    return data


def _stage_file(relpath, data_bytes):
    """Buffer an uploaded file for the current request; it is written/committed
    together with the next save_data (or flushed explicitly by /api/upload)."""
    pending = getattr(g, "_pending_files", None)
    if pending is None:
        pending = []
        g._pending_files = pending
    pending.append((relpath, data_bytes, True))


def _drain_staged_files():
    pending = getattr(g, "_pending_files", None) or []
    g._pending_files = []
    return list(pending)


def lines_to_list(text):
    """Split a textarea into a clean list (one item per non-empty line)."""
    if not text:
        return []
    return [ln.strip() for ln in text.replace("\r\n", "\n").split("\n") if ln.strip()]


def list_to_lines(items):
    return "\n".join(items or [])


def paras_to_text(paras):
    """Join paragraphs with a blank line between them (for textarea editing)."""
    return "\n\n".join(paras or [])


def text_to_paras(text):
    if not text:
        return []
    chunks = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    return [c.strip() for c in chunks if c.strip()]


def body_to_text(body):
    """Convert an article body (list of blocks) into simple editable markup."""
    out = []
    for block in body or []:
        t = block.get("type")
        if t == "h2":
            out.append("## " + block.get("text", ""))
        elif t == "rule":
            out.append("---")
        else:
            out.append(block.get("text", ""))
    return "\n\n".join(out)


def text_to_body(text):
    """Parse editable markup back into article body blocks."""
    blocks = []
    for chunk in text_to_paras(text):
        if chunk == "---":
            blocks.append({"type": "rule"})
        elif chunk.startswith("## "):
            blocks.append({"type": "h2", "text": chunk[3:].strip()})
        else:
            blocks.append({"type": "p", "text": chunk})
    return blocks


def qa_to_text(qa):
    """Render a list of {q, a} pairs as editable text: question on the first
    line, answer on the following line(s), pairs separated by a blank line."""
    blocks = []
    for item in qa or []:
        q = (item.get("q") or "").strip()
        a = (item.get("a") or "").strip()
        blocks.append((q + "\n" + a).strip())
    return "\n\n".join(blocks)


def text_to_qa(text):
    qa = []
    for chunk in text_to_paras(text):
        lines = [ln for ln in chunk.split("\n")]
        q = lines[0].strip()
        a = " ".join(ln.strip() for ln in lines[1:]).strip()
        if q:
            qa.append({"q": q, "a": a})
    return qa


def parse_num(raw):
    """Parse a numeric form field. Returns int when whole, float otherwise,
    or None when blank/unparseable."""
    raw = (raw or "").strip()
    if raw == "":
        return None
    try:
        val = float(raw)
    except ValueError:
        return None
    return int(val) if val.is_integer() else val


def _apply_category_link_form(cat):
    """Link under a category on Our Products.

    Unchecked `link_hide` is omitted from POST, so missing means False.
    Older saves (reorder, table edit) omit the fields and must not wipe the
    link. Empty text with Hide unticked removes the link object.
    """
    if "link_label" not in request.form and "link_href" not in request.form:
        return
    label = request.form.get("link_label", "").strip()
    href = request.form.get("link_href", "").strip()
    hide = form_checkbox("link_hide")
    meta = dict(cat.get("meta") if isinstance(cat.get("meta"), dict) else {})
    if not label and not href and not hide:
        meta.pop("link", None)
        if meta:
            cat["meta"] = meta
        else:
            cat.pop("meta", None)
        return
    meta["link"] = {"label": label, "href": href, "hide": hide}
    cat["meta"] = meta


def _apply_hero_buttons_form(hero):
    """Homepage hero buttons (two fixed slots).

    Both slots are always stored so an emptied or hidden button stays that
    way; the live site must not fall back to defaults. Unchecked
    `hero_btnN_hide` is omitted from POST, so missing means False.
    """
    if not any(("hero_btn%d_label" % i) in request.form for i in (1, 2)):
        return
    buttons = []
    for i in (1, 2):
        buttons.append({
            "label": request.form.get("hero_btn%d_label" % i, "").strip(),
            "href": request.form.get("hero_btn%d_href" % i, "").strip(),
            "primary": i == 1,
            "hide": form_checkbox("hero_btn%d_hide" % i),
        })
    hero["buttons"] = buttons


def form_checkbox(name):
    """True when an HTML checkbox named `name` was checked.

    Unchecked boxes are omitted from the POST body. Missing therefore means
    False — never default a section back to visible on save.
    """
    raw = request.form.get(name)
    if raw is None:
        return False
    return str(raw).strip().lower() in ("on", "true", "1", "yes")


def _apply_seo_form(target):
    """Write Search & sharing fields from the current request onto `target`.

    Unchecked `seo_noindex` is omitted from POST, so missing means False.
    If every field is left blank, the seo object is removed.
    """
    existing = target.get("seo") if isinstance(target.get("seo"), dict) else {}
    # Page editors always submit seo_title (even when blank). Other saves
    # (reorder, visual patch, older tests) omit the fields and must not wipe SEO.
    if "seo_title" not in request.form and "seo_description" not in request.form:
        return
    payload = {
        "title": request.form.get("seo_title", "").strip(),
        "description": request.form.get("seo_description", "").strip(),
        "canonical": request.form.get("seo_canonical", "").strip(),
        "image": resolve_image("seo_image", existing.get("image", "")),
        "ogType": request.form.get("seo_og_type", "").strip() or "website",
        "noindex": form_checkbox("seo_noindex"),
    }
    if seo.seo_is_blank(payload):
        target.pop("seo", None)
    else:
        target["seo"] = payload


def _form_lines(name, keep_blank=False):
    """Split a textarea into lines. Empty lines are dropped unless keep_blank."""
    raw = (request.form.get(name, "") or "").replace("\r\n", "\n")
    lines = [ln.rstrip() for ln in raw.split("\n")]
    if keep_blank:
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return lines
    return [ln.strip() for ln in lines if ln.strip()]


def is_section_visible(section):
    """Live-site default: a section is shown unless `visible` is explicitly false."""
    if not isinstance(section, dict):
        return True
    return section.get("visible", True) is not False


app.jinja_env.globals["is_section_visible"] = is_section_visible

# Public website pages shown in the CRM sidebar, ordered the way a visitor
# meets them: first the links in the site's own menu, then the pages reached
# from the footer or from links inside other pages. Tools (dashboard, homepage
# rail, visual editor, under construction) stay outside this list.
#
# `menu_label` is the wording the live menu uses, which is not always the CRM's
# name for the page — test_cms_nav keeps the two in step with data/nav.js so
# the CRM cannot drift from the site. `file` is the page it edits, `summary`
# the content that lives on it.
CMS_SITE_PAGES = [
    {
        "endpoint": "homepage", "label": "Homepage", "active": "homepage",
        "icon": "home",
        "file": "Emma Basic Homepage.html",
        "summary": "Hero, additive-free banner, founder story, pack comparison, photo grid, social",
    },
    {
        "endpoint": "catalog", "label": "Our Products", "active": "catalog",
        "menu_label": "Products Without E-Numbers", "icon": "products",
        "file": "Our Products.html",
        "summary": "Every product, its label and nutrition data, and the page header",
    },
    {
        "endpoint": "journal", "label": "Field Notes", "active": "journal",
        "menu_label": "Field Notes", "icon": "journal",
        "file": "Journal.html",
        "summary": "Blog posts, their covers and the page header",
    },
    {
        "endpoint": "people", "label": "People & Places", "active": "people",
        "menu_label": "People", "icon": "people",
        "file": "People & Places.html",
        "summary": "Founder letter, the team, who we are, what we offer, contact",
    },
    {
        "endpoint": "places", "label": "Find us", "active": "places",
        "menu_label": "Find us", "icon": "places",
        "file": "Places.html",
        "summary": "Featured shops, the stockist map, how to order, photo gallery",
    },
    {
        "endpoint": "story", "label": "Our Story", "active": "story",
        "icon": "story",
        "file": "Our Story.html",
        "summary": "Headline and in-the-wild photos",
    },
    {
        "endpoint": "company", "label": "The Basic Ingredients Ltd", "active": "company",
        "icon": "company",
        "file": "The Basic Ingredients.html",
        "summary": "Opening headline, about, contact",
    },
    {
        "endpoint": "matcha", "label": "Matcha Lab", "active": "matcha",
        "icon": "matcha",
        "file": "Matcha Lab.html",
        "summary": "Page header, pouch, USPs, testing, how-to and nutrition",
    },
]
CMS_TOOL_PAGES = [
    {
        "endpoint": "products", "label": "Homepage rail", "active": "products",
        "icon": "rail", "summary": "The featured product rail on the homepage",
    },
    {
        "endpoint": "visual_editor", "label": "Visual editor", "active": "visual",
        "icon": "visual", "summary": "Edit the website by clicking straight on the page",
    },
    {
        "endpoint": "maintenance_page", "label": "Under construction", "active": "maintenance",
        "icon": "maintenance", "summary": "Hide the website behind a holding page",
    },
]
app.jinja_env.globals["cms_site_pages"] = CMS_SITE_PAGES


def cms_assignable_items():
    """Website pages and tools that can sit at the top of the CMS menu or under another page."""
    return list(CMS_SITE_PAGES) + list(CMS_TOOL_PAGES)


def _cms_menu_parents():
    data = load_site()
    menu = data.get("cmsMenu") if isinstance(data.get("cmsMenu"), dict) else {}
    raw = menu.get("parents") if isinstance(menu.get("parents"), dict) else {}
    return {str(key): str(val) for key, val in raw.items() if key and val}


def _cleaned_cms_parents(form):
    """One level of nesting only: a page sits at the top, or directly under a top-level menu."""
    valid = {item["endpoint"] for item in cms_assignable_items()}
    raw = {}
    for item in cms_assignable_items():
        endpoint = item["endpoint"]
        parent = (form.get("parent_" + endpoint) or "").strip()
        if parent in valid and parent != endpoint:
            raw[endpoint] = parent
    nested = set(raw)
    cleaned = {}
    for child, parent in raw.items():
        if parent in nested:
            continue
        cleaned[child] = parent
    return cleaned


def cms_page_groups():
    """Split the page list the way the website is laid out.

    The site's menu carries four links; everything else is reached from the
    footer or from a link inside another page. Grouping the CRM the same way
    means a page here can be matched to a page there without guesswork.
    """
    return [
        {
            "label": "Main menu",
            "hint": "The links visitors see at the top of every page",
            "pages": [p for p in CMS_SITE_PAGES if p.get("menu_label")],
        },
        {
            "label": "Other pages",
            "hint": "Reached from the footer and from links inside other pages",
            "pages": [p for p in CMS_SITE_PAGES if not p.get("menu_label")],
        },
    ]


def cms_sidebar_tree(active=None):
    """Build the CMS sidebar: top-level menus with optional nested pages.

    Nested groups start collapsed. The group that contains the current screen
    is opened so you can still see where you are.
    """
    items = cms_assignable_items()
    valid = {item["endpoint"] for item in items}
    raw = _cms_menu_parents()
    nested = set()
    children_of = {endpoint: [] for endpoint in valid}
    for item in items:
        endpoint = item["endpoint"]
        parent = raw.get(endpoint)
        if parent not in valid or parent == endpoint:
            continue
        if raw.get(parent) in valid:
            continue
        children_of[parent].append(item)
        nested.add(endpoint)

    def nodes_from(source):
        nodes = []
        for item in source:
            if item["endpoint"] in nested:
                continue
            kids = children_of.get(item["endpoint"]) or []
            node = dict(item)
            node["children"] = kids
            acts = [item["active"]] + [kid["active"] for kid in kids]
            node["open"] = bool(active) and active in acts and bool(kids)
            nodes.append(node)
        return nodes

    page_nodes = nodes_from(CMS_SITE_PAGES)
    by_endpoint = {node["endpoint"]: node for node in page_nodes}
    groups = []
    for group in cms_page_groups():
        entry = dict(group)
        entry["nodes"] = [
            by_endpoint[page["endpoint"]]
            for page in group["pages"]
            if page["endpoint"] in by_endpoint
        ]
        groups.append(entry)

    return {
        "pages": page_nodes,
        "tools": nodes_from(CMS_TOOL_PAGES),
        "groups": groups,
    }


app.jinja_env.globals["cms_page_groups"] = cms_page_groups
app.jinja_env.globals["cms_sidebar_tree"] = cms_sidebar_tree


def _cms_menu_blob():
    data = load_site()
    menu = data.get("cmsMenu") if isinstance(data.get("cmsMenu"), dict) else {}
    return data, menu


def _cms_card_homes():
    """Overrides of where an editor card is shown. Missing means its origin page."""
    _data, menu = _cms_menu_blob()
    raw = menu.get("cards") if isinstance(menu.get("cards"), dict) else {}
    valid = {item["endpoint"] for item in cms_assignable_items()}
    homes = {}
    for key, val in raw.items():
        card_id = str(key).strip()
        parent = str(val).strip()
        origin = _cms_card_origin(card_id)
        if not origin or parent not in valid or parent == origin:
            continue
        homes[card_id] = parent
    return homes


def _cms_card_origin(card_id):
    if not card_id or "." not in card_id:
        return ""
    prefix = str(card_id).split(".", 1)[0]
    valid = {item["endpoint"] for item in cms_assignable_items()}
    return prefix if prefix in valid else ""


def _cms_card_host_endpoints():
    return {item["endpoint"] for item in cms_assignable_items()}


def _cleaned_card_home(card_id, parent):
    """Return the endpoint to store, '' to restore the default, or None if invalid."""
    origin = _cms_card_origin(card_id)
    if not origin:
        return None
    valid = _cms_card_host_endpoints()
    parent = (parent or "").strip()
    if not parent or parent == origin:
        return ""
    if parent not in valid:
        return None
    return parent


def _cleaned_card_order_list(ids):
    """Drop blanks, duplicates, and ids that are not card ids (page.section)."""
    if not isinstance(ids, list):
        return []
    seen = set()
    cleaned = []
    for item in ids:
        card_id = str(item).strip()
        if not card_id or card_id in seen:
            continue
        if not _cms_card_origin(card_id):
            continue
        seen.add(card_id)
        cleaned.append(card_id)
    return cleaned


def _cms_card_orders():
    """Per-page editor-card order. Missing page means the template order."""
    _data, menu = _cms_menu_blob()
    raw = menu.get("cardOrder") if isinstance(menu.get("cardOrder"), dict) else {}
    valid = _cms_card_host_endpoints()
    orders = {}
    for key, val in raw.items():
        page = str(key).strip()
        if page not in valid:
            continue
        cleaned = _cleaned_card_order_list(val)
        if cleaned:
            orders[page] = cleaned
    return orders


def _apply_card_order(current_ids, saved_order):
    """Saved ids first (skipping unknown); anything else keeps its relative place at the end."""
    current_ids = list(current_ids)
    if not saved_order:
        return current_ids
    present = set(current_ids)
    ordered = [card_id for card_id in saved_order if card_id in present]
    if not ordered:
        return current_ids
    used = set(ordered)
    rest = [card_id for card_id in current_ids if card_id not in used]
    return ordered + rest


def _cms_menu_payload(parents=None, cards=None, card_order=None):
    _data, menu = _cms_menu_blob()
    if parents is None:
        raw = menu.get("parents") if isinstance(menu.get("parents"), dict) else {}
        parents = {str(k): str(v) for k, v in raw.items() if k and v}
    if cards is None:
        cards = _cms_card_homes()
    if card_order is None:
        card_order = _cms_card_orders()
    payload = {"parents": parents}
    if cards:
        payload["cards"] = cards
    if card_order:
        payload["cardOrder"] = card_order
    return payload


_CARD_ATTR_RE = re.compile(r'\sdata-cms-card="([^"]*)"')
_CONTENT_INNER_RE = re.compile(
    r'<div\s[^>]*class="[^"]*\bcontent-inner\b[^"]*"[^>]*>', re.I
)
_FORM_OPEN_RE = re.compile(r"<form\b", re.I)


def _tag_gt(html, i):
    """Index of '>' closing this start tag, skipping quoted attribute values."""
    n = len(html)
    quote = ""
    while i < n:
        ch = html[i]
        if quote:
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            i += 1
            continue
        if ch == ">":
            return i
        i += 1
    return -1


def _element_span(html, start):
    """Byte span of the element whose start tag begins at `start`."""
    if start < 0 or start >= len(html) or html[start] != "<":
        return None
    m = re.match(r"<(/)?([A-Za-z][A-Za-z0-9:-]*)", html[start:])
    if not m or m.group(1):
        return None
    tag = m.group(2)
    gt = _tag_gt(html, start + m.end())
    if gt < 0:
        return None
    if html[gt - 1] == "/" or tag.lower() in {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }:
        return (start, gt + 1)
    tag_l = tag.lower()
    open_l = "<" + tag_l
    close_l = "</" + tag_l
    depth = 1
    i = gt + 1
    n = len(html)
    while i < n and depth:
        if html.startswith("<!--", i):
            endc = html.find("-->", i + 4)
            i = n if endc < 0 else endc + 3
            continue
        chunk = html[i:i + len(close_l) + 8].lower()
        if chunk.startswith(close_l) and (
            i + len(close_l) >= n or html[i + len(close_l)] in " \t\r\n/>"
        ):
            end_gt = html.find(">", i)
            if end_gt < 0:
                break
            depth -= 1
            i = end_gt + 1
            if depth == 0:
                return (start, i)
            continue
        if chunk.startswith(open_l) and (
            i + len(open_l) < n and html[i + len(open_l)] in " \t\r\n/>"
        ):
            inner_gt = _tag_gt(html, i + len(open_l))
            if inner_gt < 0:
                break
            if html[inner_gt - 1] != "/":
                depth += 1
            i = inner_gt + 1
            continue
        i += 1
    return (start, n)


def _find_cms_cards(html):
    hits = []
    for match in _CARD_ATTR_RE.finditer(html):
        card_id = (match.group(1) or "").strip()
        if not card_id:
            continue
        start = html.rfind("<", 0, match.start())
        span = _element_span(html, start)
        if span:
            hits.append((card_id, span[0], span[1]))
    return hits


def _content_inner_span(html):
    match = _CONTENT_INNER_RE.search(html)
    if not match:
        return None
    return _element_span(html, match.start())


def _enclosing_form_span(html, start, end):
    pos = start
    while True:
        found = None
        for match in _FORM_OPEN_RE.finditer(html[:pos]):
            found = match
        if not found:
            return None
        span = _element_span(html, found.start())
        if span and span[0] <= start and span[1] >= end:
            return span
        pos = found.start()
        if pos <= 0:
            return None


def _start_tag_attrs(html, start):
    gt = html.find(">", start)
    if gt < 0:
        return {}
    parser = HTMLParser()
    attrs = {}

    def grab(tag, tag_attrs):
        attrs.update(tag_attrs)

    parser.handle_starttag = grab
    parser.feed(html[start:gt + 1])
    return dict(attrs)


class _FieldParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = []
        self._textarea = None
        self._select = None
        self._option = None

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        name = data.get("name")
        if tag == "input" and name:
            typ = (data.get("type") or "text").lower()
            if typ in ("file", "submit", "button", "image", "reset"):
                return
            if typ in ("checkbox", "radio") and "checked" not in data:
                return
            value = data.get("value")
            if value is None:
                value = "on" if typ in ("checkbox", "radio") else ""
            self.fields.append((name, value))
        elif tag == "textarea" and name:
            self._textarea = [name, ""]
        elif tag == "select" and name:
            self._select = [name, None, []]
        elif tag == "option" and self._select is not None:
            self._option = [data.get("value"), "selected" in data, ""]

    def handle_data(self, text):
        if self._textarea is not None:
            self._textarea[1] += text
        elif self._option is not None:
            self._option[2] += text

    def handle_endtag(self, tag):
        if tag == "textarea" and self._textarea is not None:
            self.fields.append((self._textarea[0], self._textarea[1]))
            self._textarea = None
        elif tag == "option" and self._option is not None and self._select is not None:
            value, selected, label = self._option
            if value is None:
                value = label
            self._select[2].append((value, selected))
            if selected:
                self._select[1] = value
            self._option = None
        elif tag == "select" and self._select is not None:
            name, chosen, options = self._select
            if chosen is None and options:
                chosen = options[0][0]
            if chosen is not None:
                self.fields.append((name, chosen))
            self._select = None


def _named_fields(fragment):
    parser = _FieldParser()
    try:
        parser.feed(fragment)
        parser.close()
    except Exception:
        return []
    return parser.fields


def _hidden_fields_html(fields):
    parts = []
    for name, value in fields:
        parts.append(
            '<input type="hidden" name="%s" value="%s"/>'
            % (html_escape(name, quote=True), html_escape(value or "", quote=True))
        )
    return "".join(parts)


def _ensure_card_dom_id(card_html, card_id):
    gt = card_html.find(">")
    if gt < 0:
        return card_html
    head = card_html[:gt]
    if re.search(r"\sid=", head):
        return card_html
    slug = card_id.replace(".", "-")
    return head + ' id="%s"' % html_escape(slug, quote=True) + card_html[gt:]


def _form_save_label(form_html, card_start, card_end):
    outside = form_html[:card_start] + form_html[card_end:]
    match = re.search(
        r'<div[^>]*class="[^"]*\bsave-bar\b[^"]*"[^>]*>.*?<button[^>]*>(.*?)</button>',
        outside,
        re.I | re.S,
    )
    if not match:
        return "Save"
    label = re.sub(r"<[^>]+>", "", match.group(1))
    label = re.sub(r"\s+", " ", label).strip()
    return label or "Save"


def _wrap_guest_card(origin_html, card_id, card_start, card_end):
    card_html = _ensure_card_dom_id(origin_html[card_start:card_end], card_id)
    if re.search(r"<form\b", card_html, re.I):
        return card_html
    form_span = _enclosing_form_span(origin_html, card_start, card_end)
    if not form_span:
        return card_html
    form_html = origin_html[form_span[0]:form_span[1]]
    rel_start = card_start - form_span[0]
    rel_end = card_end - form_span[0]
    attrs = _start_tag_attrs(origin_html, form_span[0])
    method = html_escape(attrs.get("method") or "post", quote=True)
    action = html_escape(attrs.get("action") or "", quote=True)
    enctype = attrs.get("enctype") or ""
    extra = ' enctype="%s"' % html_escape(enctype, quote=True) if enctype else ""
    siblings = _named_fields(form_html[:rel_start] + form_html[rel_end:])
    label = html_escape(_form_save_label(form_html, rel_start, rel_end))
    return (
        '<form method="%s" action="%s"%s class="cms-guest-card">'
        "%s%s"
        '<div class="actions-bar save-bar">'
        '<button class="btn" type="submit">%s</button>'
        "</div></form>"
        % (method, action, extra, card_html, _hidden_fields_html(siblings), label)
    )


def _render_origin_html(endpoint):
    cache = getattr(g, "_cms_origin_html", None)
    if cache is None:
        cache = {}
        g._cms_origin_html = cache
    if endpoint in cache:
        return cache[endpoint]
    view = app.view_functions.get(endpoint)
    if view is None:
        cache[endpoint] = ""
        return ""
    try:
        result = view()
    except Exception:
        cache[endpoint] = ""
        return ""
    if isinstance(result, Response):
        html = result.get_data(as_text=True)
    elif isinstance(result, str):
        html = result
    else:
        html = ""
    cache[endpoint] = html
    return html


def _guest_card_html(origin, card_id):
    origin_html = _render_origin_html(origin)
    if not origin_html:
        return ""
    for found_id, start, end in _find_cms_cards(origin_html):
        if found_id == card_id:
            return _wrap_guest_card(origin_html, card_id, start, end)
    return ""


def _relocate_cms_cards_html(html, endpoint, homes):
    inner = _content_inner_span(html)
    if not inner:
        return html
    start, end = inner
    body = html[start:end]
    for card_id, c_start, c_end in reversed(_find_cms_cards(body)):
        origin = _cms_card_origin(card_id)
        home = homes.get(card_id) or origin
        if home == endpoint:
            continue
        hidden = _hidden_fields_html(_named_fields(body[c_start:c_end]))
        body = body[:c_start] + hidden + body[c_end:]
    guests = []
    for card_id, home in homes.items():
        if home != endpoint:
            continue
        origin = _cms_card_origin(card_id)
        if not origin or origin == endpoint:
            continue
        guest = _guest_card_html(origin, card_id)
        if guest:
            guests.append(guest)
    if guests:
        close = body.rfind("</div>")
        if close >= 0:
            body = body[:close] + "\n".join(guests) + "\n" + body[close:]
    return html[:start] + body + html[end:]


def _card_unit_span(html, card_start, card_end):
    """Move a guest form as a whole; otherwise just the card element."""
    form = _enclosing_form_span(html, card_start, card_end)
    if not form:
        return (card_start, card_end)
    classes = (_start_tag_attrs(html, form[0]).get("class") or "").split()
    if "cms-guest-card" in classes:
        return form
    return (card_start, card_end)


def _ensure_form_id(html, start, hint):
    attrs = _start_tag_attrs(html, start)
    existing = (attrs.get("id") or "").strip()
    if existing:
        return html, existing
    fid = hint
    n = 2
    while re.search(r'\sid="%s"' % re.escape(fid), html):
        fid = "%s-%s" % (hint, n)
        n += 1
    gt = _tag_gt(html, start)
    if gt < 0:
        return html, fid
    html = html[:gt] + ' id="%s"' % html_escape(fid, quote=True) + html[gt:]
    return html, fid


def _stamp_form_attr(fragment, form_id):
    """Associate fields with a form they no longer sit inside, skipping nested forms."""
    if not form_id:
        return fragment
    attr = ' form="%s"' % html_escape(form_id, quote=True)
    out = []
    i = 0
    n = len(fragment)
    depth = 0
    while i < n:
        if fragment.startswith("<!--", i):
            endc = fragment.find("-->", i + 4)
            endc = n if endc < 0 else endc + 3
            out.append(fragment[i:endc])
            i = endc
            continue
        if fragment[i] != "<":
            nxt = fragment.find("<", i)
            out.append(fragment[i:] if nxt < 0 else fragment[i:nxt])
            if nxt < 0:
                break
            i = nxt
            continue
        gt = _tag_gt(fragment, i)
        if gt < 0:
            out.append(fragment[i:])
            break
        tag_html = fragment[i:gt + 1]
        match = re.match(r"<(/)?([A-Za-z][A-Za-z0-9:-]*)", tag_html)
        if not match:
            out.append(tag_html)
            i = gt + 1
            continue
        closing = bool(match.group(1))
        name = match.group(2).lower()
        self_close = (not closing) and (
            tag_html.rstrip().endswith("/>") or name in {
                "area", "base", "br", "col", "embed", "hr", "img", "input",
                "link", "meta", "param", "source", "track", "wbr",
            }
        )
        if name == "form":
            if closing:
                depth = max(0, depth - 1)
            elif not self_close:
                depth += 1
            out.append(tag_html)
            i = gt + 1
            continue
        if (
            not closing
            and depth == 0
            and name in ("input", "textarea", "select", "button")
            and not re.search(r"\sform\s*=", tag_html, re.I)
        ):
            if tag_html.rstrip().endswith("/>"):
                tag_html = tag_html.rstrip()[:-2] + attr + "/>"
            else:
                tag_html = tag_html[:-1] + attr + ">"
        out.append(tag_html)
        i = gt + 1
    return "".join(out)


def _after_title_offset(inner_html):
    """Byte index after the heading / subtitle so cards stay below the page title."""
    gt = inner_html.find(">")
    i = 0 if gt < 0 else gt + 1
    last_end = i
    while i < len(inner_html):
        while i < len(inner_html) and inner_html[i] in " \t\r\n":
            i += 1
        if i >= len(inner_html) or inner_html.startswith("</", i) or inner_html[i] != "<":
            break
        span = _element_span(inner_html, i)
        if not span:
            break
        chunk = inner_html[span[0]:span[1]]
        lower = chunk[:200].lower()
        is_title = (
            "<h1" in chunk.lower()
            or lower.startswith("<h1")
            or bool(re.search(r"<p\b[^>]*class=\"[^\"]*\bsub\b", chunk, re.I))
        )
        if not is_title:
            break
        last_end = span[1]
        i = span[1]
    return last_end


def _reorder_cms_cards_html(html, endpoint, saved_order):
    inner = _content_inner_span(html)
    if not inner:
        return html
    start, end = inner
    body = html[start:end]
    hits = _find_cms_cards(body)
    current_ids = [card_id for card_id, _a, _b in hits]
    desired = _apply_card_order(current_ids, saved_order)
    if desired == current_ids:
        return html

    form_starts = []
    for card_id, c_start, c_end in hits:
        form = _enclosing_form_span(body, c_start, c_end)
        if not form:
            continue
        classes = (_start_tag_attrs(body, form[0]).get("class") or "").split()
        if "cms-guest-card" in classes:
            continue
        form_starts.append(form[0])
    for index, form_start in enumerate(sorted(set(form_starts), reverse=True)):
        hint = "cms-form-%s-%s" % (endpoint, index + 1)
        body, _fid = _ensure_form_id(body, form_start, hint)

    hits = _find_cms_cards(body)
    units = {}
    for card_id, c_start, c_end in reversed(hits):
        unit_start, unit_end = _card_unit_span(body, c_start, c_end)
        fragment = body[unit_start:unit_end]
        form = _enclosing_form_span(body, c_start, c_end)
        if form:
            attrs = _start_tag_attrs(body, form[0])
            classes = (attrs.get("class") or "").split()
            fid = (attrs.get("id") or "").strip()
            if "cms-guest-card" not in classes and fid:
                fragment = _stamp_form_attr(fragment, fid)
        units[card_id] = fragment
        body = body[:unit_start] + body[unit_end:]

    stacked = "\n".join(units[card_id] for card_id in desired if card_id in units)
    insert_at = _after_title_offset(body)
    body = body[:insert_at] + "\n" + stacked + "\n" + body[insert_at:]
    return html[:start] + body + html[end:]


@app.after_request
def _relocate_editor_cards(response):
    if request.method != "GET":
        return response
    endpoint = request.endpoint
    if not endpoint or endpoint not in _cms_card_host_endpoints():
        return response
    if "html" not in (response.content_type or ""):
        return response
    homes = _cms_card_homes()
    order = (_cms_card_orders().get(endpoint) or [])
    if not homes and not order:
        return response
    html = response.get_data(as_text=True)
    relocated = html
    if homes:
        relocated = _relocate_cms_cards_html(relocated, endpoint, homes)
    if order:
        relocated = _reorder_cms_cards_html(relocated, endpoint, order)
    if relocated != html:
        response.set_data(relocated)
    return response


@app.context_processor
def _inject_cms_card_ui():
    if _auth_required() and not session.get("cms_auth"):
        return {"cms_card_menus": [], "cms_card_homes": {}, "cms_card_page": ""}
    endpoint = request.endpoint or ""
    return {
        "cms_card_menus": [
            {"endpoint": item["endpoint"], "label": item["label"]}
            for item in cms_assignable_items()
        ],
        "cms_card_homes": _cms_card_homes(),
        "cms_card_page": endpoint,
    }


# Scalar text fields exposed by the bulk table editor (catalog_table.html).
# Kept here so the columns rendered by the template and the fields parsed by
# catalog_table_save stay perfectly in sync. Complex/nested fields (images,
# nutrition, education, qa, badges, pairings, displayMode, imageScale, …) are
# intentionally left to the full per-product editor.
CATALOG_TABLE_TEXT_FIELDS = [
    ("name", "Name"),
    ("japanese", "Japanese"),
    ("origin", "Origin line"),
    ("tagline", "Tagline"),
    ("amazon", "Amazon URL"),
    ("ingredients", "Ingredients"),
    ("allergens", "Allergens"),
]

# List-of-strings fields exposed as one-item-per-line textareas in the bulk
# table. Both round-trip via lines_to_list / '\n'.join exactly like the full
# per-product editor, so plain-string lists stay plain-string lists.
CATALOG_TABLE_LIST_FIELDS = [
    ("sellingPoints", "Selling points"),
    ("badges", "Badges"),
]


NUTRITION_KEYS = [
    ("energy_kj", "Energy (kJ)"),
    ("energy_kcal", "Energy (kcal)"),
    ("fat", "Fat (g)"),
    ("saturates", "Saturates (g)"),
    ("carbohydrate", "Carbohydrate (g)"),
    ("sugars", "Sugars (g)"),
    ("fibre", "Fibre (g)"),
    ("protein", "Protein (g)"),
    ("salt", "Salt (g)"),
]


def _human_kb(num_bytes):
    return "%.0f KB" % (num_bytes / 1024.0) if num_bytes < 1024 * 1024 \
        else "%.1f MB" % (num_bytes / (1024.0 * 1024.0))


def trim_uniform_border(img):
    """Crop a flat near-white margin off all four edges of an image.

    Requires every edge to carry the same margin so that a photograph which
    merely opens onto a bright sky or wall is left untouched.
    """
    rgb = img.convert("RGB")
    w, h = rgb.size
    if w < 8 or h < 8:
        return img

    px = rgb.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    if any(min(c) < BORDER_TRIM_MIN_LIGHTNESS for c in corners):
        return img

    ref = corners[0]

    def matches(pixel):
        return max(abs(a - b) for a, b in zip(pixel, ref)) <= BORDER_TRIM_TOLERANCE

    if not all(matches(c) for c in corners[1:]):
        return img

    step_x = max(1, w // 256)
    step_y = max(1, h // 256)
    limit_x = int(w * BORDER_TRIM_MAX_FRACTION)
    limit_y = int(h * BORDER_TRIM_MAX_FRACTION)

    def row_is_margin(y):
        return all(matches(px[x, y]) for x in range(0, w, step_x))

    def col_is_margin(x):
        return all(matches(px[x, y]) for y in range(0, h, step_y))

    top = 0
    while top < limit_y and row_is_margin(top):
        top += 1
    bottom = 0
    while bottom < limit_y and row_is_margin(h - 1 - bottom):
        bottom += 1
    left = 0
    while left < limit_x and col_is_margin(left):
        left += 1
    right = 0
    while right < limit_x and col_is_margin(w - 1 - right):
        right += 1

    def line_has_content(samples):
        off = sum(1 for p in samples if not matches(p))
        return off >= max(1, int(len(samples) * BORDER_TRIM_EDGE_CONTENT))

    def row_has_content(y):
        return line_has_content([px[x, y] for x in range(0, w, step_x)])

    def col_has_content(x):
        return line_has_content([px[x, y] for y in range(0, h, step_y)])

    def is_padding(near, far, extent):
        if min(near, far) < extent * BORDER_TRIM_MIN_FRACTION:
            return False
        # Padding is applied evenly; an organic bright edge is not.
        return abs(near - far) <= max(2, BORDER_TRIM_SYMMETRY * max(near, far))

    # Deliberate padding arrives as a matched pair of opposite margins:
    # letterboxed (top and bottom), pillarboxed (left and right), or a full
    # frame. A single bright edge belongs to the photograph, so keep it.
    #
    # Padding also butts straight onto the photo, so the first line inside it
    # carries real content. A portrait shot on a white studio backdrop fades
    # in instead, leaving that line still almost blank — trimming there would
    # eat the backdrop and crop into the subject, so both boundaries have to
    # look like a hard edge before anything is removed.
    vertical = (
        is_padding(top, bottom, h)
        and row_has_content(top)
        and row_has_content(h - 1 - bottom)
    )
    horizontal = (
        is_padding(left, right, w)
        and col_has_content(left)
        and col_has_content(w - 1 - right)
    )
    if not vertical and not horizontal:
        return img
    if not vertical:
        top = bottom = 0
    if not horizontal:
        left = right = 0

    return img.crop((left, top, w - right, h - bottom))


def optimize_image_bytes(raw, ext):
    """Resize/recompress image bytes to reduce file size.

    Returns (optimized_bytes, info). Safely returns the original bytes for
    vector/unsupported formats (e.g. SVG) or on any error.
    """
    info = {"optimized": False}
    if not HAVE_PIL:
        return raw, info
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        return raw, info  # not a raster image Pillow understands — leave as-is

    info["dims_before"] = "%d×%d" % img.size
    img = ImageOps.exif_transpose(img)  # honour phone orientation
    size_before_trim = img.size
    img = trim_uniform_border(img)
    trimmed = img.size != size_before_trim
    resized = False
    if max(img.size) > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM))
        resized = True

    out = io.BytesIO()
    try:
        if ext in (".jpg", ".jpeg"):
            img.convert("RGB").save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        elif ext == ".png":
            img.save(out, format="PNG", optimize=True)
        elif ext == ".webp":
            img.save(out, format="WEBP", quality=WEBP_QUALITY, method=6)
        else:
            # gif or other — only rewrite if we actually changed the pixels
            if not resized and not trimmed:
                return raw, info
            img.save(out)
        info["optimized"] = True
        info["dims_after"] = "%d×%d" % img.size
        return out.getvalue(), info
    except Exception:
        return raw, info


def save_upload(file_storage):
    """Stage + optimize an uploaded image; return its web path (or None)."""
    result = save_upload_detailed(file_storage)
    return result["path"] if result else None


def save_upload_detailed(file_storage):
    """Optimize an uploaded image and stage it under assets/uploads for the
    current request. Returns a dict with the web path and before/after sizes.

    The bytes are committed/written by the next save_data (form saves) or
    flushed immediately by /api/upload."""
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Unsupported image type: %s" % ext)
    raw = file_storage.read()
    orig_bytes = len(raw)
    data, opt = optimize_image_bytes(raw, ext)
    new_bytes = len(data)

    base = secure_filename(os.path.splitext(file_storage.filename)[0]) or "image"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = "{base}-{stamp}{ext}".format(base=base, stamp=stamp, ext=ext)
    _stage_file(PROJECT_REL + "/assets/uploads/" + name, data)

    web_path = "assets/uploads/" + name
    return {
        "path": web_path,
        "preview_url": url_for("site_assets", filename="uploads/" + name),
        "orig_bytes": orig_bytes,
        "new_bytes": new_bytes,
        "orig_kb": _human_kb(orig_bytes),
        "new_kb": _human_kb(new_bytes),
        "optimized": opt.get("optimized", False),
        "dims_before": opt.get("dims_before"),
        "dims_after": opt.get("dims_after"),
    }


def resolve_image(form_key, existing=""):
    """Given a form, prefer an uploaded file, else the text path field."""
    upload = request.files.get(form_key + "_file")
    if upload and upload.filename:
        return save_upload(upload)
    return request.form.get(form_key, existing).strip()


def image_file_size(web_path):
    """Return a human-readable file size for a site image path (or None)."""
    if not web_path:
        return None
    rel = PROJECT_REL + "/" + web_path.strip().lstrip("/")
    size = storage.get_size(rel)
    return _human_kb(size) if isinstance(size, int) else None


def gallery_with_sizes(product):
    """Build the gallery list [{path, size}] for a catalog product."""
    return [{"path": img, "size": image_file_size(img)}
            for img in (product.get("images") or [])]


# ---------------------------------------------------------------------------
# Routes — dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", git=git_status_summary())


# Serve the site's assets so image previews work inside the CMS. On the GitHub
# backend there is no local assets folder, so we proxy the bytes from the repo
# (works for private repos too, since the API call is authenticated).
@app.route("/site-assets/<path:filename>")
def site_assets(filename):
    if storage.is_github():
        data = storage.read_bytes(PROJECT_REL + "/assets/" + filename)
        if data is None:
            abort(404)
        ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        resp = Response(data, mimetype=ctype)
        resp.headers["Cache-Control"] = "private, max-age=60"
        return resp
    return send_from_directory(ASSETS_DIR, filename)


# Drag-and-drop / AJAX image upload. Saves + optimizes and returns JSON so the
# form field and preview can update instantly without a page reload.
@app.route("/api/upload", methods=["POST"])
def api_upload():
    file_storage = request.files.get("file")
    if not file_storage or not file_storage.filename:
        return jsonify({"ok": False, "error": "No file received."}), 400
    try:
        result = save_upload_detailed(file_storage)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover
        return jsonify({"ok": False, "error": "Upload failed: %s" % exc}), 500

    # A drag-and-drop upload isn't followed by a form save, so persist the
    # staged image immediately (a single commit on the GitHub backend).
    try:
        storage.persist(_drain_staged_files(), message="CMS: upload %s" % result["path"])
    except Exception as exc:  # pragma: no cover
        return jsonify({"ok": False, "error": "Save failed: %s" % exc}), 500

    if result["optimized"] and result["new_bytes"] < result["orig_bytes"]:
        saved = 100 - (result["new_bytes"] * 100 // max(1, result["orig_bytes"]))
        dims = ""
        if result.get("dims_before") and result.get("dims_after") and result["dims_before"] != result["dims_after"]:
            dims = " · %s → %s" % (result["dims_before"], result["dims_after"])
        result["message"] = "Optimized: %s → %s (%d%% smaller)%s" % (
            result["orig_kb"], result["new_kb"], saved, dims,
        )
    else:
        result["message"] = "Uploaded (%s)" % result["new_kb"]
    result["ok"] = True
    return jsonify(result)


# ---------------------------------------------------------------------------
# Routes — products
# ---------------------------------------------------------------------------
@app.route("/products")
def products():
    home = load_data("homepage")
    return render_template(
        "products.html",
        products=load_data("products"),
        rail=(home.get("productRail") or {}),
    )


@app.route("/products/rail/save", methods=["POST"])
def product_rail_save():
    h = load_data("homepage")
    h.setdefault("productRail", {})["heading"] = request.form.get("rail_heading", "").strip()
    save_data("homepage", h)
    flash("Homepage rail heading saved.", "ok")
    return redirect(url_for("products"))


@app.route("/products/new")
def product_new():
    blank = {
        "id": "", "name": "", "origin": "", "lot": "", "pill": "", "tagline": "",
        "tone": "warm", "image": "", "imagePosition": "", "imageZoom": None,
        "amazon": "", "usps": [], "ingredients": [], "notTested": [],
    }
    return render_template("product_edit.html", p=blank, index=-1, is_new=True)


@app.route("/products/<int:index>")
def product_edit(index):
    items = load_data("products")
    if index < 0 or index >= len(items):
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    return render_template("product_edit.html", p=items[index], index=index, is_new=False)


@app.route("/products/save", methods=["POST"])
def product_save():
    items = load_data("products")
    index = int(request.form.get("index", "-1"))
    is_new = request.form.get("is_new") == "1"

    existing = {} if is_new else items[index]
    zoom_raw = request.form.get("imageZoom", "").strip()
    try:
        zoom = float(zoom_raw) if zoom_raw else None
    except ValueError:
        zoom = None
    pill = request.form.get("pill", "").strip()

    prod = {
        "id": request.form.get("id", "").strip(),
        "name": request.form.get("name", "").strip(),
        "origin": request.form.get("origin", "").strip(),
        "lot": request.form.get("lot", "").strip(),
        "pill": pill if pill else None,
        "tagline": request.form.get("tagline", "").strip(),
        "tone": request.form.get("tone", "warm").strip(),
        "image": resolve_image("image", existing.get("image", "")),
        "imagePosition": request.form.get("imagePosition", "").strip(),
        "imageZoom": zoom,
        "amazon": request.form.get("amazon", "").strip(),
        "usps": lines_to_list(request.form.get("usps", "")),
        "ingredients": lines_to_list(request.form.get("ingredients", "")),
        "notTested": lines_to_list(request.form.get("notTested", "")),
    }

    if not prod["id"] or not prod["name"]:
        flash("Product needs at least an id and a name.", "error")
        return redirect(request.referrer or url_for("products"))

    if is_new:
        items.append(prod)
    else:
        items[index] = prod
    save_data("products", items)
    flash("Saved product: %s" % prod["name"], "ok")
    return redirect(url_for("products"))


@app.route("/products/<int:index>/delete", methods=["POST"])
def product_delete(index):
    items = load_data("products")
    if 0 <= index < len(items):
        removed = items.pop(index)
        save_data("products", items)
        flash("Deleted product: %s" % removed.get("name", ""), "ok")
    return redirect(url_for("products"))


# ---------------------------------------------------------------------------
# Routes — journal / blog
# ---------------------------------------------------------------------------
@app.route("/journal")
def journal():
    data = load_data("journal")
    return render_template(
        "journal.html",
        posts=data.get("posts", []),
        hero=data.get("hero") or {},
        footer=data.get("footer") or {},
        page_seo=data.get("seo") or {},
    )


@app.route("/journal/hero/save", methods=["POST"])
def journal_hero_save():
    data = load_data("journal")
    _apply_hero_form(data.setdefault("hero", {}))
    _apply_footer_form(data)
    _apply_seo_form(data)
    save_data("journal", data)
    flash("Field Notes headline saved.", "ok")
    return redirect(url_for("journal"))


@app.route("/journal/new")
def journal_new():
    blank_post = {
        "id": "", "category": "Ingredient Stories", "date": "", "title": "",
        "excerpt": "", "image": "", "tone": "warm", "featured": False,
        "author": "",
    }
    blank_article = {
        "category": "Ingredient Stories", "date": "", "readTime": "", "title": "",
        "image": "", "imagePosition": "", "intro": "", "body": [],
        "author": "",
    }
    return render_template(
        "journal_edit.html", post=blank_post, article=blank_article,
        body_text="", index=-1, is_new=True,
    )


@app.route("/journal/<int:index>")
def journal_edit(index):
    data = load_data("journal")
    posts = data.get("posts", [])
    if index < 0 or index >= len(posts):
        flash("Post not found.", "error")
        return redirect(url_for("journal"))
    post = posts[index]
    article = data.get("articles", {}).get(post["id"], {
        "category": post.get("category", ""), "date": post.get("date", ""),
        "readTime": "", "title": post.get("title", ""), "image": post.get("image", ""),
        "imagePosition": "", "intro": "", "body": [],
        "author": post.get("author", ""),
    })
    return render_template(
        "journal_edit.html", post=post, article=article,
        body_text=body_to_text(article.get("body", [])), index=index, is_new=False,
    )


@app.route("/journal/save", methods=["POST"])
def journal_save():
    data = load_data("journal")
    posts = data.get("posts", [])
    articles = data.get("articles", {})
    index = int(request.form.get("index", "-1"))
    is_new = request.form.get("is_new") == "1"

    old_id = request.form.get("old_id", "").strip()
    existing_article = articles.get(old_id, {}) if old_id else {}
    existing_post = {} if is_new else (posts[index] if 0 <= index < len(posts) else {})

    post_id = request.form.get("id", "").strip()
    image = resolve_image("image", existing_post.get("image", ""))

    post = {
        "id": post_id,
        "category": request.form.get("category", "").strip(),
        "date": request.form.get("date", "").strip(),
        "title": request.form.get("title", "").strip(),
        "author": request.form.get("author", "").strip(),
        "excerpt": request.form.get("excerpt", "").strip(),
        "image": image,
        "tone": request.form.get("tone", "warm").strip(),
        "featured": request.form.get("featured") == "on",
    }
    if existing_post.get("seo"):
        post["seo"] = dict(existing_post["seo"])
    _apply_seo_form(post)

    article = {
        "category": post["category"],
        "date": post["date"],
        "readTime": request.form.get("readTime", "").strip(),
        "title": request.form.get("article_title", "").strip() or post["title"],
        "image": resolve_image("article_image", existing_article.get("image", "")) or image,
        "imagePosition": request.form.get("imagePosition", "").strip(),
        "intro": request.form.get("intro", "").strip(),
        "body": text_to_body(request.form.get("body", "")),
        "author": post["author"],
    }

    if not post_id or not post["title"]:
        flash("Post needs at least an id and a title.", "error")
        return redirect(request.referrer or url_for("journal"))

    # If featured, unset featured on all others
    if post["featured"]:
        for p in posts:
            p["featured"] = False

    if is_new:
        insert_post_by_date(posts, post)
    else:
        posts[index] = post
        # id may have changed — drop the old article key
        if old_id and old_id != post_id and old_id in articles:
            articles.pop(old_id)
    articles[post_id] = article

    data["posts"] = posts
    data["articles"] = articles
    save_data("journal", data)
    flash("Saved post: %s" % post["title"], "ok")
    return redirect(url_for("journal"))


@app.route("/journal/<int:index>/delete", methods=["POST"])
def journal_delete(index):
    data = load_data("journal")
    posts = data.get("posts", [])
    if 0 <= index < len(posts):
        removed = posts.pop(index)
        data.get("articles", {}).pop(removed.get("id", ""), None)
        data["posts"] = posts
        save_data("journal", data)
        flash("Deleted post: %s" % removed.get("title", ""), "ok")
    return redirect(url_for("journal"))


@app.route("/journal/reorder", methods=["POST"])
def journal_reorder():
    """Persist a drag-and-drop reorder of Field Notes posts."""
    payload = request.get_json(silent=True) or {}
    order = payload.get("order")
    data = load_data("journal")
    posts = data.get("posts") or []
    try:
        data["posts"] = reorder_by_index(posts, order)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    save_data("journal", data)
    flash("Reordered Field Notes.", "ok")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Routes — homepage
# ---------------------------------------------------------------------------
@app.route("/homepage")
def homepage():
    return render_template(
        "homepage.html",
        h=load_data("homepage"),
        site_footer=site_footer_for_editor(),
        nav=load_data("nav"),
    )


@app.route("/homepage/save", methods=["POST"])
def homepage_save():
    h = load_data("homepage")

    hero = h.setdefault("hero", {})
    hero["image"] = resolve_image("hero_image", hero.get("image", ""))
    hero["headlineLine1"] = request.form.get("hero_headlineLine1", "").strip()
    hero["headlineLine2"] = request.form.get("hero_headlineLine2", "").strip()
    hero["body"] = request.form.get("hero_body", "").strip()
    _apply_hero_buttons_form(hero)
    hero["visible"] = form_checkbox("hero_visible")
    _apply_footer_form(h)

    banner = h.setdefault("banner", {})
    banner["text"] = request.form.get("banner_text", "").strip()
    banner["tag"] = request.form.get("banner_tag", "").strip()

    founder = h.setdefault("founder", {})
    founder["image"] = resolve_image("founder_image", founder.get("image", ""))
    founder["introLine"] = request.form.get("founder_introLine", "").strip()
    founder["paragraphs"] = text_to_paras(request.form.get("founder_paragraphs", ""))

    shelf = h.setdefault("shelfTest", {})
    shelf["headingLine1"] = request.form.get("shelf_headingLine1", "").strip()
    shelf["headingLine2"] = request.form.get("shelf_headingLine2", "").strip()
    shelf["subtitle"] = request.form.get("shelf_subtitle", "").strip()
    shelf["theirsLabel"] = (request.form.get("shelf_theirsLabel", "").strip() or "Other Brands")
    shelf["oursLabel"] = (request.form.get("shelf_oursLabel", "").strip() or "Emma Basic")
    shelf["theirs"] = lines_to_list(request.form.get("shelf_theirs", ""))
    shelf["ours"] = lines_to_list(request.form.get("shelf_ours", ""))
    if "shelf_theirsTag" in request.form:
        shelf["theirsTag"] = request.form.get("shelf_theirsTag", "").strip()
    if "shelf_oursTag" in request.form:
        shelf["oursTag"] = request.form.get("shelf_oursTag", "").strip()
    if "shelf_oursSignoff" in request.form:
        shelf["oursSignoff"] = request.form.get("shelf_oursSignoff", "").strip()
    shelf.pop("closingLine1", None)
    shelf.pop("closingLine2", None)

    lifestyle = h.setdefault("lifestyle", {})
    lifestyle["headingLine1"] = request.form.get("life_headingLine1", "").strip()
    lifestyle["headingLine2"] = request.form.get("life_headingLine2", "").strip()
    lifestyle["handle"] = request.form.get("life_handle", "").strip()
    lifestyle["followHref"] = request.form.get("life_followHref", "").strip()
    # Lifestyle tiles. A tile is "present" only if its fields were submitted;
    # removed tiles have no fields in the form and are skipped entirely.
    count = int(request.form.get("tile_count", "0"))
    new_tiles = []
    for i in range(count):
        text_key = "tile%d_image" % i
        file_key = "tile%d_image_file" % i
        has_file = bool(request.files.get(file_key) and request.files.get(file_key).filename)
        if text_key not in request.form and not has_file:
            continue
        label = request.form.get("tile%d_label" % i, "").strip()
        img = resolve_image(text_key, "")
        if not img and not label:
            continue
        new_tiles.append({
            "image": img,
            "label": label,
            "tone": request.form.get("tile%d_tone" % i, "warm").strip(),
            "kind": request.form.get("tile%d_kind" % i, "purity").strip(),
            "span": request.form.get("tile%d_span" % i, "").strip(),
            "position": request.form.get("tile%d_position" % i, "center center").strip() or "center center",
        })
    if new_tiles:
        lifestyle["tiles"] = new_tiles

    social = h.setdefault("social", {})
    social["visible"] = form_checkbox("social_visible")
    social["eyebrow"] = request.form.get("social_eyebrow", "").strip()
    social["headingLine1"] = request.form.get("social_headingLine1", "").strip()
    social["headingLine2"] = request.form.get("social_headingLine2", "").strip()
    social["intro"] = request.form.get("social_intro", "").strip()
    social["instagram"] = {
        "enabled": form_checkbox("social_instagram_enabled"),
        "handle": request.form.get("social_instagram_handle", "").strip(),
        "href": request.form.get("social_instagram_href", "").strip(),
    }
    social["linkedin"] = {
        "enabled": form_checkbox("social_linkedin_enabled"),
        "href": request.form.get("social_linkedin_href", "").strip(),
        "posts": lines_to_list(request.form.get("social_linkedin_posts", "")),
    }
    social["facebook"] = {
        "enabled": form_checkbox("social_facebook_enabled"),
        "href": request.form.get("social_facebook_href", "").strip(),
    }
    social["x"] = {
        "enabled": form_checkbox("social_x_enabled"),
        "href": request.form.get("social_x_href", "").strip(),
    }

    _apply_seo_form(h)
    save_data("homepage", h)
    site = load_site()
    if _apply_site_footer_form(site):
        save_data("site", site)
    flash("Homepage content saved.", "ok")
    return redirect(url_for("homepage"))


@app.route("/nav/save", methods=["POST"])
def nav_save():
    nav = load_data("nav")
    nav["wordmark"] = request.form.get("nav_wordmark", "").strip() or "Emma Basic"
    nav["left"] = _collect_site_footer_links("nav_left")
    nav["right"] = _collect_site_footer_links("nav_right")
    save_data("nav", nav)
    flash("Top menu saved.", "ok")
    return redirect(url_for("homepage"))


# ---------------------------------------------------------------------------
# Routes — People & Places page
# ---------------------------------------------------------------------------
@app.route("/people")
def people():
    return render_template("people.html", d=load_data("people"))


@app.route("/people/save", methods=["POST"])
def people_save():
    d = load_data("people")

    # Hero — same helper as other pages so an unchecked box (omitted from POST)
    # saves visible:false instead of leaving the previous True in place.
    _apply_hero_form(d.setdefault("hero", {}))
    _apply_footer_form(d)

    # Photo + letter under the headline (People page only — not Homepage).
    founder = d.setdefault("founder", {})
    founder["image"] = resolve_image("founder_image", founder.get("image", ""))
    founder["introLine"] = request.form.get("founder_introLine", "").strip()
    founder["paragraphs"] = text_to_paras(request.form.get("founder_paragraphs", ""))
    founder["visible"] = form_checkbox("founder_visible")

    # Team — heading/intro plus a repeatable list of members.
    team = d.setdefault("team", {})
    team["headingLine1"] = request.form.get("team_headingLine1", "").strip()
    team["headingLine2"] = request.form.get("team_headingLine2", "").strip()
    team["intro"] = request.form.get("team_intro", "").strip()
    team["visible"] = form_checkbox("team_visible")
    count = int(request.form.get("member_count", "0"))
    members = []
    for i in range(count):
        if ("member%d_name" % i) not in request.form:
            continue  # removed member — no fields submitted
        name = request.form.get("member%d_name" % i, "").strip()
        image = resolve_image("member%d_image" % i, "")
        if not name and not image:
            continue
        member = {
            "name": name,
            "role": request.form.get("member%d_role" % i, "").strip(),
            "bio": request.form.get("member%d_bio" % i, "").replace("\r\n", "\n").strip(),
            "tone": request.form.get("member%d_tone" % i, "warm").strip(),
            "image": image,
            "image2": resolve_image("member%d_image2" % i, ""),
            "phone": request.form.get("member%d_phone" % i, "").strip(),
        }
        email = request.form.get("member%d_email" % i, "").strip()
        if email:
            member["email"] = email
        position = request.form.get("member%d_imagePosition" % i, "").strip()
        if position:
            member["imagePosition"] = position
        zoom = parse_num(request.form.get("member%d_imageZoom" % i, ""))
        if zoom is not None:
            member["imageZoom"] = zoom
        members.append(member)
    team["members"] = members

    # "Who we are" intro block
    intro = d.setdefault("intro", {})
    intro["heading"] = request.form.get("intro_heading", "").strip()
    intro["headingAccent"] = request.form.get("intro_headingAccent", "").strip()
    intro["paragraphs"] = text_to_paras(request.form.get("intro_paragraphs", ""))
    intro["visible"] = form_checkbox("intro_visible")

    # Services block — repeatable cards.
    services = d.setdefault("services", {})
    services["eyebrow"] = request.form.get("services_eyebrow", "").strip()
    services["heading"] = request.form.get("services_heading", "").strip()
    services["closing"] = request.form.get("services_closing", "").strip()
    services["visible"] = form_checkbox("services_visible")
    card_count = int(request.form.get("card_count", "0"))
    cards = []
    for i in range(card_count):
        if ("card%d_title" % i) not in request.form:
            continue
        title = request.form.get("card%d_title" % i, "").strip()
        body = request.form.get("card%d_body" % i, "").strip()
        if not title and not body:
            continue
        cards.append({"title": title, "body": body})
    services["cards"] = cards

    _apply_contact_form(d.setdefault("contact", {}))
    _apply_seo_form(d)

    save_data("people", d)
    flash("People & Places content saved.", "ok")
    return redirect(url_for("people"))


@app.route("/people/reorder", methods=["POST"])
def people_reorder():
    """Persist a drag-and-drop reorder of team members on the People page."""
    payload = request.get_json(silent=True) or {}
    order = payload.get("order")
    data = load_data("people")
    team = data.setdefault("team", {})
    members = team.get("members") or []
    try:
        team["members"] = reorder_by_index(members, order)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}, 400
    save_data("people", data)
    flash("Reordered the team.", "ok")
    return {"ok": True}


def _apply_trade_form(trade):
    """Write How-to-order fields from the current request onto `trade`.

    Existing PDF form links are preserved by position (they aren't editable
    in the CMS).
    """
    trade["eyebrow"] = request.form.get("trade_eyebrow", "").strip()
    trade["heading"] = request.form.get("trade_heading", "").strip()
    trade["intro"] = request.form.get("trade_intro", "").strip()
    trade["visible"] = form_checkbox("trade_visible")
    old_items = trade.get("items", [])
    item_count = int(request.form.get("trade_count", "0"))
    items = []
    for i in range(item_count):
        if ("trade%d_q" % i) not in request.form:
            continue
        q = request.form.get("trade%d_q" % i, "").strip()
        a = request.form.get("trade%d_a" % i, "").strip()
        if not q and not a:
            continue
        item = dict(old_items[i]) if i < len(old_items) else {}
        item["q"] = q
        item["a"] = a
        items.append(item)
    trade["items"] = items


def _apply_contact_form(contact):
    """Write shared contact-block fields from the current request."""
    contact["headingLine1"] = request.form.get("contact_headingLine1", "").strip()
    contact["headingLine2"] = request.form.get("contact_headingLine2", "").strip()
    contact["body"] = request.form.get("contact_body", "").strip()
    contact["visible"] = form_checkbox("contact_visible")
    contact["regionLabel"] = request.form.get("contact_regionLabel", "").strip()
    contact["addressLine1"] = request.form.get("contact_addressLine1", "").strip()
    contact["addressLine2"] = request.form.get("contact_addressLine2", "").strip()
    contact["email"] = request.form.get("contact_email", "").strip()
    contact["note"] = request.form.get("contact_note", "").strip()


@app.route("/distributor")
def distributor():
    """Old address. How to order now lives on Find us, under the shop list."""
    return redirect(url_for("places") + "#how-to-order")


@app.route("/distributor/save", methods=["POST"])
def distributor_save():
    """Save the How to Place Your First Order sheet (not People contact)."""
    d = load_data("people")
    dist = d.setdefault("distributor", {})
    dist["title"] = request.form.get("banner_title", "").strip()
    dist["email"] = request.form.get("banner_email", "").strip()
    dist["visible"] = form_checkbox("hero_visible")

    old_steps = dist.get("steps") or []
    count = int(request.form.get("step_count", "0") or "0")
    steps = []
    for i in range(count):
        if ("step%d_title" % i) not in request.form and ("step%d_number" % i) not in request.form:
            continue
        title = request.form.get("step%d_title" % i, "").strip()
        number = request.form.get("step%d_number" % i, "").strip()
        icon = request.form.get("step%d_icon" % i, "").strip()
        bullets = _form_lines("step%d_bullets" % i)
        if not title and not number and not icon and not bullets:
            continue
        prev = dict(old_steps[i]) if i < len(old_steps) else {}
        prev.update({
            "icon": icon,
            "number": number,
            "title": title,
            "bullets": bullets,
            "visible": form_checkbox("step%d_visible" % i),
        })
        steps.append(prev)
    dist["steps"] = steps

    other = dist.setdefault("otherWays", {})
    other["heading"] = request.form.get("other_heading", "").strip()
    other["visible"] = form_checkbox("other_visible")
    collect = other.setdefault("collect", {})
    collect["title"] = request.form.get("collect_title", "").strip()
    collect["lines"] = _form_lines("collect_lines", keep_blank=True)
    own = other.setdefault("ownDistributor", {})
    own["title"] = request.form.get("own_title", "").strip()
    own["lines"] = _form_lines("own_lines", keep_blank=True)

    sheet = dist.setdefault("sheetFooter", {})
    sheet["text"] = request.form.get("sheet_footer_text", "").strip()
    sheet["visible"] = form_checkbox("sheet_footer_visible")

    _apply_footer_form(d, "distributorFooter")
    _apply_seo_form(d.setdefault("distributor", {}))
    save_data("people", d)
    flash("How to order saved.", "ok")
    return redirect(url_for("places") + "#how-to-order")


def _apply_hero_form(hero):
    hero["eyebrow"] = request.form.get("hero_eyebrow", "").strip()
    hero["title"] = request.form.get("hero_title", "").strip()
    hero["titleItalic"] = request.form.get("hero_titleItalic", "").strip()
    hero["subtitle"] = request.form.get("hero_subtitle", "").strip()
    hero["visible"] = form_checkbox("hero_visible")


SITE_FOOTER_BLOCK_IDS = (
    "contact",
    "email",
    "london",
    "rotterdam",
    "wordmark",
    "browse",
    "company",
    "legal",
)

SITE_FOOTER_DEFAULTS = {
    "contactHeading": "Get in touch",
    "contactBody": (
        "If any Emma Basic product does not live up to your expectations, "
        "reach out and we will make every effort to arrange a replacement or refund."
    ),
    "emailLabel": "Email",
    "email": "Boris@thebasicingredients.com",
    "londonHeading": "London",
    "londonLines": [
        "The Basic Ingredients Ltd",
        "4 New Concordia Wharf",
        "Mill Street",
        "London SE1 2BB",
    ],
    "rotterdamHeading": "Rotterdam",
    "rotterdamLines": [
        "The Basic Ingredients B.V.",
        "Westplein 12–14",
        "3016BM Rotterdam",
        "The Netherlands",
    ],
    "wordmark": "Emma\nBasic.",
    "browseHeading": "Browse",
    "browseLinks": [
        {"label": "Matcha", "href": "Our Products.html#cat-matcha"},
        {"label": "Oils", "href": "Our Products.html#cat-oils"},
        {"label": "Pantry", "href": "Our Products.html#cat-pantry"},
        {"label": "Full Collection", "href": "Our Products.html"},
    ],
    "companyHeading": "Company",
    "companyLinks": [
        {"label": "Our Story", "href": "Our Story.html"},
        {"label": "People & Places", "href": "People%20%26%20Places.html"},
        {"label": "Find us", "href": "Places.html"},
        {"label": "Journal", "href": "Journal.html"},
    ],
    "legalLeft": "© The Basic Ingredients Ltd · MMXXVI",
    "legalCenter": "No Additives. Ever.",
    "legalRight": "London · Rotterdam",
    "blocks": {key: {"visible": True} for key in SITE_FOOTER_BLOCK_IDS},
}


def _site_footer_blocks_from_form():
    return {
        key: {"visible": form_checkbox("site_footer_%s_visible" % key)}
        for key in SITE_FOOTER_BLOCK_IDS
    }


def site_footer_for_editor(site=None):
    """Shared footer copy for the CMS card, filled in from the live defaults."""
    if site is None:
        site = load_site()
    stored = (site or {}).get("footer") if isinstance(site, dict) else None
    merged = json.loads(json.dumps(SITE_FOOTER_DEFAULTS))
    if not isinstance(stored, dict):
        return merged
    for key in SITE_FOOTER_DEFAULTS:
        if key == "blocks":
            continue
        value = stored.get(key)
        if value in (None, "", []):
            continue
        merged[key] = value
    stored_blocks = stored.get("blocks")
    if isinstance(stored_blocks, dict):
        for block_id in SITE_FOOTER_BLOCK_IDS:
            block = stored_blocks.get(block_id)
            if not isinstance(block, dict):
                continue
            merged["blocks"][block_id] = {
                "visible": block.get("visible", True) is not False,
            }
    return merged


def _collect_site_footer_links(prefix):
    items = []
    for i in range(24):
        label_key = "%s%d_label" % (prefix, i)
        href_key = "%s%d_href" % (prefix, i)
        if label_key not in request.form and href_key not in request.form:
            break
        label = request.form.get(label_key, "").strip()
        href = request.form.get(href_key, "").strip()
        if label or href:
            items.append({"label": label, "href": href})
    return items


def _apply_site_footer_form(site):
    """Write shared footer copy from the homepage Page footer card into site.js.

    Older homepage saves omit these fields and must not blank the live footer.
    """
    if (
        "site_footer_contact_body" not in request.form
        and "site_footer_email" not in request.form
    ):
        return False
    wordmark = (request.form.get("site_footer_wordmark", "") or "").replace("\r\n", "\n")
    site["footer"] = {
        "contactHeading": request.form.get("site_footer_contact_heading", "").strip(),
        "contactBody": request.form.get("site_footer_contact_body", "").strip(),
        "emailLabel": request.form.get("site_footer_email_label", "").strip(),
        "email": request.form.get("site_footer_email", "").strip(),
        "londonHeading": request.form.get("site_footer_london_heading", "").strip(),
        "londonLines": _form_lines("site_footer_london_lines"),
        "rotterdamHeading": request.form.get("site_footer_rotterdam_heading", "").strip(),
        "rotterdamLines": _form_lines("site_footer_rotterdam_lines"),
        "wordmark": wordmark.strip(),
        "browseHeading": request.form.get("site_footer_browse_heading", "").strip(),
        "browseLinks": _collect_site_footer_links("site_footer_browse"),
        "companyHeading": request.form.get("site_footer_company_heading", "").strip(),
        "companyLinks": _collect_site_footer_links("site_footer_company"),
        "legalLeft": request.form.get("site_footer_legal_left", "").strip(),
        "legalCenter": request.form.get("site_footer_legal_center", "").strip(),
        "legalRight": request.form.get("site_footer_legal_right", "").strip(),
        "blocks": _site_footer_blocks_from_form(),
    }
    return True


def _apply_footer_form(data, key="footer"):
    """Per-page footer visibility. Unchecked box is omitted from POST → False."""
    data.setdefault(key, {})["visible"] = form_checkbox("footer_visible")


MATCHA_COPY_DEFAULTS = {
    "pouch": {
        "heading": "What's in",
        "headingItalic": "the pouch.",
        "body": (
            "One ingredient: Tencha (green tea). Shade-grown for 25 days before "
            "hand-picking to develop natural sweetness, vibrant green colour and "
            "umami depth. Nothing added before or after milling.\n\n"
            "Longjin 43 and Yabukita cultivars — two varieties selected for their "
            "distinct characters: one brings brightness, the other depth. Together "
            "they make a matcha that works whisked in water, in a latte, or stirred "
            "into baking."
        ),
        "note": "Ingredients — Tencha (green tea). Shade-grown for 25 days prior to harvest.",
    },
    "usps": {
        "heading": "Why this matcha.",
        "headingItalic": "Five things to know.",
        "code": "M002",
        "items": [
            {
                "number": "01",
                "heading": "100% Pure Matcha",
                "body": "Matcha made from Tencha. No additives. No fillers. No added extract. Every batch is tested by accredited laboratories for pesticides and heavy metals.",
            },
            {
                "number": "02",
                "heading": "Made for Lattes and Beyond",
                "body": "Sieve 1–2g of matcha into a cup. Add 40ml warm water (75°C) and whisk until smooth. Enjoy hot or iced with your choice of milk for a latte. Although designed for lattes, it's premium enough to sip neat as a traditional matcha short. Or — if you feel like indulging — use in baking for cakes, cookies, bread and matcha desserts.",
            },
            {
                "number": "03",
                "heading": "25 Days Shaded Pre-Harvest",
                "body": "Made from Longjin 43 and Yabukita tea leaves, carefully shaded for 25 days before hand-picking to develop natural sweetness, vibrant green colour and umami depth.",
            },
            {
                "number": "04",
                "heading": "Sealed for Freshness, Generous Value",
                "body": "Supplied in a multi-layer PET/AL/PE foil pouch — resealable and light-protected to preserve the vibrant green colour, delicate aroma and fresh flavour. 100g delivers approximately 50–100 cups — ideal for daily matcha drinkers.",
            },
            {
                "number": "05",
                "heading": "Naturally Occurring Compounds",
                "body": "Matcha is produced from the leaves of Camellia sinensis and naturally contains catechins (tea polyphenols) and L-theanine, a naturally occurring amino acid.",
            },
        ],
    },
    "testing": {
        "eyebrow": "Batch Testing",
        "heading": "Every batch.",
        "headingItalic": "No exceptions.",
        "body": (
            "Every batch of our matcha is tested by accredited laboratories for "
            "pesticides and heavy metals before it ships. We don't self-certify. "
            "Results are on file and available on request.\n\n"
            "This is the standard we hold ourselves to because it's the standard "
            "we'd want if we were buying."
        ),
        "rows": [
            {"label": "Pesticide residues", "result": "Tested every batch"},
            {"label": "Heavy metals (Pb, Cd, As, Hg)", "result": "Tested every batch"},
            {"label": "Testing standard", "result": "Accredited laboratory"},
            {"label": "Results available", "result": "On request"},
            {"label": "Additives", "result": "None"},
            {"label": "Fillers", "result": "None"},
        ],
    },
    "howTo": {
        "heading": "How to use it.",
        "headingItalic": "Three ways.",
        "methods": [
            {
                "label": "Traditional Short",
                "steps": "Sieve 1–2g matcha into a chawan or small bowl\nAdd 40ml water at 75°C\nWhisk in a W motion until frothy\nDrink immediately",
            },
            {
                "label": "Latte",
                "steps": "Sieve 1–2g matcha into a cup\nAdd 40ml water at 75°C, whisk until smooth\nTop with steamed or cold milk of choice\nIced: pour over ice after whisking",
            },
            {
                "label": "Baking",
                "steps": "Sieve directly into dry ingredients\n1 tsp (2g) per serving for clear colour and flavour\nWorks in cakes, cookies, bread, energy balls\nDoes not require pre-dissolving",
            },
        ],
    },
    "nutrition": {
        "per": "Per 100g",
        "intro": "Matcha is a concentrated whole-leaf powder. A typical serving is 1–2g, making the per-100g figures higher than most food labels. The numbers below are accurate.",
        "allergensLabel": "Allergens",
        "allergens": "Free from all major allergens.",
        "rows": [
            {"label": "Energy", "value": "382 kcal / 1596 kJ"},
            {"label": "Fat", "value": "3.2g"},
            {"label": "of which saturates", "value": "0.8g", "sub": True},
            {"label": "Carbohydrate", "value": "59.8g"},
            {"label": "of which sugars", "value": "2.0g", "sub": True},
            {"label": "Fibre", "value": "35.3g"},
            {"label": "Protein", "value": "27.1g"},
            {"label": "Salt", "value": "0g"},
        ],
    },
}


def matcha_for_editor(data=None):
    """Fill Matcha Lab editor fields from stored JSON, then live defaults."""
    if data is None:
        data = load_data("matcha")
    merged = dict(data or {})
    defaults = json.loads(json.dumps(MATCHA_COPY_DEFAULTS))
    for key, fallback in defaults.items():
        stored = merged.get(key)
        if not isinstance(stored, dict):
            merged[key] = fallback
            continue
        filled = dict(fallback)
        filled.update({k: v for k, v in stored.items() if v not in (None, "", [])})
        merged[key] = filled
    how = merged.get("howTo") or {}
    methods = []
    for method in how.get("methods") or []:
        item = dict(method)
        steps = item.get("steps")
        if isinstance(steps, list):
            item["steps"] = "\n".join(steps)
        methods.append(item)
    if methods:
        how = dict(how)
        how["methods"] = methods
        merged["howTo"] = how
    return merged


def _apply_matcha_copy_form(data):
    """Write Matcha Lab body copy. Older saves omit these fields and must not wipe them."""
    if "pouch_heading" not in request.form and "usp0_heading" not in request.form:
        return
    pouch = data.setdefault("pouch", {})
    pouch["heading"] = request.form.get("pouch_heading", "").strip()
    pouch["headingItalic"] = request.form.get("pouch_headingItalic", "").strip()
    pouch["body"] = request.form.get("pouch_body", "").strip()
    pouch["note"] = request.form.get("pouch_note", "").strip()

    usps = data.setdefault("usps", {})
    usps["heading"] = request.form.get("usps_heading", "").strip()
    usps["headingItalic"] = request.form.get("usps_headingItalic", "").strip()
    usps["code"] = request.form.get("usps_code", "").strip()
    items = []
    for i in range(12):
        heading_key = "usp%d_heading" % i
        if heading_key not in request.form and ("usp%d_body" % i) not in request.form:
            break
        heading = request.form.get(heading_key, "").strip()
        body = request.form.get("usp%d_body" % i, "").strip()
        number = request.form.get("usp%d_number" % i, "").strip()
        if heading or body:
            items.append({"number": number, "heading": heading, "body": body})
    usps["items"] = items

    testing = data.setdefault("testing", {})
    testing["eyebrow"] = request.form.get("testing_eyebrow", "").strip()
    testing["heading"] = request.form.get("testing_heading", "").strip()
    testing["headingItalic"] = request.form.get("testing_headingItalic", "").strip()
    testing["body"] = request.form.get("testing_body", "").strip()
    rows = []
    for i in range(16):
        label_key = "testing%d_label" % i
        if label_key not in request.form and ("testing%d_result" % i) not in request.form:
            break
        label = request.form.get(label_key, "").strip()
        result = request.form.get("testing%d_result" % i, "").strip()
        if label or result:
            rows.append({"label": label, "result": result})
    testing["rows"] = rows

    how = data.setdefault("howTo", {})
    how["heading"] = request.form.get("howto_heading", "").strip()
    how["headingItalic"] = request.form.get("howto_headingItalic", "").strip()
    methods = []
    for i in range(8):
        label_key = "method%d_label" % i
        if label_key not in request.form and ("method%d_steps" % i) not in request.form:
            break
        label = request.form.get(label_key, "").strip()
        steps = request.form.get("method%d_steps" % i, "").strip()
        if label or steps:
            methods.append({"label": label, "steps": lines_to_list(steps)})
    how["methods"] = methods

    nutrition = data.setdefault("nutrition", {})
    nutrition["per"] = request.form.get("nutrition_per", "").strip()
    nutrition["intro"] = request.form.get("nutrition_intro", "").strip()
    nutrition["allergensLabel"] = request.form.get("nutrition_allergens_label", "").strip()
    nutrition["allergens"] = request.form.get("nutrition_allergens", "").strip()
    nrows = []
    for i in range(16):
        label_key = "nutrition%d_label" % i
        if label_key not in request.form and ("nutrition%d_value" % i) not in request.form:
            break
        label = request.form.get(label_key, "").strip()
        value = request.form.get("nutrition%d_value" % i, "").strip()
        if label or value:
            nrows.append({
                "label": label,
                "value": value,
                "sub": form_checkbox("nutrition%d_sub" % i),
            })
    nutrition["rows"] = nrows


def _simple_page_save(key, flash_msg, redirect_endpoint):
    data = load_data(key)
    _apply_hero_form(data.setdefault("hero", {}))
    _apply_footer_form(data)
    _apply_seo_form(data)
    save_data(key, data)
    flash(flash_msg, "ok")
    return redirect(url_for(redirect_endpoint))


@app.route("/places")
def places():
    return render_template(
        "places.html",
        d=load_data("places"),
        order=load_data("people"),
    )


@app.route("/places/save", methods=["POST"])
def places_save():
    d = load_data("places")
    _apply_hero_form(d.setdefault("hero", {}))
    _apply_footer_form(d)
    featured = d.setdefault("featured", {})
    featured["eyebrow"] = request.form.get("featured_eyebrow", "").strip()
    featured["heading"] = request.form.get("featured_heading", "").strip()
    featured["headingItalic"] = request.form.get("featured_headingItalic", "").strip()
    featured["hideHeading"] = form_checkbox("featured_hideHeading")
    # Unchecked boxes are omitted from POST. Missing means show the carousel.
    featured["hidden"] = form_checkbox("featured_hidden")
    old_retailers = featured.get("retailers") or []
    retailers = []
    count = int(request.form.get("retailer_count", "0"))
    for i in range(count):
        if ("retailer%d_name" % i) not in request.form:
            continue
        name = request.form.get("retailer%d_name" % i, "").strip()
        city = request.form.get("retailer%d_city" % i, "").strip()
        url = request.form.get("retailer%d_url" % i, "").strip()
        style = request.form.get("retailer%d_style" % i, "").strip()
        if not name and not city:
            continue
        prev = dict(old_retailers[i]) if i < len(old_retailers) else {}
        prev.update({"name": name, "city": city, "url": url})
        if style:
            prev["style"] = style
        retailers.append(prev)
    featured["retailers"] = retailers

    directory = d.setdefault("directory", {})
    directory["heading"] = request.form.get("directory_heading", "").strip()
    directory["headingItalic"] = request.form.get("directory_headingItalic", "").strip()
    directory["hideHeading"] = form_checkbox("directory_hideHeading")
    directory["missingNote"] = request.form.get("directory_missingNote", "").strip()

    # Headings, carousel, SEO and HQ are one modest form. The stockist
    # directory is saved separately (highlights, or one shop) so this save
    # is not a dump of every address. An older form that still posts
    # shop_count may rewrite the list; a normal save leaves the shops as
    # they are.
    if "shop_count" in request.form:
        _apply_legacy_shop_list(d)
    # Same idea for the photo gallery: only a form that carries its fields
    # may rewrite the album.
    if "gallery_photo_count" in request.form:
        _apply_gallery_form(d)
    _apply_seo_form(d)

    hq = d.setdefault("hq", {})
    hq["label"] = request.form.get("hq_label", "").strip()
    hq["addressLine1"] = request.form.get("hq_addressLine1", "").strip()
    hq["addressLine2"] = request.form.get("hq_addressLine2", "").strip()
    lat = parse_num(request.form.get("hq_lat", ""))
    lng = parse_num(request.form.get("hq_lng", ""))
    if lat is not None:
        hq["lat"] = lat
    if lng is not None:
        hq["lng"] = lng
    save_data("places", d)
    flash("Shops saved.", "ok")
    return redirect(url_for("places"))


def _apply_gallery_form(d):
    """Photo gallery at the foot of the Find us page.

    A photo is "present" only if its fields were submitted; removed photos
    have no fields in the form and are skipped entirely.
    """
    gallery = d.setdefault("gallery", {})
    gallery["heading"] = request.form.get("gallery_heading", "").strip()
    gallery["headingItalic"] = request.form.get("gallery_headingItalic", "").strip()
    gallery["intro"] = request.form.get("gallery_intro", "").strip()
    gallery["hideHeading"] = form_checkbox("gallery_hideHeading")
    gallery["visible"] = form_checkbox("gallery_visible")

    photos = []
    count = int(request.form.get("gallery_photo_count", "0") or "0")
    for i in range(count):
        text_key = "photo%d_image" % i
        upload = request.files.get(text_key + "_file")
        if text_key not in request.form and not (upload and upload.filename):
            continue
        image = resolve_image(text_key, "")
        if not image:
            continue
        photo = {"image": image}
        caption = request.form.get("photo%d_caption" % i, "").strip()
        if caption:
            photo["caption"] = caption
        photos.append(photo)
    gallery["photos"] = photos


def _apply_legacy_shop_list(d):
    """Rewrite the shop list from a form that still posts every stockist.

    Kept so an older cached page, and the spreadsheet hand-edit tests, can
    still save. The live page does not use this shape.
    """
    shops = []
    shop_count = int(request.form.get("shop_count", "0") or "0")
    old_shops = d.get("shops") or []
    for i in range(shop_count):
        if ("shop%d_name" % i) not in request.form:
            continue
        name = request.form.get("shop%d_name" % i, "").strip()
        city = request.form.get("shop%d_city" % i, "").strip()
        address = request.form.get("shop%d_address" % i, "").strip()
        if not name and not address:
            continue
        prev = dict(old_shops[i]) if i < len(old_shops) else {}
        prev.update({"name": name, "city": city, "address": address})
        for field in ("postcode", "url", "phone"):
            key = "shop%d_%s" % (i, field)
            if key not in request.form:
                continue
            value = request.form.get(key, "").strip()
            if field == "postcode":
                value = stockists_import.normalise_postcode(value) or value.upper()
            if value:
                prev[field] = value
            else:
                prev.pop(field, None)
        lat = parse_num(request.form.get("shop%d_lat" % i, ""))
        lng = parse_num(request.form.get("shop%d_lng" % i, ""))
        if lat is not None:
            prev["lat"] = lat
        else:
            prev.pop("lat", None)
        if lng is not None:
            prev["lng"] = lng
        else:
            prev.pop("lng", None)
        if form_checkbox("shop%d_highlight" % i):
            prev["highlight"] = True
        else:
            prev.pop("highlight", None)
        shops.append(prev)
    stockists_import.fill_missing_coordinates(shops)
    d["shops"] = shops


def _merge_shop_from_request(prev, highlight=None):
    """Copy one shop's text fields from the current form onto prev.

    highlight is True, False, or None. None leaves an existing tick alone
    (the box was not part of this save). False clears it.
    """
    prev = dict(prev or {})
    prev["name"] = request.form.get("name", "").strip()
    prev["city"] = request.form.get("city", "").strip()
    prev["address"] = request.form.get("address", "").strip()
    for field in ("postcode", "url", "phone"):
        value = request.form.get(field, "").strip()
        if field == "postcode":
            value = stockists_import.normalise_postcode(value) or value.upper()
        if value:
            prev[field] = value
        else:
            prev.pop(field, None)
    for field in ("lat", "lng"):
        num = parse_num(request.form.get(field, ""))
        if num is not None:
            prev[field] = num
        else:
            prev.pop(field, None)
    if highlight is True:
        prev["highlight"] = True
    elif highlight is False:
        prev.pop("highlight", None)
    return prev


def _shop_index_list(raw_values, limit):
    seen = []
    for raw in raw_values:
        try:
            i = int(str(raw).strip())
        except (TypeError, ValueError):
            continue
        if i < 0 or i >= limit or i in seen:
            continue
        seen.append(i)
    return seen


def _places_shops_or_redirect():
    d = load_data("places")
    shops = d.get("shops") or []
    return d, shops


@app.route("/places/highlights", methods=["POST"])
def places_highlights_save():
    """Save only which shops are highlighted. Body is shop indexes, not addresses."""
    d, shops = _places_shops_or_redirect()
    present = _shop_index_list(request.form.getlist("id"), len(shops))
    if not present:
        flash("Nothing was saved. Refresh the page, tick the shops, and press Save highlights again.", "error")
        return redirect(url_for("places") + "#shops")
    highlighted = set(_shop_index_list(request.form.getlist("on"), len(shops)))
    for i in present:
        if i in highlighted:
            shops[i]["highlight"] = True
        else:
            shops[i].pop("highlight", None)
    d["shops"] = shops
    save_data("places", d)
    flash("Highlights saved. The map will update in a minute or two.", "ok")
    return redirect(url_for("places") + "#shops")


@app.route("/places/shop/add", methods=["POST"])
def places_shop_add():
    d, shops = _places_shops_or_redirect()
    shop = _merge_shop_from_request({}, highlight=form_checkbox("highlight"))
    if not shop.get("name") and not shop.get("address"):
        flash("Add a shop name or address, then press Add stockist.", "error")
        return redirect(url_for("places") + "#add-shop")
    stockists_import.fill_missing_coordinates([shop])
    shops.append(shop)
    d["shops"] = shops
    save_data("places", d)
    flash("Added %s." % (shop.get("name") or "that shop"), "ok")
    return redirect(url_for("places") + "#shop-%d" % (len(shops) - 1))


@app.route("/places/shop/<int:index>", methods=["POST"])
def places_shop_save(index):
    d, shops = _places_shops_or_redirect()
    if index >= len(shops):
        flash("That shop is no longer on the list. Refresh the page and try again.", "error")
        return redirect(url_for("places") + "#shops")
    highlight = None
    if "highlight" in request.form:
        highlight = True if form_checkbox("highlight") else False
    shop = _merge_shop_from_request(shops[index], highlight=highlight)
    if not shop.get("name") and not shop.get("address"):
        flash("A shop needs a name or an address.", "error")
        return redirect(url_for("places") + "#shop-%d" % index)
    stockists_import.fill_missing_coordinates([shop])
    shops[index] = shop
    d["shops"] = shops
    save_data("places", d)
    flash("Saved %s." % (shop.get("name") or "that shop"), "ok")
    return redirect(url_for("places") + "#shop-%d" % index)


@app.route("/places/shop/<int:index>/remove", methods=["POST"])
def places_shop_remove(index):
    d, shops = _places_shops_or_redirect()
    if index >= len(shops):
        flash("That shop is no longer on the list. Refresh the page and try again.", "error")
        return redirect(url_for("places") + "#shops")
    name = shops[index].get("name") or "That shop"
    del shops[index]
    d["shops"] = shops
    save_data("places", d)
    flash("Removed %s." % name, "ok")
    return redirect(url_for("places") + "#shops")


STOCKIST_UPLOAD_MAX_BYTES = 4 * 1024 * 1024


@app.route("/places/import/template")
def places_import_template():
    return Response(
        stockists_import.template_workbook_bytes(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="emma-basic-stockists-template.xlsx"'},
    )


@app.route("/places/import/preview", methods=["POST"])
def places_import_preview():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        flash("Please choose your Excel file first, then press Check my file.", "error")
        return redirect(url_for("places") + "#upload-stockists")
    data = upload.read(STOCKIST_UPLOAD_MAX_BYTES + 1)
    if len(data) > STOCKIST_UPLOAD_MAX_BYTES:
        flash("That file is too big (over 4 MB). Please remove extra sheets or pictures and try again.", "error")
        return redirect(url_for("places") + "#upload-stockists")
    try:
        sheet = stockists_import.read_file(upload.filename, data)
    except stockists_import.StockistFileError as exc:
        flash(str(exc), "error")
        return redirect(url_for("places") + "#upload-stockists")
    if not sheet["rows"]:
        flash("We couldn't find any shops under the headings in that file.", "error")
        return redirect(url_for("places") + "#upload-stockists")
    existing = load_data("places").get("shops") or []
    preview = stockists_import.build_preview(
        existing, sheet["rows"], address_fallback=not sheet["consolidated"])
    ready = []
    for item in preview["items"]:
        if item["shop"]:
            item["index"] = len(ready)
            ready.append(item["shop"])
    return render_template(
        "places_import.html",
        filename=upload.filename,
        preview=preview,
        sheet=sheet,
        payload=json.dumps(ready, ensure_ascii=False),
        existing_count=len(existing),
    )


@app.route("/places/import/confirm", methods=["POST"])
def places_import_confirm():
    try:
        raw = json.loads(request.form.get("payload", ""))
    except ValueError:
        raw = None
    included = {int(i) for i in request.form.getlist("include") if str(i).isdigit()}
    shops = []
    if isinstance(raw, list):
        for idx, item in enumerate(raw):
            shop = stockists_import.clean_payload_shop(item) if idx in included else None
            if shop:
                shops.append(shop)
    if not shops:
        flash("Nothing was saved — no shops were ticked. Please upload the file again and tick the shops to add.", "error")
        return redirect(url_for("places") + "#upload-stockists")
    mode = "replace" if request.form.get("mode") == "replace" else "merge"
    d = load_data("places")
    d["shops"], summary = stockists_import.apply_import(d.get("shops") or [], shops, mode)
    save_data("places", d)
    parts = ["%d new" % summary["new"], "%d updated" % summary["updated"]]
    if summary["unchanged"]:
        parts.append("%d already up to date" % summary["unchanged"])
    if summary["removed"]:
        parts.append("%d removed" % summary["removed"])
    flash("Stockists saved: %s. The website map will update in a minute or two." % ", ".join(parts), "ok")
    return redirect(url_for("places"))


@app.route("/story")
def story():
    d = load_data("story")
    photos = ((d.get("gallery") or {}).get("photos") or [])
    return render_template(
        "simple_page.html",
        page_title="Our Story",
        save_endpoint="story_save",
        visual_page="story",
        active="story",
        d=d,
        gallery_photos=gallery_with_sizes({"images": photos}),
        extra="The founder story below the headline is edited on the Homepage. The photo gallery (The team, in the wild) is further down this page — heading and photos.",
    )


@app.route("/story/save", methods=["POST"])
def story_save():
    data = load_data("story")
    _apply_hero_form(data.setdefault("hero", {}))
    _apply_footer_form(data)
    gallery = data.setdefault("gallery", {})
    gallery["heading"] = request.form.get("gallery_heading", "").strip()
    gallery["headingItalic"] = request.form.get("gallery_headingItalic", "").strip()
    if request.form.get("gallery_photos_editor"):
        gallery["photos"] = [
            pth.strip() for pth in request.form.getlist("gallery_path") if pth.strip()
        ]
    _apply_seo_form(data)
    save_data("story", data)
    flash("Our Story content saved.", "ok")
    return redirect(url_for("story"))


@app.route("/company")
def company():
    return render_template("company.html", d=load_data("company"))


@app.route("/company/save", methods=["POST"])
def company_save():
    d = load_data("company")
    _apply_hero_form(d.setdefault("hero", {}))
    _apply_footer_form(d)
    about = d.setdefault("about", {})
    about["heading"] = request.form.get("about_heading", "").strip()
    about["headingItalic"] = request.form.get("about_headingItalic", "").strip()
    about["body"] = request.form.get("about_body", "").strip()
    about["buttonLabel"] = request.form.get("about_buttonLabel", "").strip()
    about["buttonHref"] = request.form.get("about_buttonHref", "").strip()
    _apply_contact_form(d.setdefault("contact", {}))
    _apply_seo_form(d)
    save_data("company", d)
    flash("The Basic Ingredients content saved.", "ok")
    return redirect(url_for("company"))


def _category_by_id(cat_id):
    for cat in load_catalog_bundle()["categories"]:
        if cat.get("id") == cat_id:
            return cat
    return None


def _category_underlink(cat):
    if not isinstance(cat, dict):
        return {}
    meta = cat.get("meta") if isinstance(cat.get("meta"), dict) else {}
    link = meta.get("link") if isinstance(meta.get("link"), dict) else {}
    return link


@app.route("/matcha")
def matcha():
    matcha_cat = _category_by_id("matcha")
    return render_template(
        "matcha.html",
        page_title="Matcha Lab",
        save_endpoint="matcha_save",
        visual_page="matcha",
        active="matcha",
        d=matcha_for_editor(),
        extra="This is the Matcha Lab landing page (M002). Product details live in Our Products. The link under Matcha on that page is the box below — or edit it on the Matcha product in Our Products.",
        show_category_underlink=True,
        underlink=_category_underlink(matcha_cat),
        underlink_heading="Link under Matcha on Our Products",
        underlink_help="This is the small link under the Matcha product on Our Products. It currently says “Visit the Matcha Lab”. Clear the link text, or tick Hide this link, then save, to take it off the website.",
    )


@app.route("/matcha/save", methods=["POST"])
def matcha_save():
    data = load_data("matcha")
    _apply_hero_form(data.setdefault("hero", {}))
    _apply_footer_form(data)
    _apply_seo_form(data)
    _apply_matcha_copy_form(data)
    save_data("matcha", data)
    if "link_label" in request.form or "link_href" in request.form:
        bundle = load_catalog_bundle()
        for cat in bundle["categories"]:
            if cat.get("id") == "matcha":
                _apply_category_link_form(cat)
                save_data("catalog", bundle)
                break
    flash("Matcha Lab content saved.", "ok")
    return redirect(url_for("matcha"))


# ---------------------------------------------------------------------------
# Routes — under-construction mode
# ---------------------------------------------------------------------------
# Where the website itself is served. Online the CMS and the site are separate
# deployments, so the preview links have to point at the live domain.
LOCAL_SITE_ORIGIN = "http://localhost:8080"
HOMEPAGE_FILE = "Emma%20Basic%20Homepage.html"


def site_base_url():
    return seo.SITE_ORIGIN if storage.is_github() else LOCAL_SITE_ORIGIN


def load_site():
    """Site-wide settings, tolerating a checkout that predates `site.js`.

    A missing or unreadable file must leave the website visible, so it falls
    back to the defaults rather than raising.
    """
    try:
        return load_data("site")
    except Exception:
        return {}


def current_maintenance():
    """The maintenance settings for this request, read at most once."""
    cached = getattr(g, "_maintenance", None)
    if cached is None:
        cached = maintenance.from_data(load_site())
        g._maintenance = cached
    return cached


def _maintenance_links(settings):
    base = site_base_url()
    key = settings.get("previewKey") or ""
    return {
        "notice": "%s/%s?force=1" % (base, maintenance.PAGE_FILE),
        "bypass": "%s/%s?preview=%s" % (base, HOMEPAGE_FILE, key) if key else "",
        "site": "%s/%s" % (base, HOMEPAGE_FILE),
    }


@app.context_processor
def _inject_maintenance():
    """Expose the switch to every CRM page so the banner can warn about it."""
    # Signed-out visitors only see the login screen, which has no banner — and
    # on the GitHub backend the lookup would be a wasted API call.
    if _auth_required() and not session.get("cms_auth"):
        return {"site_maintenance": dict(maintenance.DEFAULTS)}
    return {"site_maintenance": current_maintenance()}


@app.route("/maintenance")
def maintenance_page():
    settings = current_maintenance()
    return render_template(
        "maintenance.html", m=settings, links=_maintenance_links(settings),
    )


@app.route("/maintenance/save", methods=["POST"])
def maintenance_save():
    data = load_site()
    was_enabled = maintenance.is_enabled(data)

    settings = maintenance.from_data(data)
    settings["enabled"] = form_checkbox("maintenance_enabled")
    for field in maintenance.TEXT_FIELDS:
        settings[field] = request.form.get(field, settings.get(field, "")).strip()
    # A pass always exists so the owner is never locked out of their own site.
    if request.form.get("new_preview_key") == "1" or not settings["previewKey"]:
        settings["previewKey"] = maintenance.new_preview_key()

    data["maintenance"] = settings
    save_data("site", data)

    if settings["enabled"] != was_enabled:
        flash(
            "Visitors now see the under construction page."
            if settings["enabled"] else "The website is open to visitors again.",
            "ok",
        )
    else:
        flash("Under construction page saved.", "ok")
    return redirect(url_for("maintenance_page"))


@app.route("/maintenance/off", methods=["POST"])
def maintenance_off():
    """One-click way back for the banner shown on every CRM page."""
    data = load_site()
    if not maintenance.is_enabled(data):
        flash("The website was already open to visitors.", "ok")
        return redirect(request.referrer or url_for("index"))
    settings = maintenance.from_data(data)
    settings["enabled"] = False
    data["maintenance"] = settings
    save_data("site", data)
    flash("The website is open to visitors again.", "ok")
    return redirect(request.referrer or url_for("index"))


@app.route("/cms-menu")
def cms_menu():
    parents = _cms_menu_parents()
    items = cms_assignable_items()
    rows = [{"item": item, "parent": parents.get(item["endpoint"], "")} for item in items]
    return render_template("cms_menu.html", rows=rows, items=items)


@app.route("/cms-menu/save", methods=["POST"])
def cms_menu_save():
    data = load_site()
    if not isinstance(data, dict):
        data = {}
    data["cmsMenu"] = _cms_menu_payload(parents=_cleaned_cms_parents(request.form))
    save_data("site", data)
    flash("CMS menu saved. Nested pages are collapsed until you open them.", "ok")
    return redirect(url_for("cms_menu"))


@app.route("/cms-menu/cards/save", methods=["POST"])
def cms_card_home_save():
    card_id = (request.form.get("card") or "").strip()
    parent = (request.form.get("parent") or "").strip()
    cleaned = _cleaned_card_home(card_id, parent)
    dest = _cms_card_origin(card_id) or "index"
    data = load_site()
    if not isinstance(data, dict):
        data = {}
    cards = dict(_cms_card_homes())
    if cleaned is None:
        flash("That card could not be moved.", "error")
    else:
        if cleaned:
            cards[card_id] = cleaned
            dest = cleaned
        else:
            cards.pop(card_id, None)
        data["cmsMenu"] = _cms_menu_payload(cards=cards)
        save_data("site", data)
        if cleaned:
            flash("Card moved. It now lives on that CRM page.", "ok")
        else:
            flash("Card moved back to its own page.", "ok")
    if dest not in _cms_card_host_endpoints() and dest != "index":
        dest = "index"
    suffix = "#" + card_id.replace(".", "-") if card_id else ""
    return redirect(url_for(dest) + suffix)


@app.route("/cms-menu/cards/order", methods=["POST"])
def cms_card_order_save():
    """Persist a drag-and-drop reorder of editor cards on one CRM page."""
    payload = request.get_json(silent=True) or {}
    page = str(payload.get("page") or "").strip()
    if page not in _cms_card_host_endpoints():
        return {"ok": False, "error": "Unknown page"}, 400
    cleaned = _cleaned_card_order_list(payload.get("order"))
    data = load_site()
    if not isinstance(data, dict):
        data = {}
    orders = dict(_cms_card_orders())
    if cleaned:
        orders[page] = cleaned
    else:
        orders.pop(page, None)
    data["cmsMenu"] = _cms_menu_payload(card_order=orders)
    save_data("site", data)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Routes — product catalog (the full "Our Products" range)
# ---------------------------------------------------------------------------
def _catalog_counts(catalog):
    return sum(len(c.get("products", [])) for c in catalog)


@app.route("/catalog")
def catalog():
    bundle = load_catalog_bundle()
    return render_template(
        "catalog.html",
        catalog=bundle["categories"],
        page_hero=bundle.get("hero") or {},
        page_footer=bundle.get("footer") or {},
        page_seo=bundle.get("seo") or {},
    )


@app.route("/catalog/hero/save", methods=["POST"])
def catalog_hero_save():
    bundle = load_catalog_bundle()
    _apply_hero_form(bundle.setdefault("hero", {}))
    _apply_footer_form(bundle)
    _apply_seo_form(bundle)
    save_data("catalog", bundle)
    flash("Our Products headline saved.", "ok")
    return redirect(url_for("catalog"))


@app.route("/catalog/table")
def catalog_table():
    """Spreadsheet-style editor: every product across every category on one
    page, with a subset of safe scalar text fields editable inline."""
    return render_template(
        "catalog_table.html",
        catalog=load_catalog_bundle()["categories"],
        text_fields=CATALOG_TABLE_TEXT_FIELDS,
        list_fields=CATALOG_TABLE_LIST_FIELDS,
    )


@app.route("/catalog/table/save", methods=["POST"])
def catalog_table_save():
    """Apply inline edits from the bulk table.

    Rows are addressed by `p-<ci>-<pi>-<field>` form names. For each product we
    mutate the existing dict in place, overwriting ONLY the exposed fields
    (CATALOG_TABLE_TEXT_FIELDS + CATALOG_TABLE_LIST_FIELDS) and leaving every
    other key (images, nutrition, education, qa, pairings, displayMode,
    imageScale, …) untouched.
    """
    bundle = load_catalog_bundle()
    cats = bundle["categories"]
    updated = 0
    for ci, cat in enumerate(cats):
        for pi, prod in enumerate(cat.get("products", [])):
            prefix = "p-%d-%d-" % (ci, pi)
            # A row is only present if it was actually rendered/submitted.
            if (prefix + "name") not in request.form:
                continue
            changed = False
            for key, _label in CATALOG_TABLE_TEXT_FIELDS:
                form_key = prefix + key
                if form_key in request.form:
                    new_val = request.form.get(form_key, prod.get(key, "")).strip()
                    if new_val != prod.get(key, ""):
                        changed = True
                    prod[key] = new_val
            for key, _label in CATALOG_TABLE_LIST_FIELDS:
                form_key = prefix + key
                if form_key in request.form:
                    new_val = lines_to_list(request.form.get(form_key, ""))
                    if new_val != prod.get(key):
                        changed = True
                    prod[key] = new_val
            if changed:
                prod["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            updated += 1

    save_data("catalog", bundle)
    flash("Saved %d product%s from the table." % (updated, "" if updated == 1 else "s"), "ok")
    return redirect(url_for("catalog_table"))


@app.route("/catalog/category/new")
def catalog_category_new():
    blank = {"id": "", "number": "", "name": "", "japanese": "", "blurb": ""}
    return render_template("catalog_category_edit.html", c=blank, index=-1, is_new=True)


@app.route("/catalog/category/<int:ci>")
def catalog_category_edit(ci):
    cats = load_catalog_bundle()["categories"]
    if ci < 0 or ci >= len(cats):
        flash("Category not found.", "error")
        return redirect(url_for("catalog"))
    return render_template("catalog_category_edit.html", c=cats[ci], index=ci, is_new=False)


@app.route("/catalog/category/save", methods=["POST"])
def catalog_category_save():
    bundle = load_catalog_bundle()
    cats = bundle["categories"]
    index = int(request.form.get("index", "-1"))
    is_new = request.form.get("is_new") == "1"

    existing = {} if is_new else (cats[index] if 0 <= index < len(cats) else {})
    cat = dict(existing)  # preserve products, meta, and any extra fields
    cat["id"] = request.form.get("id", "").strip()
    cat["number"] = request.form.get("number", "").strip()
    cat["name"] = request.form.get("name", "").strip()
    cat["japanese"] = request.form.get("japanese", "").strip()
    cat["blurb"] = request.form.get("blurb", "").strip()
    cat.setdefault("products", [])
    _apply_category_link_form(cat)

    if not cat["id"] or not cat["name"]:
        flash("A category needs at least an id and a name.", "error")
        return redirect(request.referrer or url_for("catalog"))

    if is_new:
        cats.append(cat)
    else:
        cats[index] = cat
    save_data("catalog", bundle)
    flash("Saved category: %s" % cat["name"], "ok")
    return redirect(url_for("catalog"))


@app.route("/catalog/category/<int:ci>/delete", methods=["POST"])
def catalog_category_delete(ci):
    bundle = load_catalog_bundle()
    cats = bundle["categories"]
    if 0 <= ci < len(cats):
        removed = cats.pop(ci)
        save_data("catalog", bundle)
        flash("Deleted category: %s (and its %d products)"
              % (removed.get("name", ""), len(removed.get("products", []))), "ok")
    return redirect(url_for("catalog"))


@app.route("/catalog/product/new")
def catalog_product_new():
    cats = load_catalog_bundle()["categories"]
    ci = int(request.args.get("cat", "0"))
    blank = {
        "id": "", "name": "", "japanese": "", "origin": "", "tone": "warm",
        "tagline": "", "amazon": "", "image": "", "images": [],
        "badges": [], "pairings": [], "sellingPoints": [],
        "ingredients": "", "allergens": "",
        "nutrition": {}, "education": {}, "qa": [],
    }
    return render_template(
        "catalog_product_edit.html", p=blank, cats=cats, ci=ci, pi=-1,
        is_new=True, nutrition_keys=NUTRITION_KEYS,
        edu_body_text="", qa_text="", gallery=[], main_size=None,
    )


@app.route("/catalog/product/<int:ci>/<int:pi>")
def catalog_product_edit(ci, pi):
    cats = load_catalog_bundle()["categories"]
    if ci < 0 or ci >= len(cats) or pi < 0 or pi >= len(cats[ci].get("products", [])):
        flash("Product not found.", "error")
        return redirect(url_for("catalog"))
    p = cats[ci]["products"][pi]
    return render_template(
        "catalog_product_edit.html", p=p, cats=cats, ci=ci, pi=pi,
        is_new=False, nutrition_keys=NUTRITION_KEYS,
        edu_body_text=paras_to_text((p.get("education") or {}).get("body", [])),
        qa_text=qa_to_text(p.get("qa", [])),
        gallery=gallery_with_sizes(p),
        main_size=image_file_size(p.get("image", "")),
    )


@app.route("/catalog/product/save", methods=["POST"])
def catalog_product_save():
    bundle = load_catalog_bundle()
    cats = bundle["categories"]
    ci = int(request.form.get("cat_index", "-1"))
    pi = int(request.form.get("prod_index", "-1"))
    is_new = request.form.get("is_new") == "1"
    target_ci = int(request.form.get("target_cat_index", ci))

    if ci < 0 or ci >= len(cats):
        flash("Category not found.", "error")
        return redirect(url_for("catalog"))
    if target_ci < 0 or target_ci >= len(cats):
        target_ci = ci

    existing = {}
    if not is_new and 0 <= pi < len(cats[ci].get("products", [])):
        existing = cats[ci]["products"][pi]

    # Start from the existing product so untouched fields (image offsets,
    # scales, noWhiteBg, and anything else) are preserved verbatim.
    prod = dict(existing)
    prod["id"] = request.form.get("id", "").strip()
    prod["name"] = request.form.get("name", "").strip()
    prod["japanese"] = request.form.get("japanese", "").strip()
    prod["origin"] = request.form.get("origin", "").strip()
    prod["tone"] = request.form.get("tone", "warm").strip()
    prod["tagline"] = request.form.get("tagline", "").strip()
    prod["amazon"] = request.form.get("amazon", "").strip()
    prod["image"] = resolve_image("image", existing.get("image", ""))
    prod["badges"] = lines_to_list(request.form.get("badges", ""))
    prod["pairings"] = lines_to_list(request.form.get("pairings", ""))
    prod["sellingPoints"] = lines_to_list(request.form.get("sellingPoints", ""))
    prod["ingredients"] = request.form.get("ingredients", "").strip()
    prod["allergens"] = request.form.get("allergens", "").strip()

    # Gallery images arrive as repeated `gallery_path` fields (in display order).
    images = [pth.strip() for pth in request.form.getlist("gallery_path") if pth.strip()]
    if images:
        prod["images"] = images
    else:
        prod.pop("images", None)

    # Nutrition — preserve any extra keys, update the standard ones.
    nutr = dict(existing.get("nutrition") or {})
    serving = request.form.get("nutr_serving", "").strip()
    if serving:
        nutr["serving"] = serving
    else:
        nutr.pop("serving", None)
    for key, _label in NUTRITION_KEYS:
        val = parse_num(request.form.get("nutr_" + key, ""))
        if val is None:
            nutr.pop(key, None)
        else:
            nutr[key] = val
    if nutr:
        prod["nutrition"] = nutr
    else:
        prod.pop("nutrition", None)

    # Education block
    edu = dict(existing.get("education") or {})
    edu_title = request.form.get("edu_title", "").strip()
    edu_body = text_to_paras(request.form.get("edu_body", ""))
    if edu_title:
        edu["title"] = edu_title
    else:
        edu.pop("title", None)
    if edu_body:
        edu["body"] = edu_body
    else:
        edu.pop("body", None)
    if edu:
        prod["education"] = edu
    else:
        prod.pop("education", None)

    # Q&A
    qa = text_to_qa(request.form.get("qa", ""))
    if qa:
        prod["qa"] = qa
    else:
        prod.pop("qa", None)

    _apply_seo_form(prod)

    if not prod["id"] or not prod["name"]:
        flash("A product needs at least an id and a name.", "error")
        return redirect(request.referrer or url_for("catalog"))

    prod["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if is_new:
        cats[target_ci].setdefault("products", []).append(prod)
    elif target_ci != ci:
        # Moved to another category
        cats[ci]["products"].pop(pi)
        cats[target_ci].setdefault("products", []).append(prod)
    else:
        cats[ci]["products"][pi] = prod

    # The Our Products under-link belongs to the category Emma was editing,
    # not the destination if the product is moved.
    _apply_category_link_form(cats[ci] if not is_new else cats[target_ci])

    save_data("catalog", bundle)
    flash("Saved product: %s" % prod["name"], "ok")
    return redirect(url_for("catalog"))


@app.route("/catalog/product/<int:ci>/<int:pi>/delete", methods=["POST"])
def catalog_product_delete(ci, pi):
    bundle = load_catalog_bundle()
    cats = bundle["categories"]
    if 0 <= ci < len(cats) and 0 <= pi < len(cats[ci].get("products", [])):
        removed = cats[ci]["products"].pop(pi)
        save_data("catalog", bundle)
        flash("Deleted product: %s" % removed.get("name", ""), "ok")
    return redirect(url_for("catalog"))


def reorder_by_index(items, order):
    """Return `items` in the order given by a permutation of 0..len(items)-1."""
    if not isinstance(order, list) or not all(isinstance(i, int) for i in order):
        raise ValueError("order must be a list of integers")
    if sorted(order) != list(range(len(items))):
        raise ValueError("order must be a permutation of the current items")
    return [items[i] for i in order]


def parse_journal_date(value):
    """Parse a Field Notes display date so posts can be sorted earliest first."""
    text = (value or "").strip()
    if not text:
        return datetime.max.replace(tzinfo=timezone.utc)
    for fmt in ("%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.max.replace(tzinfo=timezone.utc)


def sort_posts_earliest_first(posts):
    """Return posts oldest-date-first. Unreadable dates sort last."""
    return sorted(posts, key=lambda p: parse_journal_date(p.get("date") or ""))


def insert_post_by_date(posts, post):
    """Insert `post` so the list stays in earliest-date-first order."""
    key = parse_journal_date(post.get("date") or "")
    index = 0
    while index < len(posts) and parse_journal_date(posts[index].get("date") or "") <= key:
        index += 1
    posts.insert(index, post)
    return posts


@app.route("/catalog/reorder", methods=["POST"])
def catalog_reorder():
    """Persist a drag-and-drop reorder from the catalog page.

    Expects a JSON body of the form:
      {"kind": "products", "ci": <int>, "order": [<origIndex>, ...]}
      {"kind": "categories", "order": [<origIndex>, ...]}
    `order` must be a permutation of the current index range so we can rebuild
    the list without inventing or dropping items. On success a flash is queued
    and the client reloads the page so every ci/pi link is re-indexed cleanly.
    """
    payload = request.get_json(silent=True) or {}
    kind = payload.get("kind")
    order = payload.get("order")
    if not isinstance(order, list) or not all(isinstance(i, int) for i in order):
        return {"ok": False, "error": "order must be a list of integers"}, 400

    bundle = load_catalog_bundle()
    cats = bundle["categories"]

    if kind == "products":
        try:
            ci = int(payload.get("ci"))
        except (TypeError, ValueError):
            return {"ok": False, "error": "ci is required"}, 400
        if not (0 <= ci < len(cats)):
            return {"ok": False, "error": "category out of range"}, 400
        prods = cats[ci].get("products", [])
        try:
            cats[ci]["products"] = reorder_by_index(prods, order)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}, 400
        save_data("catalog", bundle)
        flash("Reordered products in %s." % cats[ci].get("name", "category"), "ok")
        return {"ok": True}

    if kind == "categories":
        try:
            bundle["categories"] = reorder_by_index(cats, order)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}, 400
        save_data("catalog", bundle)
        flash("Reordered categories.", "ok")
        return {"ok": True}

    return {"ok": False, "error": "unknown kind"}, 400


# ---------------------------------------------------------------------------
# Routes — publish to GitHub
# ---------------------------------------------------------------------------
def run_git(args, cwd=None):
    return subprocess.run(
        ["git"] + args, cwd=cwd or REPO_ROOT, capture_output=True, text=True
    )


def _git_ahead_behind(cwd=None):
    """Return (unpushed, behind) vs the upstream branch.

    Unpushed commits are already saved locally but not on GitHub, so the
    dashboard must count them as unpublished. `behind` means GitHub has
    commits we need to combine before a push can succeed.
    """
    res = run_git(["rev-list", "--left-right", "--count", "@{u}...HEAD"], cwd)
    if res.returncode != 0:
        return 0, 0
    parts = res.stdout.strip().split()
    if len(parts) != 2:
        return 0, 0
    try:
        return int(parts[1]), int(parts[0])
    except ValueError:
        return 0, 0


def git_status_summary(cwd=None):
    # On the GitHub backend every save is already committed + deployed, so there
    # is nothing pending to "publish".
    if cwd is None and storage.is_github():
        return {
            "ok": True, "changes": 0, "files": [], "auto": True,
            "unpushed": 0, "behind": 0, "dirty": 0,
        }
    res = run_git(["status", "--porcelain"], cwd)
    if res.returncode != 0:
        return {
            "ok": False, "changes": 0, "files": [],
            "detail": res.stderr.strip(), "unpushed": 0, "behind": 0, "dirty": 0,
        }
    changed = [ln for ln in res.stdout.splitlines() if ln.strip()]
    unpushed, behind = _git_ahead_behind(cwd)
    return {
        "ok": True,
        "changes": len(changed) + unpushed,
        "files": changed[:50],
        "unpushed": unpushed,
        "behind": behind,
        "dirty": len(changed),
    }


def _cms_data_relpaths():
    return [PROJECT_REL + "/data/" + key + ".js" for key in DATA_FILES]


def _restore_cms_data(from_ref, cwd=None):
    """Put CMS data files back to `from_ref`.

    Combining with GitHub is a line-level merge. If the remote copy already
    has duplicate JSON keys (from an earlier merge) and our commit didn't
    touch those lines, the duplicates survive — and the live site would show
    the last key, which is often the old photo. The CMS file we just saved
    is the source of truth.
    """
    restored = False
    for rel in _cms_data_relpaths():
        exists = run_git(["cat-file", "-e", "%s:%s" % (from_ref, rel)], cwd)
        if exists.returncode != 0:
            continue
        chk = run_git(["checkout", from_ref, "--", rel], cwd)
        if chk.returncode == 0:
            restored = True
    return restored


def sync_and_push(message, cwd=None):
    """Commit any local CMS edits, rebase onto origin if it moved, then push.

    A previous version committed then pushed with no fetch. When GitHub already
    had commits we lacked, the push was rejected — and a clean working tree
    made the dashboard claim everything was published.

    Returns {"ok": True} or {"ok": False, "error": "..."}. {"empty": True}
    means there was nothing new to send.
    """
    add = run_git(["add", "-A"], cwd)
    if add.returncode != 0:
        return {"ok": False, "error": "git add failed: %s" % add.stderr.strip()}

    commit = run_git(["commit", "-m", message], cwd)
    if commit.returncode != 0:
        out = (commit.stdout + commit.stderr).lower()
        if "nothing to commit" not in out:
            return {
                "ok": False,
                "error": "git commit failed: %s" % (commit.stderr or commit.stdout).strip(),
            }

    pre_head = run_git(["rev-parse", "HEAD"], cwd)
    pre_ref = (pre_head.stdout or "").strip()

    fetch = run_git(["fetch", "origin"], cwd)
    if fetch.returncode != 0:
        return {"ok": False, "error": "git fetch failed: %s" % fetch.stderr.strip()}

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    branch_name = (branch.stdout or "").strip()
    if branch.returncode != 0 or not branch_name or branch_name == "HEAD":
        return {"ok": False, "error": "Could not determine git branch."}

    _, behind = _git_ahead_behind(cwd)
    if behind:
        # During rebase, "theirs" is the CMS commit being replayed. Prefer
        # that so a just-saved photo or cache-buster stamp isn't reverted.
        rebase = run_git(
            ["pull", "--rebase", "--autostash", "-X", "theirs", "origin", branch_name],
            cwd,
        )
        if rebase.returncode != 0:
            run_git(["rebase", "--abort"], cwd)
            return {
                "ok": False,
                "error": "Could not combine with newer GitHub changes: %s"
                % (rebase.stderr or rebase.stdout).strip(),
            }
        if pre_ref and _restore_cms_data(pre_ref, cwd):
            status = run_git(["status", "--porcelain"], cwd)
            if status.stdout.strip():
                run_git(["add", "-A"], cwd)
                keep = run_git(
                    ["commit", "-m", "%s — keep saved CMS content" % message],
                    cwd,
                )
                if keep.returncode != 0:
                    return {
                        "ok": False,
                        "error": "git commit failed: %s"
                        % (keep.stderr or keep.stdout).strip(),
                    }

    unpushed, _ = _git_ahead_behind(cwd)
    if unpushed == 0:
        return {"ok": True, "empty": True}

    push = run_git(["push", "origin", "HEAD"], cwd)
    if push.returncode != 0:
        return {"ok": False, "error": "git push failed: %s" % push.stderr.strip()}
    return {"ok": True}


# Cache-busting for the content data files. The HTML pages load products/
# catalog/homepage/journal JSON via <script src="data/xxx.js"> tags. Browsers
# (on the local http.server serving localhost:8080) and the Vercel edge CDN can
# serve a stale copy of these files, which means the page renders old content
# (e.g. an old product image path) even though the new file is on disk / live.
# Rewriting the ?v= query whenever a data file is saved gives it a brand-new
# URL, forcing a fresh fetch on the very next refresh — no publish required.
ALL_DATA_KEYS = tuple(DATA_FILES.keys())


def _data_script_re(keys):
    """Regex matching <script src="data/<key>.js?v=..."> for the given keys.

    Anchored to the script `src` attribute so comments that mention
    `data/people.js` are not rewritten (the old pattern ate the `).` after
    those comments on every People save).
    """
    names = "|".join(re.escape(k) for k in keys)
    return re.compile(
        r'(<script\b[^>]*\bsrc=["\'])(data/(?:' + names + r')\.js)(\?v=[^"\']*)?(["\'])',
        re.IGNORECASE,
    )


def _cache_bust_changes(keys=None):
    """Compute (relpath, new_text, False) edits that stamp a fresh
    ?v=<timestamp> onto the data-file <script> tags across the site's HTML
    pages, so browsers/CDN refetch the new content immediately.

    `keys` may be a single data-file key, an iterable of keys, or None for all.
    Only the tags for the given keys are touched, keeping each save's diff small.
    """
    if keys is None:
        keys = ALL_DATA_KEYS
    elif isinstance(keys, str):
        keys = (keys,)
    pattern = _data_script_re(keys)
    # Include milliseconds so two saves within the same second still produce a
    # different ?v=, guaranteeing the browser refetches after every save.
    stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    changes = []
    for name in storage.list_dir(PROJECT_REL):
        if not name.lower().endswith(".html"):
            continue
        rel = PROJECT_REL + "/" + name
        try:
            text = storage.read_text(rel)
        except Exception:
            continue
        new_text = pattern.sub(r"\g<1>\g<2>?v=" + stamp + r"\g<4>", text)
        if new_text != text:
            changes.append((rel, new_text, False))
    return changes


def _html_publish_changes(key, data):
    """Cache-bust data scripts and write SEO + maintenance markup into the
    matching HTML pages."""
    keys = (key,) if isinstance(key, str) else tuple(key)
    pattern = _data_script_re(keys)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    changes = []
    for name in storage.list_dir(PROJECT_REL):
        if not name.lower().endswith(".html"):
            continue
        rel = PROJECT_REL + "/" + name
        try:
            text = storage.read_text(rel)
        except Exception:
            continue
        new_text = text
        if isinstance(data, dict):
            new_text = seo.apply_to_html(new_text, name, key, data)
        new_text = maintenance.apply_to_html(new_text, name, key, data)
        new_text = pattern.sub(r"\g<1>\g<2>?v=" + stamp + r"\g<4>", new_text)
        if new_text != text:
            changes.append((rel, new_text, False))
    return changes


def bump_data_cache_bust(keys=None):
    """Persist fresh cache-busters right now (used by the local Publish flow).
    Normal saves already fold these edits into save_data's single batch."""
    changes = _cache_bust_changes(keys)
    if changes:
        storage.persist(changes, message="CMS: refresh cache-busters")
    return len(changes)


@app.route("/publish", methods=["POST"])
def publish():
    # Online (GitHub) backend publishes automatically on every save.
    if storage.is_github():
        flash("Auto-publish is on — every change is committed and deployed automatically.", "ok")
        return redirect(url_for("index"))
    message = request.form.get("message", "").strip() or (
        "CMS update — %s" % datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    # Refresh the cache-busting query on the data-file script tags so the new
    # content is fetched immediately after this deploy goes live.
    bump_data_cache_bust()
    result = sync_and_push(message)
    if not result.get("ok"):
        flash(result.get("error") or "Publish failed.", "error")
    elif result.get("empty"):
        flash("Nothing to publish — no changes since last publish.", "ok")
    else:
        flash("Published to GitHub: %s" % message, "ok")
    return redirect(url_for("index"))


def _visual_sections(page, data):
    from visual import get_path
    out = []
    for spec in page.get("sections") or []:
        try:
            visible = get_path(data, spec["path"])
        except Exception:
            visible = True
        item = dict(spec)
        item["visible"] = False if visible is False else True
        out.append(item)
    return out


@app.route("/visual")
def visual_editor():
    from visual import SITE_PAGES, page_by_id
    page_id = request.args.get("page") or "home"
    page = page_by_id(page_id) or SITE_PAGES[0]
    data = {}
    try:
        data = load_data(page["data_key"])
    except Exception:
        data = {}
    return render_template(
        "visual.html",
        pages=SITE_PAGES,
        page_id=page["id"],
        data_key=page["data_key"],
        sections=_visual_sections(page, data),
    )


def _project_rel(filename):
    return PROJECT_REL + "/" + str(filename).replace("\\", "/").lstrip("/")


def _read_project_html(filename):
    return storage.read_text(_project_rel(filename))


@app.route("/preview/<page_id>")
def visual_preview(page_id):
    from visual import page_by_id, rewrite_preview_html
    page = page_by_id(page_id)
    filename = page["file"] if page else (
        page_id if str(page_id).endswith(".html") else str(page_id) + ".html"
    )
    try:
        html = _read_project_html(filename)
    except Exception:
        abort(404)
    return Response(rewrite_preview_html(html, os.path.basename(filename)), mimetype="text/html")


@app.route("/preview-static/<path:filename>")
def preview_static(filename):
    try:
        data = storage.read_bytes(_project_rel(filename))
    except Exception:
        abort(404)
    if data is None:
        abort(404)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    resp = Response(data, mimetype=ctype)
    resp.headers["Cache-Control"] = "private, max-age=60"
    return resp


@app.route("/api/visual/patch", methods=["POST"])
def visual_patch():
    from visual import set_path
    body = request.get_json(force=True, silent=True) or {}
    key = body.get("key")
    path = body.get("path")
    if key not in DATA_FILES or not path:
        return jsonify(ok=False, error="Missing field"), 400
    try:
        data = load_data(key)
        set_path(data, path, body.get("value", ""))
        save_data(key, data)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400
    return jsonify(ok=True)


@app.route("/api/visual/image", methods=["POST"])
def visual_image():
    from visual import set_path
    key = request.form.get("key")
    path = request.form.get("path")
    if key not in DATA_FILES or not path:
        return jsonify(ok=False, error="Missing field"), 400
    try:
        uploaded = save_upload_detailed(request.files.get("file"))
        if not uploaded:
            return jsonify(ok=False, error="No image"), 400
        data = load_data(key)
        set_path(data, path, uploaded["path"])
        save_data(key, data)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400
    return jsonify(ok=True, url=uploaded["preview_url"], path=uploaded["path"])


@app.route("/api/visual/section", methods=["POST"])
def visual_section():
    from visual import add_custom_section, set_path
    body = request.get_json(force=True, silent=True) or {}
    key = body.get("key")
    if key not in DATA_FILES:
        return jsonify(ok=False, error="Unknown page data"), 400
    try:
        data = load_data(key)
        action = body.get("action")
        if action == "add":
            add_custom_section(data, body.get("heading") or "New section", body.get("body") or "")
        elif action == "visibility":
            set_path(data, body.get("path"), bool(body.get("visible")))
        else:
            return jsonify(ok=False, error="Unknown action"), 400
        save_data(key, data)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400
    return jsonify(ok=True)


@app.route("/api/visual/page", methods=["POST"])
def visual_add_page():
    from visual import draft_site_page
    body = request.get_json(force=True, silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(ok=False, error="A page needs a title"), 400
    try:
        nav = load_data("nav")
    except Exception:
        nav = {"left": [], "right": []}
    try:
        result = draft_site_page(
            title,
            body.get("heading") or title,
            body.get("body") or "",
            nav,
            storage.list_dir(PROJECT_REL),
        )
        storage.persist(
            [(_project_rel(result["filename"]), result["html"], False)],
            message="CMS: add page %s" % result["filename"],
        )
        save_data("nav", result["nav"])
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400
    return jsonify(ok=True, filename=result["filename"])


if __name__ == "__main__":
    print("Emma Basic CMS running at http://localhost:5000")
    print("Editing content in:", DATA_DIR)
    app.run(host="127.0.0.1", port=5000, debug=True)
