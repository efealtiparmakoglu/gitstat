"""Report rendering: plain text, markdown and JSON."""

from __future__ import annotations

import json

# Unicode block ramp for the weekly sparkline; zero renders as a middle
# dot so empty weeks stay visible.
BLOCKS = ["·", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]


def sparkline(counts: list[int]) -> str:
    if not counts:
        return ""
    peak = max(counts)
    if peak == 0:
        return BLOCKS[0] * len(counts)
    return "".join(BLOCKS[round(count * (len(BLOCKS) - 1) / peak)] for count in counts)


def render_text(report: dict) -> str:
    lines: list[str] = []
    totals = report["totals"]
    lines.append(f"Repository: {report['repo']}")
    lines.append(
        f"{totals['commits']} commits | {totals['authors']} authors | "
        f"{totals['files']} files | +{totals['added']} -{totals['deleted']} lines"
    )
    lines.append("")

    lines.append(f"{'AUTHOR':<24} {'COMMITS':>7} {'ADDED':>8} {'DELETED':>8}  FIRST       LAST")
    for row in report["authors"]:
        lines.append(
            f"{row['name']:<24.24} {row['commits']:>7} {row['added']:>8} "
            f"{row['deleted']:>8}  {row['first']}  {row['last']}"
        )
    lines.append("")

    weeks = report["weekly"]
    lines.append(f"Weekly commits (last {len(weeks)} weeks)")
    lines.append(sparkline([week["count"] for week in weeks]))
    if weeks:
        lines.append(f"{weeks[0]['week']} ... {weeks[-1]['week']}  "
                     f"(peak {max(week['count'] for week in weeks)})")
    lines.append("")

    lines.append(f"{'FILE':<44} {'TOUCHES':>7} {'ADDED':>8} {'DELETED':>8}")
    for row in report["files"]:
        lines.append(
            f"{row['path']:<44.44} {row['touches']:>7} {row['added']:>8} {row['deleted']:>8}"
        )
    return "\n".join(lines)


def render_markdown(report: dict) -> str:
    lines: list[str] = [f"# gitstat — {report['repo']}", ""]
    totals = report["totals"]
    lines.append(f"**{totals['commits']}** commits, **{totals['authors']}** authors, "
                 f"**+{totals['added']} / -{totals['deleted']}** lines")
    lines.append("")
    lines.append("| Author | Commits | Added | Deleted | First | Last |")
    lines.append("|---|---:|---:|---:|---|---|")
    for row in report["authors"]:
        lines.append(
            f"| {row['name']} | {row['commits']} | {row['added']} | {row['deleted']} "
            f"| {row['first']} | {row['last']} |"
        )
    lines.append("")
    lines.append("| Week | Commits |")
    lines.append("|---|---:|")
    for week in report["weekly"]:
        lines.append(f"| {week['week']} | {week['count']} |")
    lines.append("")
    lines.append("| File | Touches | Added | Deleted |")
    lines.append("|---|---:|---:|---:|")
    for row in report["files"]:
        lines.append(f"| `{row['path']}` | {row['touches']} | {row['added']} | {row['deleted']} |")
    return "\n".join(lines)


def render_json(report: dict) -> str:
    return json.dumps(report, indent=2, sort_keys=False)
