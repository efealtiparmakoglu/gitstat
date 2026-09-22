"""Aggregations over the collected commit list: authors, weekly heat,
file density and totals."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from .collect import Commit


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def author_table(commits: list[Commit]) -> list[dict]:
    """Per-author totals keyed by lowercase email; display name is the
    most frequently seen spelling. Sorted by commit count descending."""
    stats: dict[str, dict] = {}
    for commit in commits:
        key = commit.author_email.lower()
        entry = stats.setdefault(
            key,
            {"email": key, "names": Counter(), "commits": 0, "added": 0, "deleted": 0,
             "first": commit.timestamp, "last": commit.timestamp},
        )
        entry["names"][commit.author_name] += 1
        entry["commits"] += 1
        for added, deleted, _path in commit.files:
            entry["added"] += added
            entry["deleted"] += deleted
        entry["first"] = min(entry["first"], commit.timestamp)
        entry["last"] = max(entry["last"], commit.timestamp)
    table = []
    for entry in stats.values():
        table.append({
            "name": entry["names"].most_common(1)[0][0],
            "email": entry["email"],
            "commits": entry["commits"],
            "added": entry["added"],
            "deleted": entry["deleted"],
            "first": _iso(entry["first"]),
            "last": _iso(entry["last"]),
        })
    table.sort(key=lambda row: (-row["commits"], row["email"]))
    return table


def _week_start(dt: datetime) -> datetime:
    """Monday 00:00 UTC of the ISO week containing dt."""
    day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return day - timedelta(days=day.weekday())


def weekly_heat(commits: list[Commit], weeks: int = 26, today: datetime | None = None) -> list[dict]:
    """Commit counts bucketed by ISO week for the last `weeks` weeks
    (including the current one). Older commits fall outside the window."""
    if weeks <= 0:
        return []
    now = today or datetime.now(tz=timezone.utc)
    current_week = _week_start(now)
    buckets: dict[datetime, int] = {}
    starts = []
    for offset in range(weeks - 1, -1, -1):
        start = current_week - timedelta(weeks=offset)
        buckets[start] = 0
        starts.append(start)
    for commit in commits:
        start = _week_start(datetime.fromtimestamp(commit.timestamp, tz=timezone.utc))
        if start in buckets:
            buckets[start] += 1
    return [
        {
            "week": start.strftime("%G-W%V"),
            "start": start.strftime("%Y-%m-%d"),
            "count": buckets[start],
        }
        for start in starts
    ]


def file_density(commits: list[Commit]) -> list[dict]:
    """Per-file churn: how often a file was touched and how many lines
    moved in it. Sorted by churn (added + deleted) descending."""
    stats: dict[str, dict] = {}
    for commit in commits:
        for added, deleted, path in commit.files:
            entry = stats.setdefault(path, {"touches": 0, "added": 0, "deleted": 0})
            entry["touches"] += 1
            entry["added"] += added
            entry["deleted"] += deleted
    table = [
        {
            "path": path,
            "touches": entry["touches"],
            "added": entry["added"],
            "deleted": entry["deleted"],
            "churn": entry["added"] + entry["deleted"],
        }
        for path, entry in stats.items()
    ]
    table.sort(key=lambda row: (-row["churn"], row["path"]))
    return table


def totals(commits: list[Commit]) -> dict:
    files = set()
    added = 0
    deleted = 0
    for commit in commits:
        for a, d, path in commit.files:
            files.add(path)
            added += a
            deleted += d
    return {
        "commits": len(commits),
        "authors": len({c.author_email.lower() for c in commits}),
        "files": len(files),
        "added": added,
        "deleted": deleted,
    }
