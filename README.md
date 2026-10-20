# github-stars
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/wlamason/github-stars/blob/main/LICENSE)

> ⭐Create a searchable view of your github stars. Runs daily with github actions.

[Click here for an example.](https://github.com/wlamason/github-stars/blob/main/stars.md)

## Basic Usage

```
uv run python github_stars.py
```

## Additional Options

```
uv run python github_stars.py --help
usage: github_stars.py [-h] [-v] [-f FILENAME] [-j] [-jf JSON_FILENAME] username

Create markdown file showcasing a user's github stars.

positional arguments:
  username              User to extract stars from.

options:
  -h, --help            show this help message and exit
  -v, --verbose
  -f, --filename FILENAME
                        Output markdown filename.
  -j, --json            Write json file with starred repo data.
  -jf, --json-filename JSON_FILENAME
                        Output json filename.
```

## Overriding Default Output

To override default output behavior, you can supply an `overrides.json` file. See [`overrides.json`](https://github.com/wlamason/github-stars/blob/main/overrides.json) for an example. [`overrides.template.json`](https://github.com/wlamason/github-stars/blob/main/overrides.template.json) is supplied as an empty template.

Attributes in `overrides.json`:

- `hidden_languages`: A list of programming languages to exclude from output.
- `hidden_repos`: A list of repos to exclude from output. Format is `<user>/<repo>`.
- `overrides`: Key value pairs of repo in `<user>/<repo>` format to object. The object contains key value pairs that override the [`Repo` class](https://github.com/wlamason/github-stars/blob/main/github_stars.py#L27-L36) in [`github_stars.py`](https://github.com/wlamason/github-stars/blob/main/github_stars.py).

## Running via Github Actions

This repo was created for personal use. As such, external usage is slightly convoluted. Feel free to raise a github issue if you would like to use this code, and I will make the github action more generic. Otherwise I recommend:

1. Fork this repo in the top right corner of the webpage
1. `git clone git@github.com:<your_user_name>/github-stars.git`
1. `cd github-stars`
1. `cp overrides.template.json overrides.json`
1. Update `overrides.json` with any overrides
1. `git add .`
1. `git commit -m "personal github-stars"`
1. `git push`
1. On your fork, go to repository settings > Security > Secrets > Actions
1. Add the repository secret `GIT_TOKEN`

The value of `GIT_TOKEN` should be set to a personal access token. I recommend creating a new one just for this app. The access token will have to be updated each time it expires. To create a personal access token:

1. Click your user icon in the top right > Settings
1. Click Developer settings
1. Click Personal access tokens
2. Click Generate new token

## Running Locally

Requires Python 3.15, pinned in `.python-version`.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
1. `uv sync`
1. `uv run python github_stars.py --help`

## Testing

End-to-end tests live in [`tests/test_github_stars.py`](tests/test_github_stars.py). They call `parse_args` and `main` with a fake GitHub client and write output into a temporary directory, so they do not use the network.

```
uv run pytest
```

## Updating Dependencies

Runtime dependencies live in `pyproject.toml` under `[project] dependencies`. Development dependencies live in the `dev` dependency group. Exact versions are pinned in `uv.lock`.

1. `uv lock` after editing dependencies in `pyproject.toml`
1. `uv lock --upgrade` to upgrade pinned versions
1. `uv sync` to install the updated lockfile

## Author

👤 **Will Lamason**

* Website: [wmel.us](https://wmel.us)
* Github: [@wlamason](https://github.com/wlamason)

## Show your support

Give a ⭐️ if this project helped you!

## 📝 License

Copyright © 2022 [Will Lamason](https://github.com/wlamason).<br />
This project is [Apache--2.0](http://www.apache.org/licenses/LICENSE-2.0) licensed.

***
_This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator)_
