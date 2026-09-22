"""Command line entry point."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .aggregate import author_table, file_density, totals, weekly_heat
from .collect import collect
from .render import render_json, render_markdown, render_text

USAGE = """gitstat v%(version)s — offline contribution analytics from a local git history

USAGE
  gitstat [REPO_PATH] [options]

OPTIONS
  --since <date>    limit history (anything `git log --since` accepts)
  --top <N>         rows per table (default: 10)
  --weeks <N>       weeks in the heat strip (default: 26)
  --format <f>      text | markdown | json (default: text)
  -h, --help        show this help
  -V, --version     print version

Reads the repository with the local git binary; no network access."""


def build_report(repo: str, since: str | None, top: int, weeks: int) -> dict:
    commits = collect(repo, since=since)
    if not commits:
        raise SystemExit("gitstat: no commits found in '%s'" % repo)
    return {
        "repo": repo,
        "totals": totals(commits),
        "authors": author_table(commits)[:top],
        "weekly": weekly_heat(commits, weeks=weeks),
        "files": file_density(commits)[:top],
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(add_help=False, description="gitstat")
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--since")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--weeks", type=int, default=26)
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-V", "--version", action="store_true")
    args = parser.parse_args(argv)

    if args.help:
        print(USAGE % {"version": __version__})
        return
    if args.version:
        print("gitstat", __version__)
        return
    if args.top < 1 or args.weeks < 1:
        parser.exit(2, "gitstat: --top and --weeks expect positive integers\n")

    try:
        report = build_report(args.repo, args.since, args.top, args.weeks)
    except RuntimeError as error:
        parser.exit(1, "gitstat: %s\n" % error)

    if args.format == "json":
        print(render_json(report))
    elif args.format == "markdown":
        print(render_markdown(report))
    else:
        print(render_text(report))


if __name__ == "__main__":
    main(sys.argv[1:])
