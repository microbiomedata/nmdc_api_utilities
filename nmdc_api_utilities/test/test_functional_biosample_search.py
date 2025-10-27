# -*- coding: utf-8 -*-
"""
Tests for functional biosample search functionality.
"""
import pytest
from nmdc_api_utilities.functional_biosample_search import (
    FunctionalBiosampleSearch,
    _parse_function_id,
    _determine_function_table,
)


# ============================================================================
# Unit Tests for Helper Functions
# ============================================================================


class TestParseFunctionId:
    """Tests for _parse_function_id helper function."""

    def test_parse_pfam_with_prefix(self):
        """Test parsing PFAM ID with prefix."""
        prefix, func_id = _parse_function_id("PFAM:PF00005")
        assert prefix == "PFAM"
        assert func_id == "PF00005"

    def test_parse_pfam_without_prefix(self):
        """Test parsing PFAM ID without prefix (auto-detected)."""
        prefix, func_id = _parse_function_id("PF00005")
        assert prefix == "PFAM"
        assert func_id == "PF00005"

    def test_parse_kegg_with_prefix(self):
        """Test parsing KEGG ID with full prefix."""
        prefix, func_id = _parse_function_id("KEGG.ORTHOLOGY:K00001")
        assert prefix == "KEGG.ORTHOLOGY"
        assert func_id == "K00001"

    def test_parse_kegg_without_prefix(self):
        """Test parsing KEGG ID without prefix (auto-detected)."""
        prefix, func_id = _parse_function_id("K00001")
        assert prefix == "KEGG.ORTHOLOGY"
        assert func_id == "K00001"

    def test_parse_cog_with_prefix(self):
        """Test parsing COG ID with prefix."""
        prefix, func_id = _parse_function_id("COG:COG0001")
        assert prefix == "COG"
        assert func_id == "COG0001"

    def test_parse_cog_without_prefix(self):
        """Test parsing COG ID without prefix (auto-detected)."""
        prefix, func_id = _parse_function_id("COG0001")
        assert prefix == "COG"
        assert func_id == "COG0001"

    def test_parse_go_with_prefix(self):
        """Test parsing GO ID with prefix."""
        prefix, func_id = _parse_function_id("GO:GO0000001")
        assert prefix == "GO"
        assert func_id == "GO0000001"

    def test_parse_go_without_prefix(self):
        """Test parsing GO ID without prefix (auto-detected)."""
        prefix, func_id = _parse_function_id("GO0000001")
        assert prefix == "GO"
        assert func_id == "GO0000001"

    def test_parse_invalid_id(self):
        """Test parsing invalid function ID raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse function ID"):
            _parse_function_id("INVALID123")


class TestDetermineFunctionTable:
    """Tests for _determine_function_table helper function."""

    def test_pfam_table(self):
        """Test PFAM prefix maps to pfam_function table."""
        assert _determine_function_table("PFAM") == "pfam_function"

    def test_kegg_orthology_table(self):
        """Test KEGG.ORTHOLOGY prefix maps to kegg_function table."""
        assert _determine_function_table("KEGG.ORTHOLOGY") == "kegg_function"

    def test_kegg_short_table(self):
        """Test KEGG prefix maps to kegg_function table."""
        assert _determine_function_table("KEGG") == "kegg_function"

    def test_cog_table(self):
        """Test COG prefix maps to cog_function table."""
        assert _determine_function_table("COG") == "cog_function"

    def test_go_table(self):
        """Test GO prefix maps to go_function table."""
        assert _determine_function_table("GO") == "go_function"

    def test_unsupported_table(self):
        """Test unsupported prefix raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported function type"):
            _determine_function_table("INVALID")


# ============================================================================
# Integration Tests (require NMDC API access)
# ============================================================================


