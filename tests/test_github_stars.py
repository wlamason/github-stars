"""End-to-end tests for github_stars.py.

Each test calls the real entry points: parse_args with an argv list, then main
with a fake GitHub client. The client returns canned repos, so the tests never
touch the network.

Output filenames are already CLI arguments, and overrides.json is read from the
working directory. Tests chdir into pytest's tmp_path, which keeps that layout
and leaves the script itself unchanged.
"""

import json
from types import SimpleNamespace

from github_stars import main, parse_args


class FakeUser:
    """User stand-in. get_starred() returns the canned repos."""

    def __init__(self, repos):
        self._repos = repos

    def get_starred(self):
        return self._repos


class FakeGithub:
    """Github stand-in. Records the username passed to get_user()."""

    def __init__(self, repos):
        self._repos = repos
        self.usernames = []

    def get_user(self, username):
        self.usernames.append(username)
        return FakeUser(self._repos)


def starred(full_name, *, description, language, stars, homepage="https://example.com", open_issues=0):
    """One GitHub repository object, with the attributes get_starred_repos reads."""
    return SimpleNamespace(
        full_name=full_name,
        description=description,
        html_url=f"https://github.com/{full_name}",
        homepage=homepage,
        language=language,
        open_issues=open_issues,
        stargazers_count=stars,
    )


def as_repo(tmp_path, monkeypatch, *, hidden_languages=(), hidden_repos=(), overrides=None):
    """Use tmp_path as the repo root, including an overrides.json file."""
    monkeypatch.chdir(tmp_path)
    document = {
        "hidden_languages": list(hidden_languages),
        "hidden_repos": list(hidden_repos),
        "overrides": {} if overrides is None else overrides,
    }
    (tmp_path / "overrides.json").write_text(json.dumps(document), encoding="utf-8")
    return tmp_path


def test_markdown_groups_repos_by_language_sorted_by_stars(tmp_path, monkeypatch):
    # Given
    root = as_repo(tmp_path, monkeypatch)
    github = FakeGithub(
        [
            starred("octocat/cli", description="Command line tool", language="Rust", stars=15),
            starred("octocat/http", description="HTTP client", language="Python", stars=40),
            starred("octocat/notes", description=None, language="Python", stars=2),
            starred("octocat/notebook", description="Example notebook", language="Jupyter Notebook", stars=8),
            starred("octocat/plain", description="Plain notes", language=None, stars=1),
        ]
    )

    # When
    args = parse_args(["octocat"])
    main(args, github)

    # Then
    assert github.usernames == ["octocat"]
    assert args.filename == "stars.md"
    assert args.write_json is False
    assert (root / "stars.md").read_text(encoding="utf-8") == (
        "# ⭐ Stars\n"
        "\n"
        "- [Jupyter Notebook](#jupyter-notebook)\n"
        "- [Python](#python)\n"
        "- [Rust](#rust)\n"
        "- [Txt](#txt)\n"
        "\n"
        "# Jupyter Notebook\n"
        "\n"
        "- ⭐8 [octocat/notebook](https://github.com/octocat/notebook) - Example notebook\n"
        "\n"
        "# Python\n"
        "\n"
        "- ⭐40 [octocat/http](https://github.com/octocat/http) - HTTP client\n"
        "- ⭐2 [octocat/notes](https://github.com/octocat/notes)\n"
        "\n"
        "# Rust\n"
        "\n"
        "- ⭐15 [octocat/cli](https://github.com/octocat/cli) - Command line tool\n"
        "\n"
        "# Txt\n"
        "\n"
        "- ⭐1 [octocat/plain](https://github.com/octocat/plain) - Plain notes\n"
    )
    assert not (root / "github_stars.json").exists()


def test_markdown_anchors_for_c_plus_plus_and_c_sharp(tmp_path, monkeypatch):
    # Given
    root = as_repo(tmp_path, monkeypatch)
    github = FakeGithub(
        [
            starred("octocat/cpp", description="Plus plus", language="C++", stars=3),
            starred("octocat/cs", description="Sharp", language="C#", stars=2),
            starred("octocat/c", description="Plain C", language="C", stars=1),
        ]
    )

    # When
    args = parse_args(["octocat"])
    main(args, github)

    # Then
    assert (root / args.filename).read_text(encoding="utf-8") == (
        "# ⭐ Stars\n"
        "\n"
        "- [C](#c)\n"
        "- [C#](#c-2)\n"
        "- [C++](#c-1)\n"
        "\n"
        "# C\n"
        "\n"
        "- ⭐1 [octocat/c](https://github.com/octocat/c) - Plain C\n"
        "\n"
        "# C#\n"
        "\n"
        "- ⭐2 [octocat/cs](https://github.com/octocat/cs) - Sharp\n"
        "\n"
        "# C++\n"
        "\n"
        "- ⭐3 [octocat/cpp](https://github.com/octocat/cpp) - Plus plus\n"
    )


