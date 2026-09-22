"""Read commit history from a local repository via the git binary.

The tool is fully offline: it shells out to `git log` on a local checkout
and never touches the network.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

# Field and record separators chosen to be illegal inside real data.
RS = "\x1e"
US = "\x1f"
_LOG_FORMAT = RS + "%H" + US + "%an" + US + "%ae" + US + "%at"


@dataclass
class Commit:
    hash: str
    author_name: str
    author_email: str
    timestamp: int
    files: list[tuple[int, int, str]] = field(default_factory=list)


def collect(repo: str = ".", since: str | None = None, until: str | None = None) -> list[Commit]:
    """Return the commit list of `repo`, oldest history included."""
    args = ["git", "-C", repo, "log", "--no-merges", "--pretty=" + _LOG_FORMAT, "--numstat"]
    if since:
        args += ["--since", since]
    if until:
        args += ["--until", until]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("git failed: " + result.stderr.strip())
    return parse_log(result.stdout)


def parse_log(text: str) -> list[Commit]:
    """Parse `git log --numstat` output produced with the separators above.

    Note: split("\\n") is deliberate — str.splitlines() would treat the
    \\x1e record separator itself as a line boundary.
    """
    commits: list[Commit] = []
    current: Commit | None = None
    for line in text.split("\n"):
        if not line.strip():
            continue
        if line.startswith(RS):
            parts = line[1:].split(US)
            current = Commit(
                hash=parts[0],
                author_name=parts[1],
                author_email=parts[2],
                timestamp=int(parts[3]),
            )
            commits.append(current)
            continue
        if current is None:
            continue
        parsed = _parse_numstat(line)
        if parsed is not None:
            current.files.append(parsed)
    return commits


def _parse_numstat(line: str) -> tuple[int, int, str] | None:
    fields = line.split("\t")
    if len(fields) < 3:
        return None
    added = _stat_number(fields[0])
    deleted = _stat_number(fields[1])
    path = _clean_path("\t".join(fields[2:]))
    return added, deleted, path


def _stat_number(value: str) -> int:
    # binary files show "-" for both counts
    try:
        return int(value)
    except ValueError:
        return 0


def _clean_path(raw: str) -> str:
    """Flatten git rename notation to the destination path.

    `old => new` and `dir/{old => new}` both reduce to the new side,
    keeping whatever surrounds the braces.
    """
    raw = raw.strip()
    if "=>" not in raw:
        return raw
    if "{" in raw and "}" in raw:
        head, _, tail = raw.partition("{")
        inside, _, suffix = tail.rpartition("}")
        return head + inside.split("=>")[1].strip() + suffix
    return raw.split("=>")[1].strip()
