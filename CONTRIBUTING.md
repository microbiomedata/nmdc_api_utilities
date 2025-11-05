# Contributing to nmdc_api_utilities

Thank you for your interest in contributing to `nmdc_api_utilities`! This guide will help you set up your development environment and understand our workflows.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Modern Python package manager

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### Setting Up the Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/microbiomedata/nmdc_api_utilities.git
   cd nmdc_api_utilities
   ```

2. **Install dependencies with uv**
   ```bash
   # Install all development dependencies
   uv sync --extra dev

   # This creates a .venv directory and installs:
   # - Core dependencies (pandas, requests, typer, rich)
   # - Dev tools (pytest, sphinx, pre-commit, python-dotenv)
   ```

3. **Activate the virtual environment** (optional, uv run handles this automatically)
   ```bash
   # Unix/macOS
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

4. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   uv run pre-commit install
   ```

### Environment Variables

For tests that require authentication (validation, minting):

```bash
# Create a .env file (not committed to git)
cat > .env << EOF
ENV=prod  # or "dev" for development API
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
EOF
```

**Note**: Tests will default to `ENV=prod` if not set, so `.env` is optional for most development work.

## Project Structure

```
nmdc_api_utilities/
├── nmdc_api_utilities/          # Main package
│   ├── cli.py                   # Typer-based CLI
│   ├── auth.py                  # Authentication handler
│   ├── nmdc_search.py           # Base class
│   ├── collection_search.py     # Generic collection operations
│   ├── biosample_search.py      # Biosample-specific operations
│   ├── study_search.py          # Study-specific operations
│   ├── metadata.py              # Metadata validation/submission
│   ├── minter.py                # ID minting
│   └── test/                    # Test suite
│       ├── conftest.py          # Pytest fixtures
│       ├── test_cli.py          # CLI tests (fast)
│       ├── test_*.py            # Integration tests (slow)
│       └── ...
├── docs/                        # Sphinx documentation
├── pyproject.toml               # Project configuration
├── uv.lock                      # Dependency lockfile
├── CLAUDE.md                    # Development guide for AI assistants
├── CONTRIBUTING.md              # This file
└── CHANGES.md                   # Changelog
```

## Running Tests

### Quick Reference

```bash
# Fast tests only (CLI + doctests) - recommended during development
uv run pytest nmdc_api_utilities/test/test_cli.py -v
uv run pytest --doctest-modules nmdc_api_utilities/ --ignore=nmdc_api_utilities/test/

# Full test suite (slow, ~2-3 minutes)
uv run pytest nmdc_api_utilities/test/

# Specific test file
uv run pytest nmdc_api_utilities/test/test_biosample.py -v

# Show test durations
uv run pytest nmdc_api_utilities/test/ --durations=10

# Run with coverage
uv run pytest nmdc_api_utilities/test/ --cov=nmdc_api_utilities --cov-report=html
```

### Understanding Test Types

#### 1. **CLI Tests** (Fast - ~1-2 seconds)
- Located in: `test_cli.py`
- Use `typer.testing.CliRunner` (mocked HTTP)
- No real API calls
- **Run these during development**

```bash
uv run pytest nmdc_api_utilities/test/test_cli.py -v
```

#### 2. **Integration Tests** (Slow - ~2-3 minutes)
- Located in: `test_biosample.py`, `test_study.py`, etc.
- Make **real HTTP requests** to NMDC API
- Test end-to-end functionality
- **Run before committing**

```bash
# Run all integration tests
uv run pytest nmdc_api_utilities/test/ -v

