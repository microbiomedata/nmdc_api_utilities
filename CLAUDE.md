# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`nmdc_api_utilities` is a Python library and CLI tool that provides utilities for interacting with the NMDC (National Microbiome Data Collaborative) API. The library simplifies research tasks by providing easy access to microbiome data through collection-specific search classes, metadata management tools, and a convenient command-line interface.

### Key Components

- **Python API**: Collection-specific search classes (BiosampleSearch, StudySearch, etc.)
- **CLI**: Typer-based command-line tool (`nmdc` command)
- **Authentication**: OAuth2 support for protected endpoints
- **Metadata operations**: Validation and submission of NMDC metadata

## Development Commands

### Installation

This project uses `uv` for modern Python dependency management.

```bash
# Install dependencies and create virtual environment
uv sync

# Install with dev dependencies (for testing, docs, etc.)
uv sync --extra dev

# Install with visualization support (matplotlib)
uv sync --extra viz

# Install with all extras
uv sync --all-extras

# Legacy method (still supported)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests

**Important**: Most tests are **integration tests** that make real HTTP requests to the NMDC API. They are slow (can take 2+ minutes for full suite).

```bash
# Run all tests (includes doctests) with uv - SLOW!
uv run pytest -r nmdc_api_utilities/test/

# Run a specific test file
uv run pytest nmdc_api_utilities/test/test_biosample.py

# Run CLI tests (fastest - no real API calls)
uv run pytest nmdc_api_utilities/test/test_cli.py -v

# Run with verbose output
uv run pytest -v nmdc_api_utilities/test/

# Show slowest 10 tests
uv run pytest nmdc_api_utilities/test/ --durations=10

# Run only doctests (fast)
uv run pytest --doctest-modules nmdc_api_utilities/ --ignore=nmdc_api_utilities/test/

# Run doctests for a specific module
uv run pytest --doctest-modules nmdc_api_utilities/collection_search.py
```

**Test Performance Notes**:
- Total: 48 integration tests making real API calls
- Full suite: ~2-3 minutes
- CLI tests (test_cli.py): ~1-2 seconds (mocked HTTP via typer.testing.CliRunner)
- Doctests: <30 seconds
- **Recommended**: Run CLI tests + doctests during development, full suite before commits

### Using the CLI

```bash
# Test the CLI during development
uv run nmdc --help
uv run nmdc biosample --id nmdc:bsm-13-amrnys72

# After installation, use directly
nmdc --help
nmdc biosample --id nmdc:bsm-13-amrnys72
```

### Building Documentation

```bash
# Using uv (dev dependencies include sphinx)
uv run sphinx-build -v docs build/html

# Legacy method
cd docs
pip install sphinx sphinx_rtd_theme myst_parser
sphinx-build -v . ../build/html
```

### Environment Configuration
Tests can run against different NMDC API environments:
- Set `ENV=prod` for production API (https://api.microbiomedata.org)
- Set `ENV=dev` for development API (https://api-dev.microbiomedata.org)

Authentication requires `CLIENT_ID` and `CLIENT_SECRET` environment variables for protected endpoints.

## Architecture

### CLI Architecture (cli.py)
The CLI is built with Typer and provides the following commands:
- **biosample**: Search and retrieve biosample records
- **study**: Search and retrieve study records
- **data-object**: Search and retrieve data object records
- **collection-name**: Get collection name for an NMDC ID
- **validate**: Validate JSON metadata against NMDC schema (requires auth)
- **mint**: Mint new NMDC identifiers (requires auth)

All commands support:
- Environment selection (--env prod|dev)
- JSON output to file (--output)
- Pretty console display with Rich
- Comprehensive help text with examples

### Python API Class Hierarchy
The library uses an inheritance-based architecture:

1. **NMDCSearch** (nmdc_search.py): Base class that sets the API base_url based on environment (prod/dev)

2. **CollectionSearch** (collection_search.py): Extends NMDCSearch, provides generic methods for querying NMDC collections:
   - `get_records()`: Query collections with filters, pagination, field projection
   - `get_record_by_id()`: Fetch single record by ID
   - `_get_all_pages()`: Handle pagination automatically

3. **Collection-specific classes**: Each extends CollectionSearch with a specific collection_name:
   - BiosampleSearch → "biosample_set"
   - StudySearch → "study_set"
   - DataObjectSearch → "data_object_set"
   - etc.

4. **Specialized classes**:
   - **Metadata** (metadata.py): Handles metadata validation and submission (requires auth)
   - **Minter** (minter.py): Mints new NMDC identifiers (requires auth)
   - **NMDCAuth** (auth.py): Manages OAuth2 authentication with token refresh

### Authentication Pattern
Protected operations use the `@requires_auth` decorator (decorators.py). Classes requiring auth accept an `NMDCAuth` instance:
```python
auth = NMDCAuth(client_id="...", client_secret="...")
metadata = Metadata(env="prod", auth=auth)
```

The Minter class maintains backward compatibility by accepting `client_id`/`client_secret` directly in method calls.

### Data Flow
1. User creates collection-specific search object (e.g., `BiosampleSearch()`)
2. Calls search methods with filters
3. CollectionSearch constructs API URL with query parameters
4. Makes HTTP request to NMDC API
5. Handles pagination if `all_pages=True`
6. Returns list of dictionaries

## Important Notes

- **Dependency Management**: This project uses `uv` for modern dependency management. The `requirements.txt` files are kept for backward compatibility.
- **Lightweight Core**: Core dependencies are minimal (pandas, requests, typer, rich). Optional features:
  - `viz` extra: Adds matplotlib for visualization functions
  - `dev` extra: Adds development tools (pytest, sphinx, pre-commit, etc.)
- **CLI Entry Point**: The `nmdc` command is configured in `pyproject.toml` under `[project.scripts]` pointing to `nmdc_api_utilities.cli:app`
- **Library Design**: The library is designed as a client wrapper around NMDC REST APIs
- **Class Pattern**: All collection search classes follow the same pattern: extend CollectionSearch and set collection_name
- **Type Annotations**: Use `Union[A, B]` instead of `A | B` for Python 3.9 compatibility
- **CLI Testing**: Use `typer.testing.CliRunner` for testing CLI commands
- **Logging**: Available via standard Python logging; users can enable DEBUG level for detailed API interactions
