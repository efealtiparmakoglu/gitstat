import unittest

from gitstat.collect import Commit, parse_log, _clean_path, _parse_numstat


def sample_log():
    return (
        "\x1eaaa111\x1fAda Yilmaz\x1fada@example.com\x1f1758000000\n"
        "3\t1\tsrc/app.py\n"
        "10\t0\tdocs/readme.md\n"
        "\n"
        "\x1ebbb222\x1fada yilmaz\x1fADA@example.com\x1f1758100000\n"
        "-\t-\tlogo.png\n"
        "2\t2\tsrc/{old.py => app.py}\n"
        "\n"
        "\x1eccc333\x1fMehmet Kaya\x1fmehmet@example.com\x1f1758200000\n"
        "1\t0\tsrc/app.py\n"
    )


class TestParseLog(unittest.TestCase):
    def test_parses_commits_and_files(self):
        commits = parse_log(sample_log())
        self.assertEqual(len(commits), 3)
        first = commits[0]
        self.assertEqual(first.hash, "aaa111")
        self.assertEqual(first.author_name, "Ada Yilmaz")
        self.assertEqual(first.author_email, "ada@example.com")
        self.assertEqual(first.files, [(3, 1, "src/app.py"), (10, 0, "docs/readme.md")])

    def test_binary_files_count_zero(self):
        commits = parse_log(sample_log())
        binary = commits[1].files[0]
        self.assertEqual(binary, (0, 0, "logo.png"))

    def test_rename_notation_resolves_to_new_path(self):
        commits = parse_log(sample_log())
        renamed = commits[1].files[1]
        self.assertEqual(renamed, (2, 2, "src/app.py"))

    def test_malformed_lines_are_skipped(self):
        text = "\x1eddd444\x1fX\x1fx@e.com\x1f100\nnot-a-numstat\n\n"
        commits = parse_log(text)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].files, [])

    def test_parse_numstat_long_form_rename(self):
        self.assertEqual(_parse_numstat("5\t5\tbig/dir/{a.txt => b.txt}")[2], "big/dir/b.txt")
        self.assertEqual(_parse_numstat("5\t5\told.txt => new.txt")[2], "new.txt")


class TestCleanPath(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(_clean_path("a/b.py"), "a/b.py")

    def test_short_rename(self):
        self.assertEqual(_clean_path("old.py => new.py"), "new.py")

    def test_brace_rename(self):
        self.assertEqual(_clean_path("dir/{sub/old => sub/new}.py"), "dir/sub/new.py")


class TestCommitDataclass(unittest.TestCase):
    def test_files_default_empty(self):
        commit = Commit("h", "n", "e", 1)
        self.assertEqual(commit.files, [])


if __name__ == "__main__":
    unittest.main()
