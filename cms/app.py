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
    changes.extend(_cache_bust_changes(key))
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


def form_checkbox(name):
    """True when an HTML checkbox named `name` was checked.

    Unchecked boxes are omitted from the POST body. Missing therefore means
    False — never default a section back to visible on save.
    """
    raw = request.form.get(name)
    if raw is None:
        return False
    return str(raw).strip().lower() in ("on", "true", "1", "yes")


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

# Public website pages shown in the CRM sidebar. Tools (dashboard, home rail,
# visual editor) stay outside this list.
CMS_SITE_PAGES = [
    {"endpoint": "homepage", "label": "Homepage", "active": "homepage"},
    {"endpoint": "catalog", "label": "Our Products", "active": "catalog"},
    {"endpoint": "journal", "label": "Field Notes", "active": "journal"},
    {"endpoint": "story", "label": "Our Story", "active": "story"},
    {"endpoint": "people", "label": "People & Places", "active": "people"},
    {"endpoint": "places", "label": "Where to find our products", "active": "places"},
    {"endpoint": "distributor", "label": "Become a Distributor", "active": "distributor"},
    {"endpoint": "company", "label": "The Basic Ingredients Ltd", "active": "company"},
    {"endpoint": "matcha", "label": "Matcha Lab", "active": "matcha"},
]
app.jinja_env.globals["cms_site_pages"] = CMS_SITE_PAGES


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
    return render_template("products.html", products=load_data("products"))


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
    )


@app.route("/journal/hero/save", methods=["POST"])
def journal_hero_save():
    data = load_data("journal")
    _apply_hero_form(data.setdefault("hero", {}))
    _apply_footer_form(data)
    save_data("journal", data)
    flash("Field Notes headline saved.", "ok")
    return redirect(url_for("journal"))


@app.route("/journal/new")
def journal_new():
    blank_post = {
        "id": "", "category": "Ingredient Stories", "date": "", "title": "",
        "excerpt": "", "image": "", "tone": "warm", "featured": False,
    }
    blank_article = {
        "category": "Ingredient Stories", "date": "", "readTime": "", "title": "",
        "image": "", "imagePosition": "", "intro": "", "body": [],
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
        "excerpt": request.form.get("excerpt", "").strip(),
        "image": image,
        "tone": request.form.get("tone", "warm").strip(),
        "featured": request.form.get("featured") == "on",
    }

    article = {
        "category": post["category"],
        "date": post["date"],
        "readTime": request.form.get("readTime", "").strip(),
        "title": request.form.get("article_title", "").strip() or post["title"],
        "image": resolve_image("article_image", existing_article.get("image", "")) or image,
        "imagePosition": request.form.get("imagePosition", "").strip(),
        "intro": request.form.get("intro", "").strip(),
        "body": text_to_body(request.form.get("body", "")),
    }

    if not post_id or not post["title"]:
        flash("Post needs at least an id and a title.", "error")
        return redirect(request.referrer or url_for("journal"))

    # If featured, unset featured on all others
    if post["featured"]:
        for p in posts:
            p["featured"] = False

    if is_new:
        posts.append(post)
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


# ---------------------------------------------------------------------------
# Routes — homepage
# ---------------------------------------------------------------------------
@app.route("/homepage")
def homepage():
    return render_template("homepage.html", h=load_data("homepage"))


@app.route("/homepage/save", methods=["POST"])
def homepage_save():
    h = load_data("homepage")

    hero = h.setdefault("hero", {})
    hero["image"] = resolve_image("hero_image", hero.get("image", ""))
    hero["headlineLine1"] = request.form.get("hero_headlineLine1", "").strip()
    hero["headlineLine2"] = request.form.get("hero_headlineLine2", "").strip()
    hero["body"] = request.form.get("hero_body", "").strip()
    # Hero buttons (up to 2)
    buttons = []
    for i in (1, 2):
        label = request.form.get("hero_btn%d_label" % i, "").strip()
        href = request.form.get("hero_btn%d_href" % i, "").strip()
        if label:
            buttons.append({"label": label, "href": href, "primary": i == 1})
    if buttons:
        hero["buttons"] = buttons
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
    shelf["theirs"] = lines_to_list(request.form.get("shelf_theirs", ""))
    shelf["ours"] = lines_to_list(request.form.get("shelf_ours", ""))
    shelf["closingLine1"] = request.form.get("shelf_closingLine1", "").strip()
    shelf["closingLine2"] = request.form.get("shelf_closingLine2", "").strip()

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

    save_data("homepage", h)
    flash("Homepage content saved.", "ok")
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
    return render_template("distributor.html", d=load_data("people"))


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
    save_data("people", d)
    flash("Become a Distributor content saved.", "ok")
    return redirect(url_for("distributor"))


