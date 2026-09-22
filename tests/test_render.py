import json
import unittest
from datetime import datetime, timezone

from gitstat.aggregate import author_table, file_density, totals, weekly_heat
from gitstat.collect import Commit
from gitstat.render import render_json, render_markdown, render_text, sparkline


def make_commit(i, name="Ada", email="ada@x.com"):
    return Commit(hash=str(i), author_name=name, author_email=email, timestamp=1758000000 + i,
                  files=[(1 + i, i, "src/app.py")])


def make_report():
    commits = [make_commit(0), make_commit(1), make_commit(2, "Mehmet", "mehmet@x.com")]
    return {
        "repo": "demo",
        "totals": totals(commits),
        "authors": author_table(commits),
        "weekly": weekly_heat(commits, weeks=4, today=datetime(2025, 9, 17, tzinfo=timezone.utc)),
        "files": file_density(commits),
    }


class TestSparkline(unittest.TestCase):
    def test_proportional_blocks(self):
        line = sparkline([0, 2, 4, 8])
        self.assertEqual(len(line), 4)
        self.assertEqual(line[0], "·")
        self.assertEqual(line[-1], "█")

    def test_all_zero_is_dots(self):
        self.assertEqual(sparkline([0, 0, 0]), "···")

    def test_empty(self):
        self.assertEqual(sparkline([]), "")


class TestRenderText(unittest.TestCase):
    def test_contains_all_sections(self):
        text = render_text(make_report())
        self.assertIn("3 commits", text)
        self.assertIn("Ada", text)
        self.assertIn("src/app.py", text)
        self.assertIn("Weekly commits", text)

    def test_deterministic(self):
        self.assertEqual(render_text(make_report()), render_text(make_report()))


class TestRenderMarkdown(unittest.TestCase):
    def test_tables_render(self):
        md = render_markdown(make_report())
        self.assertIn("| Author | Commits |", md)
        self.assertIn("| Week | Commits |", md)
        self.assertIn("`src/app.py`", md)


class TestRenderJson(unittest.TestCase):
    def test_round_trips(self):
        report = make_report()
        parsed = json.loads(render_json(report))
        self.assertEqual(parsed["totals"]["commits"], report["totals"]["commits"])
        self.assertEqual(parsed["authors"][0]["email"], "ada@x.com")


if __name__ == "__main__":
    unittest.main()