# Run specific integration test
uv run pytest nmdc_api_utilities/test/test_biosample.py -v
```

#### 3. **Doctests** (Fast - <30 seconds)
- Embedded in docstrings
- Test documentation examples
- **Run frequently**

```bash
uv run pytest --doctest-modules nmdc_api_utilities/ --ignore=nmdc_api_utilities/test/
```

### Recommended Workflow

1. **During development**: Run CLI tests + doctests
   ```bash
   uv run pytest nmdc_api_utilities/test/test_cli.py -v && \
   uv run pytest --doctest-modules nmdc_api_utilities/nmdc_search.py
   ```

2. **Before committing**: Run full suite
   ```bash
   uv run pytest nmdc_api_utilities/test/
   ```

3. **Before pushing**: Run full suite with coverage
   ```bash
   uv run pytest nmdc_api_utilities/test/ --cov=nmdc_api_utilities
   ```

## Writing Tests

### Guidelines

1. **Use pytest style, not unittest** (for new tests)
2. **Use fixtures from conftest.py**
3. **Add doctests to public functions**
4. **Integration tests should be idempotent** (safe to run multiple times)
5. **CLI tests should use `typer.testing.CliRunner`**

### Test Structure

#### Pytest-style Test (Recommended)

```python
def test_search_biosamples(env):
    """Test biosample search with filter.

    Args:
        env: Pytest fixture providing test environment (prod/dev)
    """
    client = BiosampleSearch(env=env)
    results = client.get_records(max_page_size=5)
    assert len(results) <= 5
    assert all('id' in r for r in results)
```

#### Unittest-style Test (Legacy)

```python
import unittest
import os

class TestCollection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.env = os.getenv("ENV", "prod")

    def test_get_records(self):
        collection = CollectionSearch("study_set", env=self.env)
        results = collection.get_records(max_page_size=10)
        self.assertEqual(len(results), 10)
```

#### CLI Test

```python
from typer.testing import CliRunner
from nmdc_api_utilities.cli import app

runner = CliRunner()

def test_biosample_command():
    """Test biosample CLI command."""
    result = runner.invoke(app, ["biosample", "--limit", "5"])
    assert result.exit_code == 0
    assert "Found" in result.stdout
```

#### Doctest

```python
def split_list(input_list: list, chunk_size: int = 100) -> list:
    """
    Split a list into chunks of a specified size.

    Parameters
    ----------
    input_list: list
        The list to split.
    chunk_size: int
        The size of each chunk.

    Returns
    -------
    list
        A list of lists.

    Examples
    --------
    >>> from nmdc_api_utilities.data_processing import DataProcessing
    >>> dp = DataProcessing()
    >>> data = list(range(10))
    >>> chunks = dp.split_list(data, chunk_size=3)
    >>> len(chunks)
    4
    >>> chunks[0]
    [0, 1, 2]
    """
    result = []
    for i in range(0, len(input_list), chunk_size):
        result.append(input_list[i : i + chunk_size])
    return result
```

### Test Best Practices

#### ✅ Do:
- Use descriptive test names: `test_search_with_filter_returns_results`
- Test edge cases and error conditions
- Use fixtures for repeated setup
- Keep tests independent (no shared state)
- Add doctests to public APIs
- Document what you're testing in docstrings

#### ❌ Don't:
- Call test functions at module level (causes collection errors)
- Use module-level `ENV = os.getenv("ENV")` (use fixtures instead)
- Make tests depend on execution order
- Test implementation details (test behavior)
- Use `try/except` to hide failures (avoid as per project guidelines)
- Skip adding assertions

### Fixtures Reference

From `conftest.py`:

```python
@pytest.fixture(scope="session")
def env():
    """Get test environment (prod/dev). Defaults to 'prod'."""
    return os.getenv("ENV", "prod")

@pytest.fixture(scope="session")
def client_id():
    """Get CLIENT_ID from environment."""
    return os.getenv("CLIENT_ID")

@pytest.fixture(scope="session")
def client_secret():
    """Get CLIENT_SECRET from environment."""
    return os.getenv("CLIENT_SECRET")
```

## Code Style

### General Guidelines

- Follow PEP 8
- Use type hints (Python 3.9+ compatible)
- Write docstrings for all public functions (NumPy style)
- Avoid try/except blocks unless absolutely necessary (see CLAUDE.md)
- Use `Union[A, B]` not `A | B` for Python 3.9 compatibility

### Type Annotations

```python
# ✅ Good (Python 3.9+ compatible)
from typing import Union, Optional

