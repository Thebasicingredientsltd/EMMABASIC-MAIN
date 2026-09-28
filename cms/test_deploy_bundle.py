"""The online CMS only ships the files named in cms/vercel.json.

Vercel's Python runtime bundles `api/index.py` plus whatever `includeFiles`
lists — nothing else. A module that is imported but not listed passes every
local test and then fails on the live CMS, and because the import runs at load
time it takes down every route rather than one feature. So walk the import
graph from the entry point and check the list covers all of it.

Run with:  python test_deploy_bundle.py
"""

import ast
import json
import os
import unittest

CMS_DIR = os.path.dirname(os.path.abspath(__file__))
VERCEL_JSON = os.path.join(CMS_DIR, "vercel.json")
ENTRY = os.path.join("api", "index.py")


def local_module_names():
    """Modules that live in cms/ and could be imported by name."""
    return {
        name[:-3] for name in os.listdir(CMS_DIR)
        if name.endswith(".py") and not name.startswith("test_")
    }


def imported_names(path):
    """Top-level names imported by a file, including imports inside functions
    (app.py defers `from visual import ...` until it is needed)."""
    with open(path, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            names.add(node.module.split(".")[0])
    return names


def modules_the_live_cms_needs():
    available = local_module_names()
    needed = set()
    queue = [ENTRY]
    while queue:
        path = os.path.join(CMS_DIR, queue.pop())
        if not os.path.isfile(path):
            continue
        for name in imported_names(path):
            if name in available and name not in needed:
                needed.add(name)
                queue.append(name + ".py")
    return needed


def include_files():
    with open(VERCEL_JSON, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    return config["builds"][0]["config"]["includeFiles"]


class DeployBundleTests(unittest.TestCase):
    def test_every_module_the_cms_imports_is_bundled(self):
        listed = set(include_files())
        for module in sorted(modules_the_live_cms_needs()):
            self.assertIn(
                module + ".py", listed,
                "%s.py is imported by the CMS but missing from vercel.json "
                "includeFiles — the live CMS would fail to start." % module,
            )

    def test_the_walk_actually_finds_the_modules(self):
        # Guards the test itself: if the graph walk silently found nothing, the
        # check above would pass no matter what was missing.
        needed = modules_the_live_cms_needs()
        for module in ("app", "storage", "seo", "visual", "maintenance"):
            self.assertIn(module, needed)

    def test_templates_and_static_are_bundled(self):
        listed = include_files()
        self.assertIn("templates/**", listed)
        self.assertIn("static/**", listed)

    def test_every_bundled_path_exists(self):
        for entry in include_files():
            base = entry.split("/")[0].replace("**", "").strip()
            self.assertTrue(
                os.path.exists(os.path.join(CMS_DIR, base)),
                "vercel.json lists %s, which is not in cms/" % entry,
            )


if __name__ == "__main__":
    unittest.main()
