"""Storage backends for the Emma Basic CMS.

The CMS reads the site's content/data files and images from the repository and
writes them back. Historically it only ever touched the local filesystem and
published via `git push`. To let the CMS run *online* (e.g. as a Vercel
serverless function, where the filesystem is read-only), this module abstracts
all persistence behind a small interface with two backends:

    CMS_BACKEND=local   (default) — read/write files on disk. Publishing is
                        still done separately via `git` (the Publish button).

    CMS_BACKEND=github  — read files via the GitHub API and write them by
                        committing directly to a branch using the GitHub Git
                        Data API. Each save is a single atomic commit, which
                        (when the repo is connected to Vercel) auto-deploys the
                        live site. No local git checkout is required.

All paths passed to this module are *repository-relative* using forward slashes
(e.g. "Emma-Basic-The-Basic-Ingredients/project/data/catalog.js").

Only the Python standard library is used (urllib) so there is no extra
dependency to install on the serverless runtime.
"""

import base64
import json
import os
import time
import urllib.error
import urllib.request

BACKEND = os.environ.get("CMS_BACKEND", "local").strip().lower()

# Repo root = parent of this cms/ directory. Used only by the local backend.
_CMS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_CMS_DIR)

# GitHub backend configuration (only required when CMS_BACKEND=github).
GITHUB_REPO = os.environ.get("GITHUB_REPO", "Thebasicingredientsltd/EMMABASIC-MAIN").strip()
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_API = os.environ.get("GITHUB_API", "https://api.github.com").rstrip("/")

_COMMIT_AUTHOR_NAME = os.environ.get("CMS_COMMIT_NAME", "Emma Basic CMS")
_COMMIT_AUTHOR_EMAIL = os.environ.get("CMS_COMMIT_EMAIL", "cms@emmabasic.local")


class StorageError(RuntimeError):
    pass


def is_github():
    return BACKEND == "github"


# ---------------------------------------------------------------------------
# Local filesystem backend helpers
# ---------------------------------------------------------------------------
def _abs(relpath):
    return os.path.join(REPO_ROOT, *relpath.split("/"))


def _local_read_text(relpath):
    with open(_abs(relpath), "r", encoding="utf-8") as fh:
        return fh.read()


def _local_read_bytes(relpath):
    path = _abs(relpath)
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def _local_get_size(relpath):
    path = _abs(relpath)
    return os.path.getsize(path) if os.path.isfile(path) else None


def _local_list_dir(relpath):
    path = _abs(relpath)
    return os.listdir(path) if os.path.isdir(path) else []


def _local_persist(changes, message=None):
    """changes: list of (relpath, data, is_binary). Writes each to disk."""
    for relpath, data, is_binary in changes:
        path = _abs(relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if is_binary:
            with open(path, "wb") as fh:
                fh.write(data if isinstance(data, (bytes, bytearray)) else data.encode("utf-8"))
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(data)
    return {"ok": True, "count": len(changes)}


# ---------------------------------------------------------------------------
# GitHub API backend
# ---------------------------------------------------------------------------
def _gh_request(method, url, body=None):
    if not GITHUB_TOKEN:
        raise StorageError("GITHUB_TOKEN is not set — cannot talk to GitHub.")
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + GITHUB_TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "emma-basic-cms")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            pass
        raise StorageError("GitHub %s %s -> %s %s" % (method, url, exc.code, detail))


def _gh_url(path):
    return "%s/repos/%s/%s" % (GITHUB_API, GITHUB_REPO, path.lstrip("/"))


def _gh_contents(relpath):
    """Return the contents API payload for a path (or None on 404)."""
    url = _gh_url("contents/%s?ref=%s" % (urllib.request.quote(relpath), GITHUB_BRANCH))
    try:
        return _gh_request("GET", url)
    except StorageError as exc:
        if " 404 " in str(exc):
            return None
        raise


