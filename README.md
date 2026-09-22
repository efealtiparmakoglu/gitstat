# gitstat

Offline contribution analytics from a **local** git history — author
table, weekly heat strip, file density. Zero dependencies beyond git
itself.

```text
$ gitstat ~/code/myproject --top 5
Repository: ~/code/myproject
312 commits | 4 authors | 96 files | +18402 -3211 lines

AUTHOR                      COMMITS    ADDED  DELETED  FIRST       LAST
Ada Yilmaz                      289    17102     1988  2024-02-11  2026-09-21
Mehmet Kaya                       21     1145     1102  2024-06-02  2026-08-30

Weekly commits (last 26 weeks)
·▂▃▁▄▅▂▃▆█▅▃▄▅▆▂▃▄▁▂▅▆▇▃▄█
2026-W14 ... 2026-W39  (peak 31)

FILE                                          TOUCHES    ADDED  DELETED
src/engine.py                                     88     4210     1902
...
```

## What it measures

- **Author table** — commits, added/deleted lines and first/last commit
  per author, merged by lowercase email with the most frequent display
  name kept.
- **Weekly heat** — commit counts bucketed by ISO week for the last N
  weeks, rendered as a Unicode block sparkline (deterministic: fixed
  `today` in tests).
- **File density** — touches, added, deleted and churn (added + deleted)
  per file, so hot spots surface fast.
- **Formats** — plain text tables, GitHub-flavored markdown, or JSON for
  scripting.

## Usage

```
gitstat [REPO_PATH] [options]

  --since <date>    limit history (anything `git log --since` accepts)
  --top <N>         rows per table (default: 10)
  --weeks <N>       weeks in the heat strip (default: 26)
  --format <f>      text | markdown | json
  -V, --version
```

Fully offline: it shells out to the local `git log --numstat` and parses
with strict field separators (binary files, renames in both `a => b` and
`dir/{a => b}` notation are handled). Exit codes: 0 ok, 1 git failure /
not a repository, 2 usage error.

Known git quirk: `--since` cutoffs do not prune root commits, so very
narrow windows on tiny repos may return more than expected — that is git,
not gitstat.

## Development

```console
$ python3 -m unittest discover -s tests   # 31 tests incl. real-repo e2e
```

## License

MIT — see [LICENSE](LICENSE).
