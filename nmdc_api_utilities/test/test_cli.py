# -*- coding: utf-8 -*-
"""Tests for the CLI module."""
import json
from pathlib import Path
from typer.testing import CliRunner
from nmdc_api_utilities.cli import app

runner = CliRunner()


def test_cli_help():
    """Test that the main help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "NMDC API utilities command-line interface" in result.stdout
    assert "biosample" in result.stdout
    assert "study" in result.stdout


def test_biosample_help():
    """Test biosample command help."""
    result = runner.invoke(app, ["biosample", "--help"])
    assert result.exit_code == 0
    assert "Search and retrieve biosample records" in result.stdout
    assert "--id" in result.stdout
    assert "--filter" in result.stdout


def test_study_help():
    """Test study command help."""
    result = runner.invoke(app, ["study", "--help"])
    assert result.exit_code == 0
    assert "Search and retrieve study records" in result.stdout


def test_data_object_help():
    """Test data-object command help."""
    result = runner.invoke(app, ["data-object", "--help"])
    assert result.exit_code == 0
    assert "Search and retrieve data object records" in result.stdout


def test_collection_name_help():
    """Test collection-name command help."""
    result = runner.invoke(app, ["collection-name", "--help"])
    assert result.exit_code == 0
    assert "Get the collection name for a given NMDC ID" in result.stdout


def test_collection_name():
    """Test collection-name command with real API call."""
    result = runner.invoke(app, ["collection-name", "nmdc:bsm-13-amrnys72"])
    assert result.exit_code == 0
    assert "biosample_set" in result.stdout


def test_biosample_by_id():
    """Test biosample command with ID."""
    result = runner.invoke(app, ["biosample", "--id", "nmdc:bsm-13-amrnys72"])
    assert result.exit_code == 0
    assert "Found" in result.stdout
    assert "record" in result.stdout


def test_biosample_with_limit():
    """Test biosample command with limit."""
    result = runner.invoke(app, ["biosample", "--limit", "3"])
    assert result.exit_code == 0
    assert "Found" in result.stdout


def test_biosample_to_file(tmp_path):
    """Test biosample command with file output."""
    output_file = tmp_path / "test_output.json"
    result = runner.invoke(
        app,
        ["biosample", "--id", "nmdc:bsm-13-amrnys72", "--output", str(output_file)]
    )
    assert result.exit_code == 0
    assert output_file.exists()

    # Verify the JSON is valid
    with open(output_file) as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) >= 1


def test_study_by_id():
    """Test study command with ID."""
    result = runner.invoke(app, ["study", "--id", "nmdc:sty-11-34xj1150"])
    assert result.exit_code == 0
    assert "Found" in result.stdout


def test_validate_help():
    """Test validate command help."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate a JSON metadata file" in result.stdout


def test_mint_help():
    """Test mint command help."""
    result = runner.invoke(app, ["mint", "--help"])
    assert result.exit_code == 0
    assert "Mint new NMDC identifiers" in result.stdout


def test_search_by_function_help():
    """Test search-by-function command help."""
    result = runner.invoke(app, ["search-by-function", "--help"])
    assert result.exit_code == 0
    assert "Search for biosamples by functional annotations" in result.stdout
    assert "PFAM" in result.stdout
    assert "KEGG" in result.stdout
    assert "--require-all" in result.stdout
    assert "--any" in result.stdout
