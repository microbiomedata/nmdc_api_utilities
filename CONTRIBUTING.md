# Contributing


👍 First of all: Thank you for taking the time to contribute!

The following is a set of guidelines for contributing to the nmdc_api_utilities repo. This guide is aimed primarily at the developers, although anyone is welcome to contribute.

Unlike other repos for data exploration, the code in this repo is used by many moving parts in the NMDC stack. We strive to hold best and interpretable practices for development, as small changes could impact downstream processes. If you want to experiment with large changes we suggest forking or meeting with the maintainers first.


## Table Of Contents

- [Code of Conduct](#code-of-conduct)
- [Guidelines for Contributions and Requests](#contributions)
    * [Reporting issues](#reporting-issues)
    * [Making pull requests](#pull-requests)
- [Best practices](#best-practices)
- [Development](#development)
    * [Previewing user documentation](#previewing-user-documentation)
- [Making a release](#release)

<a id="code-of-conduct"></a>

## Code of Conduct

The NMDC team strives to create a
welcoming environment for editors, users and other contributors.

Please carefully read NMDC's [Code of Conduct](https://github.com/microbiomedata/nmdc-schema/blob/main/CODE_OF_CONDUCT.md).

<a id="contributions"></a>

## Guidelines for Contributions and Requests

<a id="reporting-issues"></a>

### Reporting issues

Please use the [Issue Tracker](https://github.com/microbiomedata/nmdc_api_utilities/issues/) for reporting problems or suggest enhancements for the package. Issues should be focused and actionable (a PR could close an issue). Complex issues should be broken down into simpler issues where possible.

Please review GitHub's overview article,
["Tracking Your Work with Issues"][about-issues].

### Pull Requests

See [Pull Requests](https://github.com/microbiomedata/nmdc-schema/pulls/) for all pull requests. Every pull request should be associated with an issue.

Please review GitHub's article, ["About Pull Requests"][about-pulls],
and make your changes on a [new branch][about-branches].

We recommend also reading [GitHub Pull Requests: 10 Tips to Know](https://blog.mergify.com/github-pull-requests-10-tips-to-know/)

## Best Practices

<a id="best-practices"></a>

- Read ["About Issues"][about-issues] and ["About Pull Requests"][about-pulls]
- Issues should be focused and actionable
- Bugs should be reported with a clear description of the problem and steps to reproduce.
- Complex issues should be broken down into simpler issues where possible
- Pull Requests (PRs) should be atomic and aim to close a single issue
- PRs should reference issues following standard conventions (e.g. “Fixes #123”)
- Never work on the main branch, always work on an issue/feature branch
- Core developers can work on branches off origin rather than forks
- If possible create a draft or work-in-progress PR on a branch to maximize transparency of what you are doing
- PRs should be reviewed and merged in a timely fashion
- In the case of git conflicts, the contributor should try and resolve the conflict


[about-branches]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches
[about-issues]: https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues
[about-pulls]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests


## Development

<a id="Development"></a>

This project uses [uv](https://docs.astral.sh/uv/) for Python and dependency management. Production dependencies live under `[project].dependencies` in `pyproject.toml`; development and documentation dependencies live under `[dependency-groups]` (`dev` and `docs`). The `uv.lock` file pins the exact resolved versions and is committed to the repo.

### Python

#### To install the python dependencies:

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't already have it.
2. Clone the GitHub repository.
3. Install the project plus the `dev` dependency group into a managed virtual environment:

    `uv sync --group dev`

    Add `--group docs` if you also want the documentation tooling. To update an existing environment after pulling new changes, re-run the same command.

4. Run any tool inside the managed environment with `uv run`, for example:

    `uv run pytest`

#### Set up pre commit

1. Install precommit hooks to run formatting before committing:

    `uv run pre-commit install`

### Static type checking

We use [mypy](https://mypy-lang.org/) to validate our code in terms of data types.
Because mypy is a _static_ type checker, we can use it to find problems without running the code.
For example, mypy will report inconsistencies like the following:

```py
def triple(n: int) -> int:
    return n * 3

triple("1")  # 🙋 mypy will report this inconsistency
```

#### Perform static type checking

You can perform static type checking by running:

```sh
uv run mypy
```

By default, mypy will use the configuration specified within the `[tool.mypy]` section of `pyproject.toml`. You can override aspects of that configuration via [CLI options](https://mypy.readthedocs.io/en/stable/command_line.html).

### Previewing user documentation

We use [Sphinx](https://www.sphinx-doc.org/en/master/) to generate user documentation. Our Sphinx
configuration files and static assets are located in the `docs/` directory.

In production, our user documentation is generated via a GitHub Actions workflow
(i.e. `documentation.yml`) that builds the documentation website and deploys it to GitHub Pages,
where it can be accessed by users.

In development, you can build and preview the documentation website locally by following these steps:

1. Install Python dependencies and register notebook kernel. The pandoc binary that
   `nbsphinx` needs is bundled in the `pypandoc-binary` package, so no system-level
   install (Homebrew, apt) is required.

   ```sh
   uv sync --group docs
   uv run python -m ipykernel install --user --name python3 --display-name "Python 3"
   ```

2. Build (or rebuild) the documentation website.

   ```sh
   uv run sphinx-build -v docs build/html
   ```

3. Use Python's built-in HTTP server to serve the documentation website locally,
   at [`http://localhost:8000`](http://localhost:8000)

   ```sh
   uv run python -m http.server 8000 --directory build/html
   ```

When you're done previewing the documentation website, you can terminate the HTTP server by pressing
`^C` at the terminal.

#### Major refactoring

Major refactoring should be scoped with the main developers of the repo.

<a id="release"></a>
## Making a release
Right now, only the maintainer of this repository can make a release to PyPi. This process may change in the future. If you need to make a release please contact Olivia Hess.
