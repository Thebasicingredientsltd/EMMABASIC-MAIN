"""Publish must still reach GitHub when the remote has moved on.

The CRM used to commit locally, then `git push origin HEAD`. If GitHub already
had commits we didn't, the push was rejected — and the dashboard then called
the working tree "published" because it only counted uncommitted files.

Run with:  python test_publish.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import git_status_summary, sync_and_push  # noqa: E402


def git(args, cwd, check=True):
    return subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True, check=check
    )


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cms-publish-")
        self.remote = os.path.join(self.tmp, "remote.git")
        self.local = os.path.join(self.tmp, "local")
        self.other = os.path.join(self.tmp, "other")
        git(["init", "--bare", "-b", "main", self.remote], self.tmp)
        git(["clone", self.remote, self.local], self.tmp)
        git(["config", "user.name", "CMS Test"], self.local)
        git(["config", "user.email", "cms@test.local"], self.local)
        write(os.path.join(self.local, "site.txt"), "base\n")
        git(["add", "."], self.local)
        git(["commit", "-m", "init"], self.local)
        git(["push", "-u", "origin", "HEAD"], self.local)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def clone_other(self):
        git(["clone", self.remote, self.other], self.tmp)
        git(["config", "user.name", "Other"], self.other)
        git(["config", "user.email", "other@test.local"], self.other)

    def test_status_counts_unpushed_commits_as_unpublished(self):
        write(os.path.join(self.local, "site.txt"), "local-only\n")
        git(["add", "."], self.local)
        git(["commit", "-m", "local commit"], self.local)

        status = git_status_summary(cwd=self.local)
        self.assertTrue(status["ok"])
        self.assertGreaterEqual(status["unpushed"], 1)
        self.assertGreater(status["changes"], 0)

    def test_status_is_clean_when_fully_synced(self):
        status = git_status_summary(cwd=self.local)
        self.assertTrue(status["ok"])
        self.assertEqual(status["changes"], 0)
        self.assertEqual(status["unpushed"], 0)

    def test_publish_rebases_when_remote_has_new_commits_then_pushes(self):
        """The bug: a peer pushed first, so our push was a non-fast-forward."""
        self.clone_other()
        write(os.path.join(self.other, "remote.txt"), "from github\n")
        git(["add", "."], self.other)
        git(["commit", "-m", "remote commit"], self.other)
        git(["push"], self.other)

        write(os.path.join(self.local, "local.txt"), "from crm\n")
        result = sync_and_push("CRM update", cwd=self.local)
        self.assertTrue(result["ok"], result.get("error"))

        # Remote must contain both sides of the divergence.
        cloned = os.path.join(self.tmp, "verify")
        git(["clone", self.remote, cloned], self.tmp)
        self.assertTrue(os.path.exists(os.path.join(cloned, "remote.txt")))
        self.assertTrue(os.path.exists(os.path.join(cloned, "local.txt")))

        status = git_status_summary(cwd=self.local)
        self.assertEqual(status["changes"], 0)
        self.assertEqual(status["unpushed"], 0)

    def test_publish_keeps_local_cms_data_instead_of_merged_duplicate_keys(self):
        """Git can combine two JSON edits into duplicate keys. CMS content wins."""
        rel = os.path.join(
            "Emma-Basic-The-Basic-Ingredients", "project", "data", "people.js"
        )
        write(
            os.path.join(self.local, rel),
            "{\n  \"emma\": \"new.jpg\",\n  \"pad\": \"%s\",\n  \"yoko\": \"old-yoko\"\n}\n"
            % ("x" * 80),
        )
        git(["add", "."], self.local)
        git(["commit", "-m", "add people data"], self.local)
        git(["push"], self.local)

        self.clone_other()
        write(
            os.path.join(self.other, rel),
            "{\n  \"emma\": \"new.jpg\",\n  \"emma\": \"old.jpg\",\n  \"pad\": \"%s\",\n  \"yoko\": \"old-yoko\"\n}\n"
            % ("x" * 80),
        )
        git(["add", "."], self.other)
        git(["commit", "-m", "remote merge duplicated keys"], self.other)
        git(["push"], self.other)

        # Local only edits Yoko, so a line-level rebase keeps GitHub's duplicate
        # Emma keys. The whole CMS data file must win.
        write(
            os.path.join(self.local, rel),
            "{\n  \"emma\": \"new.jpg\",\n  \"pad\": \"%s\",\n  \"yoko\": \"new-yoko\"\n}\n"
            % ("x" * 80),
        )
        result = sync_and_push("CRM photo", cwd=self.local)
        self.assertTrue(result["ok"], result.get("error"))

        cloned = os.path.join(self.tmp, "verify")
        git(["clone", self.remote, cloned], self.tmp)
        with open(os.path.join(cloned, rel), encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("new.jpg", body)
        self.assertIn("new-yoko", body)
        self.assertNotIn("old.jpg", body)
        self.assertEqual(body.count('"emma"'), 1)

    def test_publish_retries_unpushed_commits_after_a_failed_push(self):
        """Working tree is clean, but commits never made it to GitHub."""
        self.clone_other()
        write(os.path.join(self.other, "remote.txt"), "from github\n")
        git(["add", "."], self.other)
        git(["commit", "-m", "remote commit"], self.other)
        git(["push"], self.other)

        write(os.path.join(self.local, "local.txt"), "from crm\n")
        git(["add", "."], self.local)
        git(["commit", "-m", "CRM update"], self.local)
        rejected = git(["push", "origin", "HEAD"], self.local, check=False)
        self.assertNotEqual(rejected.returncode, 0)

        result = sync_and_push("retry publish", cwd=self.local)
        self.assertTrue(result["ok"], result.get("error"))

        cloned = os.path.join(self.tmp, "verify")
        git(["clone", self.remote, cloned], self.tmp)
        self.assertTrue(os.path.exists(os.path.join(cloned, "remote.txt")))
        self.assertTrue(os.path.exists(os.path.join(cloned, "local.txt")))


if __name__ == "__main__":
    unittest.main()
