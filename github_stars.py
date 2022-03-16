import argparse
from contextlib import contextmanager
import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
import time
from typing import Dict, List, Set, Tuple, TypedDict, Union

from github import Github


logger = logging.getLogger(__name__)


@dataclass
class Arguments:
    """Passed in CLI arguments."""

    verbose: int
    filename: str
    write_json: bool
    json_filename: str
    username: str


class Repo(TypedDict):
    """Github repository details."""

    repo_name: str
    description: str
    url: str
    homepage: str
    language: str
    open_issues: int
    stars: int


@contextmanager
def time_it(msg: str):
    start = time.perf_counter_ns()
    try:
        yield
    finally:
        end = time.perf_counter_ns()
        logger.info(f"{msg} took {(end - start) / 1_000_000}ms")


def write_md(language_to_repos: Dict[str, Repo], filename: str, hidden_languages: Set[str], hidden_repos: Set[str]) -> None:
    """Write markdown file showcasing a user's github stars."""
    with open(filename, "w") as f:
        f.write("# ⭐ Stars\n\n")

        # Table of Contents
        for language in language_to_repos:
            if language in hidden_languages:
                continue

            lang_link = language.lower().replace(" ", "-")
            if language == "C++":
                lang_link = "c-1"
            elif language == "C#":
                lang_link = "c-2"

            f.write(f"- [{language}](#{lang_link})\n")

        # Language sections
        for language in language_to_repos:
            if language in hidden_languages:
                continue

            f.write(f"\n# {language}\n\n")

            for repo in sorted(language_to_repos[language], key=lambda x: x["stars"], reverse=True):
                if repo["repo_name"] in hidden_repos:
                    continue

                description = f" - {repo['description']}" if repo['description'] is not None else ""
                f.write(f"- ⭐{repo['stars']} [{repo['repo_name']}]({repo['url']}){description}\n")


def update_with_overrides(repo_name_to_repo: Dict[str, Repo], overrides: Dict[str, Repo]) -> None:
    """Update repos with override values."""
    for repo_name in repo_name_to_repo.keys() & overrides.keys():
        repo_name_to_repo[repo_name].update(overrides[repo_name])


def get_repo_overrides() -> Dict[str, Union[List[str], Dict[str, Repo]]]:
    """Get repo overrides from overrides.json"""
    with open("overrides.json", "r") as f:
        repo_overrides = json.load(f)
        logger.debug(f"repo_overrides = {repo_overrides}")
        return repo_overrides


def write_json(repo_name_to_repo: Dict[str, Repo], json_filename: str) -> None:
    """Write repo_name_to_repo to file as json."""
    with open(json_filename, "w") as f:
        json.dump(repo_name_to_repo, f, indent=4)


def index_starred_repos(repos: List[Repo]) -> Tuple[Dict[str, Repo], Dict[str, Repo]]:
    """Index repos by repo name and language."""

    # Create datastructures from retrieved repo data
    repo_name_to_repo = {}
    language_to_repos = defaultdict(list)
    for repo in repos:
        repo_name_to_repo[repo["repo_name"]] = repo
        language = repo["language"] if repo["language"] is not None else "Txt"
        language_to_repos[language].append(repo)

    # Sort the dictionary
    language_to_repos = dict(sorted(language_to_repos.items()))

    logger.debug(f"repo_name_to_repo = {repo_name_to_repo}")
    logger.debug(f"language_to_repos = {language_to_repos}")

    return repo_name_to_repo, language_to_repos


def get_starred_repos(username: str) -> List[Repo]:
    """Get starred repos for given username from Github API."""
    g = Github(os.environ.get("GIT_TOKEN", ""))

    with time_it("get_user"):
        user = g.get_user(username)

    with time_it("get_starred"):
        starred_repos = user.get_starred()

    logger.debug(f"starred_repos = {starred_repos}")

    # Retrieve repo data from github api
    repos: List[Repo] = []
    with time_it("enumerate paginated repos"):
        for repo in starred_repos:
            repos.append(
                Repo(
                    repo_name=repo.full_name,
                    description=repo.description,
                    url=repo.html_url,
                    homepage=repo.homepage,
                    language=repo.language,
                    open_issues=repo.open_issues,
                    stars=repo.stargazers_count,
                )
            )

    logger.debug(f"repos = {repos}")

    return repos

@time_it("github_stars.py")
def main(args: Arguments) -> None:
    """Main processing logic."""
    repos = get_starred_repos(args.username)
    logger.info(f"retrieved starred repos for user {args.username}")

    repo_name_to_repo, language_to_repos = index_starred_repos(repos)
    logger.info(f"indexed repos by repo name and language")

    if args.write_json:
        write_json(repo_name_to_repo, args.json_filename)
        logger.info(f"wrote repo_name_to_repo to {args.json_filename}")

    repo_overrides = get_repo_overrides()
    logger.info("retrieved repo_overrides")

    hidden_languages = set(repo_overrides.get("hidden_languages", []))
    logger.debug(f"hidden_languages = {hidden_languages}")
    logger.info("hidden_languages converted to set")

    hidden_repos = set(repo_overrides.get("hidden_repos", []))
    logger.debug(f"hidden_repos = {hidden_repos}")
    logger.info("hidden_repos converted to set")

    update_with_overrides(repo_name_to_repo, repo_overrides.get("overrides", {}))
    logger.debug(f"repo_name_to_repo after update_existing = {repo_name_to_repo}")
    logger.info("updated repo_name_to_repo with repo_overrides['overrides']")

    write_md(language_to_repos, args.filename, hidden_languages, hidden_repos)
    logger.info(f"wrote markdown file {args.filename}")


def config_logger(verbosity: int):
    """Configure logging script."""
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(verbosity, len(levels) - 1)]  # cap to last level index
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler("github_stars.log")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def parse_args() -> Arguments:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Create markdown file showcasing a user's github stars.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-f", "--filename", default="stars.md", help="Output markdown filename.")
    parser.add_argument("-j", "--json", action="store_true", help="Write json file with starred repo data.")
    parser.add_argument("-jf", "--json-filename", default="github_stars.json", help="Output json filename.")
    parser.add_argument("username", help="User to extract stars from.")
    args = parser.parse_args()
    return Arguments(args.verbose, args.filename, args.json, args.json_filename, args.username)


if __name__ == "__main__":
    args = parse_args()
    config_logger(args.verbose)
    main(args)
