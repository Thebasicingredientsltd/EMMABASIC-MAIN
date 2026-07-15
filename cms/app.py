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

import json
import os
import re
import subprocess
from datetime import datetime

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

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
}

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"}

# Image optimization settings. Uploaded photos are scaled down to at most
# MAX_DIM on the longest edge and re-encoded to shed file size — the main
# cause of a slow site is oversized source images.
MAX_DIM = 2000
JPEG_QUALITY = 82
WEBP_QUALITY = 82

HEADERS = {
    "products": "/* Emma Basic — product data (CMS-managed). The payload below is strict JSON. */",
    "journal": "/* Emma Basic — journal / blog data (CMS-managed). The payload below is strict JSON. */",
    "homepage": "/* Emma Basic — homepage content (CMS-managed). The payload below is strict JSON. */",
    "catalog": "/* Emma Basic — full product catalog (CMS-managed). The payload below is strict JSON. */",
}

app = Flask(__name__)
app.secret_key = "emma-basic-cms-local"


# ---------------------------------------------------------------------------
# Data file helpers
# ---------------------------------------------------------------------------
def load_data(key):
    """Read a data file and return the parsed JSON payload."""
    info = DATA_FILES[key]
    with open(info["file"], "r", encoding="utf-8") as fh:
        text = fh.read()
    # Strip everything up to the first '=' then trailing ';'
    idx = text.index("=")
    payload = text[idx + 1:].strip()
    if payload.endswith(";"):
        payload = payload[:-1].strip()
    return json.loads(payload)


def save_data(key, data):
    """Write the JSON payload back into the `window.EB_X = ...;` wrapper."""
    info = DATA_FILES[key]
    body = json.dumps(data, ensure_ascii=False, indent=2)
    text = "{header}\n{var} = {body};\n".format(
        header=HEADERS[key], var=info["var"], body=body
    )
    with open(info["file"], "w", encoding="utf-8") as fh:
        fh.write(text)


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


def optimize_image(abs_path):
    """Resize/recompress an image in place to reduce file size.

    Returns a dict describing what changed (used for user feedback). Safely
    no-ops for vector/unsupported formats (e.g. SVG, AVIF without a plugin).
    """
    info = {"optimized": False}
    if not HAVE_PIL:
        return info
    ext = os.path.splitext(abs_path)[1].lower()
    try:
        img = Image.open(abs_path)
        img.load()
    except Exception:
        return info  # not a raster image Pillow understands — leave untouched

    info["dims_before"] = "%d×%d" % img.size
    img = ImageOps.exif_transpose(img)  # honour phone orientation
    resized = False
    if max(img.size) > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM))
        resized = True

    try:
        if ext in (".jpg", ".jpeg"):
            img.convert("RGB").save(abs_path, quality=JPEG_QUALITY, optimize=True, progressive=True)
        elif ext == ".png":
            img.save(abs_path, optimize=True)
        elif ext == ".webp":
            img.save(abs_path, quality=WEBP_QUALITY, method=6)
        else:
            # gif or other — only rewrite if we resized
            if resized:
                img.save(abs_path)
            else:
                return info
        info["optimized"] = True
        info["dims_after"] = "%d×%d" % img.size
    except Exception:
        pass
    return info


def save_upload(file_storage):
    """Save + optimize an uploaded image; return its web path (or None)."""
    result = save_upload_detailed(file_storage)
    return result["path"] if result else None


def save_upload_detailed(file_storage):
    """Save an uploaded image into assets/uploads, optimize it, and return
    a dict with the web path and before/after size info."""
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Unsupported image type: %s" % ext)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    base = secure_filename(os.path.splitext(file_storage.filename)[0]) or "image"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = "{base}-{stamp}{ext}".format(base=base, stamp=stamp, ext=ext)
    abs_path = os.path.join(UPLOAD_DIR, name)
    file_storage.save(abs_path)

    orig_bytes = os.path.getsize(abs_path)
    opt = optimize_image(abs_path)
    new_bytes = os.path.getsize(abs_path)

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
    rel = web_path.strip().lstrip("/")
    abs_path = os.path.join(PROJECT_DIR, *rel.split("/"))
    if os.path.isfile(abs_path):
        return _human_kb(os.path.getsize(abs_path))
    return None


def gallery_with_sizes(product):
    """Build the gallery list [{path, size}] for a catalog product."""
    return [{"path": img, "size": image_file_size(img)}
            for img in (product.get("images") or [])]


# ---------------------------------------------------------------------------
# Routes — dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    products = load_data("products")
    journal = load_data("journal")
    catalog_data = load_data("catalog")
    return render_template(
        "index.html",
        product_count=len(products),
        post_count=len(journal.get("posts", [])),
        catalog_categories=len(catalog_data),
        catalog_products=_catalog_counts(catalog_data),
        git=git_status_summary(),
    )


# Serve the site's assets so image previews work inside the CMS
@app.route("/site-assets/<path:filename>")
def site_assets(filename):
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
    return render_template("journal.html", posts=load_data("journal").get("posts", []))


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

    save_data("homepage", h)
    flash("Homepage content saved.", "ok")
    return redirect(url_for("homepage"))


# ---------------------------------------------------------------------------
# Routes — product catalog (the full "Our Products" range)
# ---------------------------------------------------------------------------
def _catalog_counts(catalog):
    return sum(len(c.get("products", [])) for c in catalog)