def validate_json(self, json_records: Union[list[dict], str]) -> int:
    ...

# ❌ Bad (Python 3.10+ only)
def validate_json(self, json_records: list[dict] | str) -> int:
    ...
```

### Docstrings

Use NumPy style with Examples section for doctests:

```python
def get_records(
    self,
    filter: str = "",
    max_page_size: int = 100,
    all_pages: bool = False,
) -> list[dict]:
    """
    Get records from the NMDC API.

    Parameters
    ----------
    filter : str
        MongoDB filter query. Default is empty string.
    max_page_size : int
        Maximum number of items per page. Default is 100.
    all_pages : bool
        Fetch all pages if True. Default is False.

    Returns
    -------
    list[dict]
        A list of dictionaries containing the records.

    Raises
    ------
    RuntimeError
        If the API request fails.

    Examples
    --------
    >>> from nmdc_api_utilities.biosample_search import BiosampleSearch
    >>> client = BiosampleSearch()
    >>> records = client.get_records(max_page_size=10)
    >>> isinstance(records, list)
    True
    """
    ...
```

### CLI Development

When adding CLI commands:

1. Use Typer for argument parsing
2. Add comprehensive help text with examples
3. Use Rich for output formatting
4. Handle errors gracefully
5. Add corresponding tests in `test_cli.py`

Example:

```python
@app.command()
def my_command(
    id: str = typer.Argument(..., help="The ID to search"),
    limit: int = typer.Option(10, "--limit", "-l", help="Result limit"),
    env: str = env_option,
):
    """
    Brief description of command.

    Examples:

    \b
        # Example 1
        nmdc my-command some-id

    \b
        # Example 2
        nmdc my-command some-id --limit 20
    """
    try:
        # Implementation
        ...
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

## Submitting Changes

### Before Submitting

1. **Run tests**
   ```bash
   uv run pytest nmdc_api_utilities/test/
   ```

2. **Run linters** (if pre-commit is set up)
   ```bash
   uv run pre-commit run --all-files
   ```

3. **Update documentation**
   - Add docstrings to new functions
   - Update README.md if adding user-facing features
   - Update CHANGES.md with your changes

4. **Test CLI changes**
   ```bash
   uv run nmdc --help
   uv run nmdc your-command --help
   ```

### Commit Guidelines

- Use descriptive commit messages
- Reference issue numbers if applicable
- Keep commits focused (one logical change per commit)

```bash
# Good commit messages
git commit -m "Add biosample filtering by lat/lon coordinates

- Implement lat_lon_filter method in BiosampleSearch
- Add tests for geographic filtering
- Update README with usage examples

Fixes #42"

# Not as good
git commit -m "fix stuff"
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Commit your changes
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request with:
   - Clear description of changes
   - Reference to related issues
   - Test results
   - Screenshots (for UI changes)

## Getting Help

- Check [CLAUDE.md](CLAUDE.md) for architecture details
- Review [CHANGES.md](CHANGES.md) for recent changes
- Look at existing tests for examples
- Open an issue for questions or bugs
- Check the [NMDC API documentation](https://api.microbiomedata.org/docs)

## Project-Specific Notes

### Avoiding Try/Except

Per project guidelines (see CLAUDE.md), avoid wrapping code in try/except blocks:

```python
# ❌ Discouraged
try:
    dataset = json.load(...)
    v = dataset.some_operation()
except:
    logger.error(f"Failed: {e}")
    return None

# ✅ Preferred
dataset = json.load(...)
v = dataset.some_operation()
# If an exception occurs, investigate and fix the root cause
```

### CLI Tools

- Use `just` commands if available (older repos may use `make`)
- Prefer Typer over Click for new CLI code
- Never use raw argparse

### Testing Philosophy

- Doctests are great for documentation + testing
- Use pytest style over unittest for new tests
- CLI tests should be fast (use CliRunner)
- Integration tests will be slow (real API calls)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

## Questions?

Feel free to open an issue for questions or clarifications!