def test_json_flag_writes_fetched_repo_data(tmp_path, monkeypatch):
    # Given
    root = as_repo(tmp_path, monkeypatch)
    github = FakeGithub(
        [
            starred(
                "octocat/http",
                description="HTTP client",
                language="Python",
                stars=40,
                homepage="https://octocat.dev",
                open_issues=7,
            ),
            starred("octocat/plain", description=None, language=None, stars=1, homepage=None),
        ]
    )

    # When
    args = parse_args(["--json", "octocat"])
    main(args, github)

    # Then
    assert args.write_json is True
    assert args.json_filename == "github_stars.json"
    assert json.loads((root / "github_stars.json").read_text(encoding="utf-8")) == {
        "octocat/http": {
            "repo_name": "octocat/http",
            "description": "HTTP client",
            "url": "https://github.com/octocat/http",
            "homepage": "https://octocat.dev",
            "language": "Python",
            "open_issues": 7,
            "stars": 40,
        },
        "octocat/plain": {
            "repo_name": "octocat/plain",
            "description": None,
            "url": "https://github.com/octocat/plain",
            "homepage": None,
            "language": None,
            "open_issues": 0,
            "stars": 1,
        },
    }
    markdown = (root / "stars.md").read_text(encoding="utf-8")
    assert "[octocat/http](https://github.com/octocat/http) - HTTP client" in markdown
    assert "# Txt\n" in markdown


def test_custom_markdown_and_json_filenames(tmp_path, monkeypatch):
    # Given
    root = as_repo(tmp_path, monkeypatch)
    github = FakeGithub([starred("octocat/http", description="HTTP client", language="Python", stars=40)])

    # When
    args = parse_args(["--filename", "mine.md", "--json", "--json-filename", "mine.json", "octocat"])
    main(args, github)

    # Then
    assert (root / "mine.md").read_text(encoding="utf-8") == (
        "# ⭐ Stars\n"
        "\n"
        "- [Python](#python)\n"
        "\n"
        "# Python\n"
        "\n"
        "- ⭐40 [octocat/http](https://github.com/octocat/http) - HTTP client\n"
    )
    assert json.loads((root / "mine.json").read_text(encoding="utf-8")) == {
        "octocat/http": {
            "repo_name": "octocat/http",
            "description": "HTTP client",
            "url": "https://github.com/octocat/http",
            "homepage": "https://example.com",
            "language": "Python",
            "open_issues": 0,
            "stars": 40,
        }
    }
    assert not (root / "stars.md").exists()
    assert not (root / "github_stars.json").exists()


def test_overrides_hide_entries_and_replace_repo_fields(tmp_path, monkeypatch):
    # Given
    root = as_repo(
        tmp_path,
        monkeypatch,
        hidden_languages=["Java"],
        hidden_repos=["octocat/secret"],
        overrides={"octocat/http": {"description": "Overridden description"}},
    )
    github = FakeGithub(
        [
            starred("octocat/http", description="Fetched description", language="Python", stars=40),
            starred("octocat/secret", description="Hidden repo", language="Python", stars=50),
            starred("octocat/jvm", description="Hidden language", language="Java", stars=9),
        ]
    )

    # When
    args = parse_args(["--json", "octocat"])
    main(args, github)

    # Then
    assert (root / "stars.md").read_text(encoding="utf-8") == (
        "# ⭐ Stars\n"
        "\n"
        "- [Python](#python)\n"
        "\n"
        "# Python\n"
        "\n"
        "- ⭐40 [octocat/http](https://github.com/octocat/http) - Overridden description\n"
    )
    # JSON is written from the fetched repos, before overrides.json is applied.
    assert json.loads((root / "github_stars.json").read_text(encoding="utf-8")) == {
        "octocat/http": {
            "repo_name": "octocat/http",
            "description": "Fetched description",
            "url": "https://github.com/octocat/http",
            "homepage": "https://example.com",
            "language": "Python",
            "open_issues": 0,
            "stars": 40,
        },
        "octocat/secret": {
            "repo_name": "octocat/secret",
            "description": "Hidden repo",
            "url": "https://github.com/octocat/secret",
            "homepage": "https://example.com",
            "language": "Python",
            "open_issues": 0,
            "stars": 50,
        },
        "octocat/jvm": {
            "repo_name": "octocat/jvm",
            "description": "Hidden language",
            "url": "https://github.com/octocat/jvm",
            "homepage": "https://example.com",
            "language": "Java",
            "open_issues": 0,
            "stars": 9,
        },
    }
