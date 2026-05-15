# Contributing

👍 First of all: Thank you for taking the time to contribute!

The following is a set of guidelines for contributing to the [nmdc_api_utilities](https://github.com/microbiomedata/nmdc_api_utilities) repo. This guide is aimed primarily at the developers, although anyone is welcome to contribute.

Unlike other repos for data exploration, the code in this repo is used by many moving parts in the NMDC stack. We strive to hold best and interpretable practices for development, as small changes could impact downstream processes. If you want to experiment with large changes, we suggest forking or meeting with the maintainers first.

## Table Of Contents

<!-- TODO: Update the table of contents. Consider using a VS Code extension that generates this automatically based upon the headings within the document. -->

- [Code of Conduct](#code-of-conduct)
- [Guidelines for Contributions and Requests](#contributions)
  - [Reporting issues](#reporting-issues)
  - [Making pull requests](#pull-requests)
  - [Best practices](#best-practices)
- [Development](#development)
- [Testing](#testing)
  - [Running tests](#running-tests)
  - [The `api_base_url` variable](#the-api_base_url-variable)
  - [Writing new tests](#writing-new-tests)
- [Docstrings](#docstrings)
- [Previewing user documentation](#previewing-user-documentation)
- [Making a release](#release)

<a id="code-of-conduct"></a>

## Code of Conduct

The NMDC team strives to create a welcoming environment for editors, users, and other contributors.

Please carefully read NMDC's [Code of Conduct](https://github.com/microbiomedata/nmdc-schema/blob/main/CODE_OF_CONDUCT.md).

<a id="contributions"></a>

## Guidelines for Contributions and Requests

<a id="reporting-issues"></a>

### Reporting issues

Please use the [Issue Tracker](https://github.com/microbiomedata/nmdc_api_utilities/issues/) for reporting problems or suggest enhancements for the package. Issues should be focused and actionable (a PR could close an issue). Complex issues should be broken down into simpler issues where possible.

Please review GitHub's overview article,
["Tracking Your Work with Issues"][about-issues].

<a id="pull-requests"></a>

### Making pull requests

See [Pull Requests](https://github.com/microbiomedata/nmdc_api_utilities/pulls/) for all pull requests. Every pull request should be associated with an issue.

Please review GitHub's article, ["About Pull Requests"][about-pulls],
and make your changes on a [new branch][about-branches].

We recommend also reading [GitHub Pull Requests: 10 Tips to Know](https://blog.mergify.com/github-pull-requests-10-tips-to-know/)

<a id="best-practices"></a>

### Best practices for issues and pull requests

- Read ["About Issues"][about-issues] and ["About Pull Requests"][about-pulls]
- Issues should be focused and actionable
- Bugs should be reported with a clear description of the problem and steps to reproduce
- Complex issues should be broken down into simpler issues where possible
- Pull Requests (PRs) should be atomic and aim to close a single issue
- PRs should reference issues following standard conventions (e.g. “Fixes #123”)
- Never work on the main branch, always work on an issue/feature branch
- Core developers can work on branches off origin rather than forks
- If possible create a draft or work-in-progress PR on a branch to maximize transparency of what you are doing
- PRs should be reviewed and merged in a timely fashion
- In the case of git conflicts, the contributor should try and resolve the conflict

<!--
    Note: The following are "reference-style" links, whose references are sprinkled throughout this document.
          For more information: https://www.markdownguide.org/basic-syntax/#reference-style-links
          These kinds of links are not mentioned in GitHub's docs, at: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#links
-->

[about-branches]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-branches
[about-issues]: https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues
[about-pulls]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests

## Development

<a id="Development"></a>

This project uses [uv](https://docs.astral.sh/uv/) for Python and dependency management. Production dependencies live under `[project].dependencies` in `pyproject.toml`; development and documentation dependencies live under `[dependency-groups]` (`dev` and `docs`). The `uv.lock` file pins the exact resolved versions and is committed to the repo.

### Python

#### Install Python dependencies

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't already have it.
2. Clone the GitHub repository.
3. Install the project, plus the dependencies in the `dev` group, into a uv-managed virtual environment:

    ```sh
    uv sync --group dev
    ```

    You can add `--group docs` to also install the documentation dependencies. To update an existing environment after pulling new changes, re-run the same command.

4. Run any tool inside the uv-managed environment with `uv run`; for example:

    ```sh
    uv run pytest
    ```

#### Set up pre-commit

1. Install pre-commit hooks to run formatting before committing:

    ```sh
    uv run pre-commit install
    ```

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

<a id="docstrings"></a>

### Docstrings

We use [numpydoc](https://numpydoc.readthedocs.io/en/latest/format.html) style for all docstrings.
The key sections are `Parameters`, `Returns`, `Raises`, and `Examples` (when helpful).

**Do not** include types or default values in docstrings. Instead, express them as Python type hints
directly in the function or method signature. For example:

```py
# ✅ Do this — type hints in the signature, no types or defaults in the docstring
def get_records(self, filter: str = "", max_page_size: int = 100) -> list[dict]:
    """
    Retrieve records from the collection.

    Parameters
    ----------
    filter
        A MongoDB-style filter string to narrow the results.
    max_page_size
        Maximum number of records to return per page.

    Returns
    -------
    list[dict]
        The matching records.
    """
    ...

# ❌ Don't do this — types and defaults duplicated in the docstring
def get_records(self, filter: str = "", max_page_size: int = 100) -> list[dict]:
    """
    Retrieve records from the collection.

    Parameters
    ----------
    filter : str, optional
        A MongoDB-style filter string to narrow the results, by default "".
    max_page_size : int, optional
        Maximum number of records to return per page, by default 100.

    Returns
    -------
    list[dict]
        The matching records.
    """
    ...
```

### Deprecation

#### Overview

We occasionally [deprecate](https://en.wikipedia.org/wiki/Deprecation#Software) existing Python
classes, methods, functions, or function parameters; normally, when we introduce an alternative
that we want people to use instead.

#### Our approach

In this project, deprecating something involves making it so that: (a) Python displays a deprecation
message whenever someone uses that thing; and (b) the Sphinx-generated documentation about that
thing includes a deprecation message. A deprecation message looks something like this:

> `foo` is deprecated. Use `bar` instead.

To accomplish (a) and (b) for classes, methods, and functions, we use a third-party package named
[Deprecated](https://deprecated.readthedocs.io/en/latest/).

To accomplish (a) and (b) for function and method parameters, we use a custom decorator called
`has_deprecated_parameter`. That's because, while the third-party `Deprecated` package does have
a decorator that designates a parameter as being deprecated, that decorator does not add
a note to the Sphinx docs.

#### How to deprecate things

To deprecate a class, method, or function, follow the steps shown in the documentation of the
[deprecated.sphinx](https://deprecated.readthedocs.io/en/latest/sphinx_deco.html#using-the-sphinx-decorators) module.

To deprecate a parameter(s) of a function, use our custom decorator as shown here:

```py
from nmdc_api_utilities.decorators import has_deprecated_params

@has_deprecated_params("region", reason="Use ``region_id`` instead.")
def get_location(name: str, region: str | None, region_id: str):
    pass
```

```py
from nmdc_api_utilities.decorators import has_deprecated_params

@has_deprecated_params("region", reason="Use ``region_id`` instead.")
class Location:
    def __init__(self, name: str, region: str | None = None, region_id: str):
        pass
```

> When deprecating a parameter of a class's `__init__` method, apply the decorator to the **class**,
> itself; not to the `__init__` method.

### Previewing user documentation

We use [Sphinx](https://www.sphinx-doc.org/en/master/) to generate user documentation. Our Sphinx
configuration files and static assets are located in the `docs/` directory.

In production, our user documentation is generated via a GitHub Actions workflow
(i.e. `documentation.yml`) that builds the documentation website and deploys it to GitHub Pages,
where it can be accessed by users.

In development, you can build and preview the documentation website locally by following these steps:

1. Install Python dependencies. The pandoc binary that `nbsphinx` needs is bundled in
   the `pypandoc-binary` package, so no system-level install (Homebrew, apt) is required.

   ```sh
   uv sync --group docs
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

<a id="testing"></a>

## Testing

We use [pytest](https://docs.pytest.org/) as our testing framework. All tests live in the `nmdc_api_utilities/test/` directory.

<a id="running-tests"></a>

### Running tests

Run the full test suite with:

```sh
uv run pytest
```

To run only a specific test file:

```sh
uv run pytest nmdc_api_utilities/test/test_collection.py
```

To run a specific test by name:

```sh
uv run pytest nmdc_api_utilities/test/test_collection.py::TestCollection::test_get_records
```

<a id="the-api_base_url-variable"></a>

### The `api_base_url` variable

Most methods in this package accept an `api_base_url` parameter that specifies which instance of the NMDC Runtime API to send requests to. At module load time, the `API_BASE_URL` constant in `nmdc_api_utilities/config.py` is resolved from environment variables and is used as the default value throughout the test suite.

For our CI/CD testing workflows, we test against both the production and development instances of the NMDC Runtime API. This is configured via environment variables in the GitHub Actions workflow files (`prod_tests.yml` and `dev_tests.yml`), and the logic for resolving which API to target is implemented in `nmdc_api_utilities/config.py`. For any new test you write, you should ensure that it can be run against any API instance by using the `API_BASE_URL` constant as the default value for the `api_base_url` parameter when constructing client objects. This allows the test to be flexible and work in different environments without modification.

<a id="writing-new-tests"></a>

### Writing new tests

- Place new test files in `nmdc_api_utilities/test/` and name them `test_<module>.py`.
- Test functions and methods should be named `test_<what_is_being_tested>`.
- Import `API_BASE_URL` from `nmdc_api_utilities.config` and pass it as the `api_base_url` argument to any client object you instantiate.

**Mocking privileged API calls**

Any test that exercises an API endpoint that requires authentication or that _submits, modifies, or deletes_ data **must** mock the underlying HTTP calls. Do **not** write tests that actually submit data to the production (or development) NMDC Runtime API.

Use `unittest.mock.patch` (or pytest's `monkeypatch`) to intercept the relevant HTTP calls. The existing tests in `test_staging.py` demonstrate the recommended pattern:

```python
from unittest.mock import MagicMock, patch
import pytest
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.data_staging import JGISequencingProjectAPI


@pytest.fixture
def mock_auth():
    with patch("nmdc_api_utilities.data_staging.NMDCAuth") as mock_auth_class:
        mock_auth_instance = MagicMock()
        mock_auth_instance.get_token.return_value = "fake-token"
        mock_auth_instance.has_credentials.return_value = True
        mock_auth_class.return_value = mock_auth_instance
        yield mock_auth_instance


@pytest.fixture
def mock_post_response():
    with patch("requests.post") as mock_post:
        yield mock_post


def test_create_sequencing_project(mock_auth, mock_post_response):
    mock_post_response.return_value.json.return_value = {"resources": {"key": "value"}}
    client = JGISequencingProjectAPI(api_base_url=API_BASE_URL, auth=mock_auth)
    result = client.create_jgi_sequencing_project({"key": "value"})
    assert result == {"resources": {"key": "value"}}
    mock_post_response.assert_called_once()  # verify the call was made (but not for real)
```

The key rules are:

- **Never** call a write/submission endpoint against the live API in a test.
- Always assert both the return value _and_ that the mock was called the expected number of times. Use `assert_called_once()` to verify it was called exactly once, or `assert_called_once_with(expected_url, ...)` to also verify the correct arguments were passed (which provides stronger validation).

<a id="release"></a>

## Making a release

Right now, only the maintainer of this repository can make a release to [PyPI](https://pypi.org/project/nmdc-api-utilities/). This process may change in the future. If you need to make a release, please contact Olivia Hess.
