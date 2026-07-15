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
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

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
}

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"}

HEADERS = {
    "products": "/* Emma Basic — product data (CMS-managed). The payload below is strict JSON. */",
    "journal": "/* Emma Basic — journal / blog data (CMS-managed). The payload below is strict JSON. */",
    "homepage": "/* Emma Basic — homepage content (CMS-managed). The payload below is strict JSON. */",
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


def save_upload(file_storage):
    """Save an uploaded image into assets/uploads and return its web path."""
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Unsupported image type: %s" % ext)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    base = secure_filename(os.path.splitext(file_storage.filename)[0]) or "image"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = "{base}-{stamp}{ext}".format(base=base, stamp=stamp, ext=ext)
    file_storage.save(os.path.join(UPLOAD_DIR, name))
    return "assets/uploads/" + name


def resolve_image(form_key, existing=""):
    """Given a form, prefer an uploaded file, else the text path field."""
    upload = request.files.get(form_key + "_file")
    if upload and upload.filename:
        return save_upload(upload)
    return request.form.get(form_key, existing).strip()


# ---------------------------------------------------------------------------
# Routes — dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    products = load_data("products")
    journal = load_data("journal")
    return render_template(
        "index.html",
        product_count=len(products),
        post_count=len(journal.get("posts", [])),
        git=git_status_summary(),
    )


# Serve the site's assets so image previews work inside the CMS
@app.route("/site-assets/<path:filename>")
def site_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


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


@app.route("/publish", methods=["POST"])
def publish():
    message = request.form.get("message", "").strip() or (
        "CMS update — %s" % datetime.now().strftime("%Y-%m-%d %H:%M")
    )
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