def _gh_read_text(relpath):
    payload = _gh_contents(relpath)
    if not payload:
        raise StorageError("File not found on GitHub: %s" % relpath)
    content = payload.get("content", "")
    encoding = payload.get("encoding", "base64")
    if content and encoding == "base64":
        return base64.b64decode(content).decode("utf-8")
    # Large files come back without inline content — fetch the blob.
    sha = payload.get("sha")
    blob = _gh_request("GET", _gh_url("git/blobs/%s" % sha))
    return base64.b64decode(blob.get("content", "")).decode("utf-8")


def _gh_read_bytes(relpath):
    payload = _gh_contents(relpath)
    if not payload:
        return None
    content = payload.get("content", "")
    if content and payload.get("encoding") == "base64":
        return base64.b64decode(content)
    sha = payload.get("sha")
    if not sha:
        return None
    blob = _gh_request("GET", _gh_url("git/blobs/%s" % sha))
    return base64.b64decode(blob.get("content", ""))


def _gh_get_size(relpath):
    payload = _gh_contents(relpath)
    if not payload:
        return None
    return payload.get("size")


def _gh_list_dir(relpath):
    payload = _gh_contents(relpath)
    if not isinstance(payload, list):
        return []
    return [entry.get("name") for entry in payload if entry.get("name")]


def _gh_persist(changes, message=None):
    """Commit a set of file changes as ONE commit via the Git Data API.

    changes: list of (relpath, data, is_binary). Text data is committed as
    utf-8; binary data (bytes) is committed as base64.
    """
    if not changes:
        return {"ok": True, "count": 0, "commit": None}

    ref = _gh_request("GET", _gh_url("git/ref/heads/%s" % GITHUB_BRANCH))
    base_sha = ref["object"]["sha"]
    base_commit = _gh_request("GET", _gh_url("git/commits/%s" % base_sha))
    base_tree = base_commit["tree"]["sha"]

    tree_entries = []
    for relpath, data, is_binary in changes:
        if is_binary:
            payload = {
                "content": base64.b64encode(
                    data if isinstance(data, (bytes, bytearray)) else data.encode("utf-8")
                ).decode("ascii"),
                "encoding": "base64",
            }
        else:
            payload = {"content": data, "encoding": "utf-8"}
        blob = _gh_request("POST", _gh_url("git/blobs"), payload)
        tree_entries.append({
            "path": relpath,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })

    new_tree = _gh_request("POST", _gh_url("git/trees"), {
        "base_tree": base_tree,
        "tree": tree_entries,
    })
    commit = _gh_request("POST", _gh_url("git/commits"), {
        "message": message or "CMS update",
        "tree": new_tree["sha"],
        "parents": [base_sha],
        "author": {
            "name": _COMMIT_AUTHOR_NAME,
            "email": _COMMIT_AUTHOR_EMAIL,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    })
    _gh_request("PATCH", _gh_url("git/refs/heads/%s" % GITHUB_BRANCH), {
        "sha": commit["sha"],
        "force": False,
    })
    return {"ok": True, "count": len(changes), "commit": commit["sha"]}


# ---------------------------------------------------------------------------
# Public interface (dispatches on BACKEND)
# ---------------------------------------------------------------------------
def read_text(relpath):
    return _gh_read_text(relpath) if is_github() else _local_read_text(relpath)


def read_bytes(relpath):
    return _gh_read_bytes(relpath) if is_github() else _local_read_bytes(relpath)


def get_size(relpath):
    return _gh_get_size(relpath) if is_github() else _local_get_size(relpath)


def list_dir(relpath):
    return _gh_list_dir(relpath) if is_github() else _local_list_dir(relpath)


def persist(changes, message=None):
    """Persist a batch of file changes.

    changes: iterable of (relpath, data, is_binary).
      - local: writes each file to disk (publishing happens separately).
      - github: commits all of them in a single commit and returns the sha.
    """
    changes = list(changes)
    return _gh_persist(changes, message) if is_github() else _local_persist(changes, message)