@pytest.mark.integration
class TestFunctionalBiosampleSearch:
    """
    Integration tests for FunctionalBiosampleSearch.

    These tests make real API calls and are slow.
    Run with: pytest -m integration
    """

    def test_init_prod(self):
        """Test initialization with prod environment."""
        client = FunctionalBiosampleSearch(env="prod")
        assert client.base_url == "https://api.microbiomedata.org"
        assert client.data_base_url == "https://data.microbiomedata.org"

    def test_init_dev(self):
        """Test initialization with dev environment."""
        client = FunctionalBiosampleSearch(env="dev")
        assert client.base_url == "https://api-dev.microbiomedata.org"
        assert client.data_base_url == "https://data-dev.microbiomedata.org"

    def test_init_invalid_env(self):
        """Test initialization with invalid environment raises ValueError."""
        with pytest.raises(ValueError, match="env must be one of"):
            FunctionalBiosampleSearch(env="invalid")

    def test_search_by_pfam_single(self):
        """Test searching by single PFAM domain."""
        client = FunctionalBiosampleSearch()
        results = client.search_by_pfam(["PF00005"], limit=5)

        assert "count" in results
        assert "results" in results
        assert "search_criteria" in results
        assert results["count"] > 0
        assert len(results["results"]) <= 5

        # Check search criteria
        criteria = results["search_criteria"]
        assert "PFAM:PF00005" in criteria["function_ids"]
        assert criteria["limit"] == 5
        assert criteria["logic"] == "AND"

    def test_search_by_pfam_with_prefix(self):
        """Test searching with explicit PFAM prefix."""
        client = FunctionalBiosampleSearch()
        results = client.search_by_pfam(["PFAM:PF00005"], limit=3)

        assert results["count"] > 0
        assert len(results["results"]) <= 3

    def test_search_by_functions_mixed(self):
        """Test searching with mixed function types."""
        client = FunctionalBiosampleSearch()

        # Search for samples with both PFAM and KEGG
        results = client.search_by_functions(
            ["PFAM:PF00005", "KEGG.ORTHOLOGY:K00001"], limit=5, logic="AND"
        )

        assert "count" in results
        assert "results" in results
        # May return 0 if no samples have both

    def test_search_by_kegg(self):
        """Test searching by KEGG orthology."""
        client = FunctionalBiosampleSearch()
        results = client.search_by_kegg(["K00001"], limit=5)

        assert "count" in results
        assert "results" in results
        assert results["search_criteria"]["function_ids"] == ["KEGG.ORTHOLOGY:K00001"]

    def test_search_by_cog(self):
        """Test searching by COG."""
        client = FunctionalBiosampleSearch()
        results = client.search_by_cog(["COG0001"], limit=5)

        assert "count" in results
        assert "results" in results
        assert results["search_criteria"]["function_ids"] == ["COG:COG0001"]

    def test_search_by_go(self):
        """Test searching by GO."""
        client = FunctionalBiosampleSearch()
        results = client.search_by_go(["GO0000001"], limit=5)

        assert "count" in results
        assert "results" in results
        assert results["search_criteria"]["function_ids"] == ["GO:GO0000001"]

    def test_search_empty_function_ids(self):
        """Test that empty function_ids raises ValueError."""
        client = FunctionalBiosampleSearch()

        with pytest.raises(ValueError, match="function_ids cannot be empty"):
            client.search_by_functions([], limit=10)

    def test_search_invalid_logic(self):
        """Test that invalid logic raises ValueError."""
        client = FunctionalBiosampleSearch()

        with pytest.raises(ValueError, match="logic must be 'AND' or 'OR'"):
            client.search_by_functions(["PFAM:PF00005"], limit=10, logic="INVALID")

    def test_search_or_logic(self):
        """Test OR logic with multiple PFAMs."""
        client = FunctionalBiosampleSearch()

        results = client.search_by_pfam(
            ["PF00005", "PF00072"], limit=10, require_all=False
        )

        assert "count" in results
        assert "results" in results
        assert results["search_criteria"]["logic"] == "OR"
        # Should return samples with EITHER PFAM

    def test_response_structure(self):
        """Test that response has expected structure."""
        client = FunctionalBiosampleSearch()
        results = client.search_by_pfam(["PF00005"], limit=2)

        # Check top-level structure
        assert isinstance(results["count"], int)
        assert isinstance(results["results"], list)
        assert isinstance(results["search_criteria"], dict)

        # Check biosample structure if results exist
        if results["results"]:
            biosample = results["results"][0]
            assert "id" in biosample
            # May have omics_processing, study_id, etc.

    def test_pagination_offset(self):
        """Test pagination with offset."""
        client = FunctionalBiosampleSearch()

        # Get first page
        page1 = client.search_by_functions(["PFAM:PF00005"], limit=5, offset=0)

        # Get second page
        page2 = client.search_by_functions(["PFAM:PF00005"], limit=5, offset=5)

        # Results should be different (if enough samples exist)
        if len(page1["results"]) > 0 and len(page2["results"]) > 0:
            page1_ids = {r["id"] for r in page1["results"]}
            page2_ids = {r["id"] for r in page2["results"]}
            # Pages should have different biosamples
            assert page1_ids != page2_ids
