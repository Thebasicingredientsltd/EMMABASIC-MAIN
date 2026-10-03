"""The online CMS only ships the files named in cms/vercel.json.

Vercel's Python runtime bundles `api/index.py` plus whatever `includeFiles`
lists — nothing else. A module that is imported but not listed passes every
local test and then fails on the live CMS, and because the import runs at load
time it takes down every route rather than one feature. So walk the import
graph from the entry point and check the list covers all of it.

Run with:  python test_deploy_bundle.py
"""

import ast
import fnmatch
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

    def test_root_vercelignore_hides_secrets_but_not_what_the_cms_needs(self):
        repo = os.path.dirname(CMS_DIR)
        with open(os.path.join(repo, ".vercelignore"), encoding="utf-8") as fh:
            patterns = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

        def ignored(relpath):
            parts = relpath.split("/")
            for pat in patterns:
                pat = pat.rstrip("/")
                if "/" in pat:
                    if relpath == pat or relpath.startswith(pat + "/"):
                        return True
                elif any(fnmatch.fnmatch(part, pat) for part in parts):
                    return True
            return False

        for secret in ("cms/.env", "cms/.env.local", ".env.local",
                       "Product-nutritional-ingredients-data/a.xlsx",
                       "the-basic-ingredients-page/How_to_Order.docx", "notes.xlsx"):
            self.assertTrue(ignored(secret), secret)

        needed = ["cms/vercel.json", "cms/requirements.txt", "cms/api/index.py"]
        for entry in include_files():
            base = entry.split("/")[0]
            for root, _dirs, files in os.walk(os.path.join(CMS_DIR, base)):
                for name in files:
                    rel = os.path.relpath(os.path.join(root, name), repo).replace(os.sep, "/")
                    if "__pycache__" not in rel:
                        needed.append(rel)
            if not entry.endswith("**"):
                needed.append("cms/" + entry)
        project = os.path.join(repo, "Emma-Basic-The-Basic-Ingredients", "project")
        for root, _dirs, files in os.walk(project):
            for name in files:
                needed.append(os.path.relpath(os.path.join(root, name), repo).replace(os.sep, "/"))
        for rel in needed:
            self.assertFalse(ignored(rel), "%s would be left out of the deploy" % rel)

    def test_every_bundled_path_exists(self):
        for entry in include_files():
            base = entry.split("/")[0].replace("**", "").strip()
            self.assertTrue(
                os.path.exists(os.path.join(CMS_DIR, base)),
                "vercel.json lists %s, which is not in cms/" % entry,
            )


if __name__ == "__main__":
    unittest.main()