def _apply_hero_form(hero):
    hero["eyebrow"] = request.form.get("hero_eyebrow", "").strip()
    hero["title"] = request.form.get("hero_title", "").strip()
    hero["titleItalic"] = request.form.get("hero_titleItalic", "").strip()
    hero["subtitle"] = request.form.get("hero_subtitle", "").strip()
    hero["visible"] = form_checkbox("hero_visible")


def _apply_footer_form(data, key="footer"):
    """Per-page footer visibility. Unchecked box is omitted from POST → False."""
    data.setdefault(key, {})["visible"] = form_checkbox("footer_visible")


def _simple_page_save(key, flash_msg, redirect_endpoint):
    data = load_data(key)
    _apply_hero_form(data.setdefault("hero", {}))
    _apply_footer_form(data)
    save_data(key, data)
    flash(flash_msg, "ok")
    return redirect(url_for(redirect_endpoint))


@app.route("/places")
def places():
    return render_template("places.html", d=load_data("places"))


@app.route("/places/save", methods=["POST"])
def places_save():
    d = load_data("places")
    _apply_hero_form(d.setdefault("hero", {}))
    _apply_footer_form(d)
    featured = d.setdefault("featured", {})
    featured["eyebrow"] = request.form.get("featured_eyebrow", "").strip()
    featured["heading"] = request.form.get("featured_heading", "").strip()
    featured["headingItalic"] = request.form.get("featured_headingItalic", "").strip()
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

    shops = []
    shop_count = int(request.form.get("shop_count", "0"))
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
        shops.append(prev)
    d["shops"] = shops

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
    flash("Where to find our products content saved.", "ok")
    return redirect(url_for("places"))


@app.route("/story")
def story():
    return render_template(
        "simple_page.html",
        page_title="Our Story",
        save_endpoint="story_save",
        visual_page="story",
        active="story",
        d=load_data("story"),
        extra="The founder story below the headline is edited on the Homepage. The photo gallery heading is on this page.",
    )


@app.route("/story/save", methods=["POST"])
def story_save():
    data = load_data("story")
    _apply_hero_form(data.setdefault("hero", {}))
    _apply_footer_form(data)
    gallery = data.setdefault("gallery", {})
    gallery["heading"] = request.form.get("gallery_heading", "").strip()
    gallery["headingItalic"] = request.form.get("gallery_headingItalic", "").strip()
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
    save_data("company", d)
    flash("The Basic Ingredients content saved.", "ok")
    return redirect(url_for("company"))


@app.route("/matcha")
def matcha():
    return render_template(
        "simple_page.html",
        page_title="Matcha Lab",
        save_endpoint="matcha_save",
        visual_page="matcha",
        active="matcha",
        d=load_data("matcha"),
        extra="This is the Matcha Lab landing page (M002). Product details also live in the Catalog.",
    )


@app.route("/matcha/save", methods=["POST"])
def matcha_save():
    return _simple_page_save("matcha", "Matcha Lab content saved.", "matcha")


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
    )


@app.route("/catalog/hero/save", methods=["POST"])
def catalog_hero_save():
    bundle = load_catalog_bundle()
    _apply_hero_form(bundle.setdefault("hero", {}))
    _apply_footer_form(bundle)
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


@app.route("/preview/<page_id>")
def visual_preview(page_id):
    from visual import page_by_id, rewrite_preview_html, SITE_PAGES
    page = page_by_id(page_id)
    if page is None:
        custom = os.path.join(PROJECT_DIR, page_id if page_id.endswith(".html") else page_id + ".html")
        if not os.path.isfile(custom):
            abort(404)
        with open(custom, encoding="utf-8") as fh:
            html = fh.read()
        return Response(rewrite_preview_html(html, os.path.basename(custom)), mimetype="text/html")
    path = os.path.join(PROJECT_DIR, page["file"])
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    return Response(rewrite_preview_html(html, page["file"]), mimetype="text/html")


@app.route("/preview-static/<path:filename>")
def preview_static(filename):
    return send_from_directory(PROJECT_DIR, filename)


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
    from visual import add_site_page
    body = request.get_json(force=True, silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(ok=False, error="A page needs a title"), 400
    try:
        nav = load_data("nav")
    except Exception:
        nav = {"left": [], "right": []}
    try:
        result = add_site_page(
            PROJECT_DIR,
            title,
            body.get("heading") or title,
            body.get("body") or "",
            nav,
        )
        save_data("nav", result["nav"])
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 400
    return jsonify(ok=True, filename=result["filename"])


if __name__ == "__main__":
    print("Emma Basic CMS running at http://localhost:5000")
    print("Editing content in:", DATA_DIR)
    app.run(host="127.0.0.1", port=5000, debug=True)