@app.route("/catalog")
def catalog():
    return render_template("catalog.html", catalog=load_data("catalog"))


@app.route("/catalog/category/new")
def catalog_category_new():
    blank = {"id": "", "number": "", "name": "", "japanese": "", "blurb": ""}
    return render_template("catalog_category_edit.html", c=blank, index=-1, is_new=True)


@app.route("/catalog/category/<int:ci>")
def catalog_category_edit(ci):
    cats = load_data("catalog")
    if ci < 0 or ci >= len(cats):
        flash("Category not found.", "error")
        return redirect(url_for("catalog"))
    return render_template("catalog_category_edit.html", c=cats[ci], index=ci, is_new=False)


@app.route("/catalog/category/save", methods=["POST"])
def catalog_category_save():
    cats = load_data("catalog")
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
    save_data("catalog", cats)
    flash("Saved category: %s" % cat["name"], "ok")
    return redirect(url_for("catalog"))


@app.route("/catalog/category/<int:ci>/delete", methods=["POST"])
def catalog_category_delete(ci):
    cats = load_data("catalog")
    if 0 <= ci < len(cats):
        removed = cats.pop(ci)
        save_data("catalog", cats)
        flash("Deleted category: %s (and its %d products)"
              % (removed.get("name", ""), len(removed.get("products", []))), "ok")
    return redirect(url_for("catalog"))


@app.route("/catalog/product/new")
def catalog_product_new():
    cats = load_data("catalog")
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
    cats = load_data("catalog")
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
    cats = load_data("catalog")
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

    if is_new:
        cats[target_ci].setdefault("products", []).append(prod)
    elif target_ci != ci:
        # Moved to another category
        cats[ci]["products"].pop(pi)
        cats[target_ci].setdefault("products", []).append(prod)
    else:
        cats[ci]["products"][pi] = prod

    save_data("catalog", cats)
    flash("Saved product: %s" % prod["name"], "ok")
    return redirect(url_for("catalog"))


@app.route("/catalog/product/<int:ci>/<int:pi>/delete", methods=["POST"])
def catalog_product_delete(ci, pi):
    cats = load_data("catalog")
    if 0 <= ci < len(cats) and 0 <= pi < len(cats[ci].get("products", [])):
        removed = cats[ci]["products"].pop(pi)
        save_data("catalog", cats)
        flash("Deleted product: %s" % removed.get("name", ""), "ok")
    return redirect(url_for("catalog"))


# ---------------------------------------------------------------------------
# Routes — publish to GitHub
# ---------------------------------------------------------------------------
def run_git(args):
    return subprocess.run(
        ["git"] + args, cwd=REPO_ROOT, capture_output=True, text=True
    )


def git_status_summary():
    res = run_git(["status", "--porcelain"])
    if res.returncode != 0:
        return {"ok": False, "changes": 0, "detail": res.stderr.strip()}
    changed = [ln for ln in res.stdout.splitlines() if ln.strip()]
    return {"ok": True, "changes": len(changed), "files": changed[:50]}


# Cache-busting for the content data files. The HTML pages load products/
# catalog/homepage/journal JSON via <script src="data/xxx.js"> tags. Browsers
# and the Vercel edge CDN can serve a stale copy of these files after a deploy,
# which means the page renders old content (e.g. an old product image path)
# even though the new file is live. Rewriting the ?v= query on every publish
# gives each data file a brand-new URL, forcing a fresh fetch every time.
DATA_SCRIPT_RE = re.compile(
    r"(data/(?:products|catalog|homepage|journal)\.js)(\?v=[^\"'\s>]*)?"
)


def bump_data_cache_bust():
    """Stamp a fresh ?v=<timestamp> onto every data-file <script> tag across the
    site's HTML pages. Returns the number of HTML files changed."""
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    changed = 0
    for name in os.listdir(PROJECT_DIR):
        if not name.lower().endswith(".html"):
            continue
        path = os.path.join(PROJECT_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        new_text = DATA_SCRIPT_RE.sub(r"\g<1>?v=" + stamp, text)
        if new_text != text:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_text)
            changed += 1
    return changed


@app.route("/publish", methods=["POST"])
def publish():
    message = request.form.get("message", "").strip() or (
        "CMS update — %s" % datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    # Refresh the cache-busting query on the data-file script tags so the new
    # content is fetched immediately after this deploy goes live.
    bump_data_cache_bust()
    add = run_git(["add", "-A"])
    if add.returncode != 0:
        flash("git add failed: %s" % add.stderr.strip(), "error")
        return redirect(url_for("index"))

    commit = run_git(["commit", "-m", message])
    if commit.returncode != 0:
        out = (commit.stdout + commit.stderr).lower()
        if "nothing to commit" in out:
            flash("Nothing to publish — no changes since last publish.", "ok")
            return redirect(url_for("index"))
        flash("git commit failed: %s" % (commit.stderr or commit.stdout).strip(), "error")
        return redirect(url_for("index"))

    push = run_git(["push", "origin", "HEAD"])
    if push.returncode != 0:
        flash("Committed locally, but push failed: %s" % push.stderr.strip(), "error")
        return redirect(url_for("index"))

    flash("Published to GitHub: %s" % message, "ok")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("Emma Basic CMS running at http://localhost:5000")
    print("Editing content in:", DATA_DIR)
    app.run(host="127.0.0.1", port=5000, debug=True)
