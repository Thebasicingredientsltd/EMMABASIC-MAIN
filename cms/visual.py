"""Visual editing helpers for the Emma Basic CRM.

The CRM's form pages are still there. This module powers a click-to-edit
preview of the live site: patch a JSON path, add a section, or add a page.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from html import escape

PATH_TOKEN = re.compile(r"[^.\[\]]+|\[\d+\]")
NON_SLUG = re.compile(r"[^a-z0-9]+")

SITE_PAGES = [
    {
        "id": "home",
        "file": "Emma Basic Homepage.html",
        "label": "Homepage",
        "data_key": "homepage",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
        ],
    },
    {
        "id": "people",
        "file": "People & Places.html",
        "label": "People & Places",
        "data_key": "people",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
            {"id": "founder", "path": "founder.visible", "label": "Founder photo & story"},
            {"id": "team", "path": "team.visible", "label": "Team"},
            {"id": "intro", "path": "intro.visible", "label": "Who we are"},
            {"id": "services", "path": "services.visible", "label": "What we offer"},
            {"id": "contact", "path": "contact.visible", "label": "Contact"},
        ],
    },
    {
        "id": "products",
        "file": "Our Products.html",
        "label": "Our Products",
        "data_key": "catalog",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
        ],
    },
    {
        "id": "journal",
        "file": "Journal.html",
        "label": "Field Notes",
        "data_key": "journal",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
        ],
    },
    {
        "id": "distributor",
        "file": "Become a Distributor.html",
        "label": "Become a Distributor",
        "data_key": "people",
        "sections": [
            {"id": "hero", "path": "distributor.visible", "label": "Page header"},
            {"id": "otherWays", "path": "distributor.otherWays.visible", "label": "Other ways to receive"},
            {"id": "sheetFooter", "path": "distributor.sheetFooter.visible", "label": "Guide footer line"},
            {"id": "footer", "path": "distributorFooter.visible", "label": "Page footer"},
        ],
    },
    {
        "id": "places",
        "file": "Places.html",
        "label": "Where to find our products",
        "data_key": "places",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
        ],
    },
    {
        "id": "story",
        "file": "Our Story.html",
        "label": "Our Story",
        "data_key": "story",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
        ],
    },
    {
        "id": "company",
        "file": "The Basic Ingredients.html",
        "label": "The Basic Ingredients Ltd",
        "data_key": "company",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
        ],
    },
    {
        "id": "matcha",
        "file": "Matcha Lab.html",
        "label": "Matcha Lab",
        "data_key": "matcha",
        "sections": [
            {"id": "hero", "path": "hero.visible", "label": "Page header"},
            {"id": "footer", "path": "footer.visible", "label": "Page footer"},
        ],
    },
]


def parse_path(path):
    """Split 'team.members[0].name' into ['team', 'members', 0, 'name']."""
    if not path:
        raise ValueError("empty path")
    parts = []
    for token in PATH_TOKEN.findall(path):
        if token.startswith("["):
            parts.append(int(token[1:-1]))
        else:
            parts.append(token)
    if not parts:
        raise ValueError("empty path")
    return parts


def get_path(obj, path):
    cur = obj
    for key in parse_path(path):
        cur = cur[key]
    return cur


def set_path(obj, path, value):
    keys = parse_path(path)
    cur = obj
    for i, key in enumerate(keys[:-1]):
        nxt = keys[i + 1]
        if isinstance(key, int):
            cur = cur[key]
            continue
        if key not in cur or cur[key] is None:
            cur[key] = [] if isinstance(nxt, int) else {}
        cur = cur[key]
    last = keys[-1]
    cur[last] = value
    return obj


def slugify(title):
    slug = NON_SLUG.sub("-", (title or "").lower()).strip("-")
    return slug or "page"


def add_custom_section(data, heading, body):
    """Append a freeform section the visual editor can show or hide."""
    section = {
        "id": "extra-%s" % datetime.now().strftime("%Y%m%d%H%M%S"),
        "heading": heading or "New section",
        "body": body or "",
        "visible": True,
    }
    data.setdefault("extraSections", []).append(section)
    return section


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title} — Emma Basic</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..700,0..100,0..1;1,9..144,300..700,0..100,0..1&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="components/tokens.css"/>
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y" crossorigin="anonymous"></script>
</head>
<body data-screen-label="{title}">
<div id="root"></div>
<script src="data/nav.js"></script>
<script type="text/babel" src="components/Placeholder.jsx"></script>
<script type="text/babel" src="components/motion.jsx"></script>
<script type="text/babel" src="components/TopNav.jsx?v=18"></script>
<script type="text/babel" src="components/Sections.jsx"></script>
<script type="text/babel" src="components/ExtraSections.jsx"></script>
<script type="text/babel">
function CustomPage() {{
  const heading = {heading_js};
  const body = {body_js};
  return (
    <>
      <TopNav />
      <main>
        <section style={{{{ background: "var(--paper)", padding: "140px var(--pad-x) 80px" }}}}>
          <div style={{{{ maxWidth: "var(--maxw)", margin: "0 auto" }}}}>
            <p className="eb-kicker">Emma Basic</p>
            <h1 style={{{{ fontFamily: "var(--f-display)", fontSize: "clamp(40px, 7vw, 84px)", margin: "0 0 24px", letterSpacing: "-0.03em", fontWeight: 400 }}}}>{{heading}}</h1>
            <p style={{{{ fontFamily: "var(--f-body)", fontSize: 20, lineHeight: 1.5, maxWidth: 640, margin: 0 }}}} dangerouslySetInnerHTML={{{{ __html: body }}}} />
          </div>
        </section>
        <ExtraSections source={{ extraSections: [] }} />
      </main>
      <SiteFooter />
    </>
  );
}}
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<CustomPage />);
</script>
</body>
</html>
"""


def add_site_page(project_dir, title, heading, body, nav):
    """Write a new HTML page and append it to the site nav."""
    base = slugify(title)
    filename = base + ".html"
    n = 2
    while os.path.exists(os.path.join(project_dir, filename)):
        filename = "%s-%d.html" % (base, n)
        n += 1
    html = PAGE_TEMPLATE.format(
        title=escape(title),
        heading_js=json_str(heading or title),
        body_js=json_str(body or ""),
    )
    path = os.path.join(project_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    nav = nav if isinstance(nav, dict) else {}
    nav.setdefault("right", [])
    nav["right"].append({"label": title, "href": filename})
    return {"filename": filename, "title": title, "nav": nav}


def json_str(value):
    return json.dumps(value, ensure_ascii=False)


REL_ATTR = re.compile(
    r'(\b(?:src|href)=["\'])(?!https?:|//|mailto:|tel:|#|data:|/)([^"\']+)(["\'])',
    re.IGNORECASE,
)


def rewrite_preview_html(html, page_file):
    """Point relative assets at /preview-static and inject the visual editor."""
    html = REL_ATTR.sub(r"\1/preview-static/\2\3", html)
    inject = (
        '<script>window.__CMS_VISUAL=true;window.__CMS_PAGE_FILE=%s;</script>'
        '<script src="/static/cms-visual.js"></script>'
        % json.dumps(page_file)
    )
    if re.search(r"</body>", html, re.IGNORECASE):
        return re.sub(r"</body>", inject + "</body>", html, count=1, flags=re.IGNORECASE)
    return html + inject


def page_by_id(page_id):
    for page in SITE_PAGES:
        if page["id"] == page_id:
            return page
    return None

