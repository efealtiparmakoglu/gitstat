import unittest
from datetime import datetime, timezone

from gitstat.aggregate import author_table, file_density, totals, weekly_heat
from gitstat.collect import Commit


def epoch(text):
    return int(datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())


def commit(hash_, name, email, ts, files):
    return Commit(hash=hash_, author_name=name, author_email=email, timestamp=ts, files=files)


def two_authors():
    # 2026-09-15 is the Tuesday of ISO week 2026-W38
    base = epoch("2026-09-15 12:00")
    return [
        commit("1", "Ada", "ada@x.com", base, [(10, 2, "a.py")]),
        commit("2", "ada", "ADA@X.COM", base + 3600, [(1, 1, "b.py")]),
        commit("3", "Mehmet", "mehmet@x.com", base + 7200, [(0, 5, "a.py"), (3, 0, "c.py")]),
    ]


class TestAuthorTable(unittest.TestCase):
    def test_merges_by_lowercase_email(self):
        table = author_table(two_authors())
        self.assertEqual(len(table), 2)
        ada = next(row for row in table if row["email"] == "ada@x.com")
        self.assertEqual(ada["commits"], 2)
        self.assertEqual(ada["added"], 11)
        self.assertEqual(ada["deleted"], 3)
        # display name: the most frequent spelling wins
        self.assertEqual(ada["name"], "Ada")

    def test_sorted_by_commits_desc(self):
        table = author_table(two_authors())
        self.assertEqual(table[0]["commits"], 2)

    def test_first_last_dates(self):
        table = author_table(two_authors())
        self.assertEqual(table[0]["first"], "2026-09-15")
        self.assertEqual(table[0]["last"], "2026-09-15")


class TestWeeklyHeat(unittest.TestCase):
    def test_buckets_commits_by_iso_week(self):
        today = datetime(2026, 9, 16, tzinfo=timezone.utc)  # Wednesday of W38
        weeks = weekly_heat(two_authors(), weeks=4, today=today)
        self.assertEqual(len(weeks), 4)
        self.assertEqual(weeks[-1]["count"], 3, "current week holds all three")
        self.assertEqual(sum(week["count"] for week in weeks), 3)

    def test_out_of_window_commits_are_ignored(self):
        old = commit("x", "A", "a@x.com", 0, [])
        today = datetime(2026, 9, 16, tzinfo=timezone.utc)
        weeks = weekly_heat([old], weeks=2, today=today)
        self.assertEqual(sum(week["count"] for week in weeks), 0)

    def test_week_labels_are_iso(self):
        # 2026-09-22 (Tuesday) belongs to ISO week 39
        weeks = weekly_heat([], weeks=1, today=datetime(2026, 9, 22, tzinfo=timezone.utc))
        self.assertEqual(weeks[-1]["week"], "2026-W39")

    def test_commit_before_window_not_counted(self):
        today = datetime(2026, 9, 23, tzinfo=timezone.utc)  # next week (W39)
        weeks = weekly_heat(two_authors(), weeks=2, today=today)
        self.assertEqual(weeks[0]["count"], 3, "W38 is the second of the two weeks")
        self.assertEqual(weeks[-1]["count"], 0)


class TestFileDensity(unittest.TestCase):
    def test_churn_and_touches(self):
        density = file_density(two_authors())
        a_py = next(row for row in density if row["path"] == "a.py")
        self.assertEqual(a_py["touches"], 2)
        self.assertEqual(a_py["churn"], 10 + 2 + 5)

    def test_sorted_by_churn_desc_then_path(self):
        density = file_density(two_authors())
        churns = [row["churn"] for row in density]
        self.assertEqual(churns, sorted(churns, reverse=True))


class TestTotals(unittest.TestCase):
    def test_totals(self):
        totals_ = totals(two_authors())
        self.assertEqual(totals_["commits"], 3)
        self.assertEqual(totals_["authors"], 2)
        self.assertEqual(totals_["files"], 3)
        self.assertEqual(totals_["added"], 14)
        self.assertEqual(totals_["deleted"], 8)


if __name__ == "__main__":
    unittest.main()
