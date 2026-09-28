"""Under-construction mode for the Emma Basic website.

The CMS keeps a site-wide switch on `data/site.js` (`window.EB_SITE`). While it
is on, every public page sends visitors to `under-construction.html` before any
content paints, so half-finished copy is never seen.

Two pieces make that work, and both are written by the CMS rather than kept in
sync by hand:

  * the **gate** — `data/site.js` plus `components/maintenance.js`, injected as
    the first two scripts in each page's <head> so the redirect happens before
    the browser reaches the body. A page added later picks them up on the next
    save.
  * the **notice** — the headline and message on `under-construction.html`,
    written straight into the markup so the page reads correctly with no
    JavaScript and never flashes empty while `site.js` loads.
"""

from __future__ import annotations

import re
import secrets
from html import escape

# The page visitors are sent to, and the one page that must never be gated.
PAGE_FILE = "under-construction.html"

# Bump when components/maintenance.js changes so browsers refetch the gate.
GATE_SCRIPT_VERSION = "1"

GATE_START = "<!--cms-gate-start-->"
GATE_END = "<!--cms-gate-end-->"
NOTICE_START = "<!--cms-maintenance-start-->"
NOTICE_END = "<!--cms-maintenance-end-->"

GATE_RE = re.compile(
    re.escape(GATE_START) + r".*?" + re.escape(GATE_END),
    re.DOTALL,
)
CHARSET_RE = re.compile(r"<meta\b[^>]*\bcharset\b[^>]*>", re.IGNORECASE)
HEAD_OPEN_RE = re.compile(r"<head\b[^>]*>", re.IGNORECASE)

DEFAULTS = {
    "enabled": False,
    "eyebrow": "Emma Basic",
    "heading": "Under construction",
    "headingItalic": "back shortly.",
    "body": "We're updating the site. It will be back as soon as every page reads "
            "exactly as it should.",
    "note": "Our products are still on the shelves in the meantime.",
    "email": "boris@thebasicingredients.com",
    "previewKey": "",
}

TEXT_FIELDS = ("eyebrow", "heading", "headingItalic", "body", "note", "email")


def new_preview_key():
    """A short, URL-safe pass that lets the owner browse the hidden site."""
    return secrets.token_urlsafe(8)


def normalize(payload):
    """Fill in anything the stored payload is missing, without inventing copy."""
    settings = dict(DEFAULTS)
    if isinstance(payload, dict):
        for key in TEXT_FIELDS:
            if key in payload:
                settings[key] = str(payload.get(key) or "").strip()
        settings["previewKey"] = str(payload.get("previewKey") or "").strip()
        # Anything other than an explicit True leaves the site visible; a typo
        # in the data file must never take the website down.
        settings["enabled"] = payload.get("enabled") is True
    return settings


def from_data(data):
    """Read the maintenance settings off a parsed `site.js` payload."""
    if not isinstance(data, dict):
        return dict(DEFAULTS)
    return normalize(data.get("maintenance"))


def is_enabled(data):
    return from_data(data)["enabled"]


def gate_block():
    return "\n".join([
        GATE_START,
        '<script src="data/site.js"></script>',
        '<script src="components/maintenance.js?v=%s"></script>' % GATE_SCRIPT_VERSION,
        GATE_END,
    ])


def ensure_gate(html):
    """Add the gate to a page's <head> if it isn't there yet.

    Deliberately leaves an existing block alone: the `?v=` cache-buster on
    `data/site.js` is stamped by the save that follows, and rewriting the block
    on every unrelated save would strip it back off again.
    """
    if GATE_START in html:
        return html
    block = gate_block()
    anchor = CHARSET_RE.search(html) or HEAD_OPEN_RE.search(html)
    if anchor:
        return html[: anchor.end()] + "\n" + block + html[anchor.end():]
    return block + "\n" + html


def strip_gate(html):
    """Remove the gate — used for the CMS's own previews, which must keep
    rendering the real page while the website is hidden."""
    return GATE_RE.sub("", html)


def render_notice(settings):
    """Inner markup for the notice block on `under-construction.html`."""
    heading = escape(settings.get("heading") or "")
    heading_italic = escape(settings.get("headingItalic") or "")
    eyebrow = escape(settings.get("eyebrow") or "")
    body = escape(settings.get("body") or "")
    note = escape(settings.get("note") or "")
    email = escape(settings.get("email") or "")

    lines = []
    if eyebrow:
        lines.append('<p class="uc-eyebrow">%s</p>' % eyebrow)
    lines.append('<hr class="uc-rule"/>')
    if heading or heading_italic:
        lines.append("<h1 class=\"uc-title\">")
        if heading:
            lines.append('<span class="uc-title-line">%s</span>' % heading)
        if heading_italic:
            lines.append('<em class="uc-title-line uc-title-alt">%s</em>' % heading_italic)
        lines.append("</h1>")
    if body:
        lines.append('<p class="uc-body">%s</p>' % body)
    if note:
        lines.append('<p class="uc-note">%s</p>' % note)
    if email:
        lines.append(
            '<a class="uc-mail" href="mailto:%s">%s</a>' % (email, email)
        )
    return "\n".join(lines)


def apply_notice(html, settings):
    """Write the current notice copy into `under-construction.html`."""
    block = "%s\n%s\n%s" % (NOTICE_START, render_notice(settings), NOTICE_END)
    start = html.find(NOTICE_START)
    end = html.find(NOTICE_END)
    if start == -1 or end == -1 or end < start:
        return html
    return html[:start] + block + html[end + len(NOTICE_END):]


def apply_to_html(html, filename, data_key, data):
    """Keep one project HTML page in step with the maintenance settings.

    Mirrors `seo.apply_to_html`: called for every page on every save, and only
    touches what belongs to it.
    """
    if filename == PAGE_FILE:
        if data_key == "site":
            return apply_notice(html, from_data(data))
        return html
    return ensure_gate(html)
