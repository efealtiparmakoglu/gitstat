"""End-to-end: build a real local git repository, run the CLI against it."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from gitstat.cli import build_report


def run_git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def make_repo(workdir):
    repo = workdir / "repo"
    repo.mkdir()
    run_git(repo, "init", "-q", "-b", "main")
    run_git(repo, "config", "user.name", "Ada Yilmaz")
    run_git(repo, "config", "user.email", "ada@example.com")

    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('v1')\n")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "first")

    (repo / "src" / "app.py").write_text("print('v2')\nprint('more')\n")
    (repo / "README.md").write_text("hello\n")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "second")

    (repo / "README.md").write_text("hello\nworld\n")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "third")
    return repo


class TestCliEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gitstat-e2e-"))
        self.repo = make_repo(self.tmp)

    def tearDown(self):
        for root, dirs, files in os.walk(self.tmp):
            for name in dirs + files:
                os.chmod(os.path.join(root, name), 0o700)
        subprocess.run(["rm", "-rf", str(self.tmp)], check=True)

    def test_build_report_on_real_repo(self):
        report = build_report(str(self.repo), since=None, top=5, weeks=8)
        self.assertEqual(report["totals"]["commits"], 3)
        self.assertEqual(report["totals"]["authors"], 1)
        readme = next(row for row in report["files"] if row["path"] == "README.md")
        self.assertEqual(readme["touches"], 2)
        self.assertEqual(readme["added"], 2)
        self.assertEqual(readme["deleted"], 0, "append-only edits delete nothing")

    def test_since_window(self):
        # full-window since keeps everything; git's --since cutoff does not
        # prune root commits, so narrower windows are not asserted here
        report = build_report(str(self.repo), since="1970-01-01", top=5, weeks=4)
        self.assertEqual(report["totals"]["commits"], 3)

    def test_cli_text_output(self):
        out = subprocess.run(
            ["python3", "-m", "gitstat.cli", str(self.repo), "--format", "text"],
            capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parent.parent)
        self.assertIn("3 commits", out.stdout)
        self.assertIn("Ada Yilmaz", out.stdout)
        self.assertIn("src/app.py", out.stdout)

    def test_cli_json_output(self):
        out = subprocess.run(
            ["python3", "-m", "gitstat.cli", str(self.repo), "--format", "json", "--weeks", "3"],
            capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parent.parent)
        parsed = json.loads(out.stdout)
        self.assertEqual(parsed["totals"]["commits"], 3)
        self.assertEqual(len(parsed["weekly"]), 3)

    def test_cli_rejects_non_repo(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        out = subprocess.run(
            ["python3", "-m", "gitstat.cli", str(empty)],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent)
        self.assertEqual(out.returncode, 1)
        self.assertIn("git failed", out.stderr)


if __name__ == "__main__":
    unittest.main()
