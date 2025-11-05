# -*- coding: utf-8 -*-
"""
Tests for GFF parsing when PFAM IDs are in column 3 (type field).

Some NMDC GFF files (particularly from HMMER output) have the PFAM ID
in the type column (column 3) rather than in the attributes.
"""
import pytest
import tempfile
from pathlib import Path


class TestGFFPfamInTypeColumn:
    """Tests for GFF files with PFAM in the type column."""

    @pytest.fixture
    def pfam_gff_file(self):
        """Create a temporary GFF file with PFAM in column 3."""
        # This format has PFAM ID in column 3 (type field)
        gff_content = """nmdc:wfmgan-11-fw38xr59.1_0000001_101492_102622\tHMMER 3.1b2 (February 2015)\tPF01041\t15\t363\t407.0\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_101492_102622_15_363;Name=DegT_DnrJ_EryC1;fake_percent_id=76.47;alignment_length=349;e-value=3.2e-119;model_start=6;model_end=359
nmdc:wfmgan-11-fw38xr59.1_0000001_102603_103142\tHMMER 3.1b2 (February 2015)\tPF14602\t116\t146\t21.3\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_102603_103142_116_146;Name=Hexapep_2;fake_percent_id=99.17;alignment_length=31;e-value=0.071;model_start=9;model_end=34
nmdc:wfmgan-11-fw38xr59.1_0000001_103139_104170\tHMMER 3.1b2 (February 2015)\tPF01408\t5\t124\t73.0\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_103139_104170_5_124;Name=GFO_IDH_MocA;fake_percent_id=99.46;alignment_length=120;e-value=1.4e-17;model_start=2;model_end=120
nmdc:wfmgan-11-fw38xr59.1_0000001_103139_104170\tHMMER 3.1b2 (February 2015)\tPF02894\t136\t338\t31.1\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_103139_104170_136_338;Name=GFO_IDH_MocA_C;fake_percent_id=99.46;alignment_length=203;e-value=8.4e-05;model_start=42;model_end=219
nmdc:wfmgan-11-fw38xr59.1_0000001_104167_104901\tHMMER 3.1b2 (February 2015)\tPF02397\t16\t209\t196.4\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_104167_104901_16_209;Name=Bac_transf;fake_percent_id=76.52;alignment_length=194;e-value=1.4e-55;model_start=1;model_end=183
nmdc:wfmgan-11-fw38xr59.1_0000001_104986_105759\tHMMER 3.1b2 (February 2015)\tPF00483\t2\t235\t25.1\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_104986_105759_2_235;Name=NTP_transferase;fake_percent_id=99.07;alignment_length=234;e-value=0.0051;model_start=2;model_end=190
nmdc:wfmgan-11-fw38xr59.1_0000001_107628_108563\tHMMER 3.1b2 (February 2015)\tPF00483\t2\t239\t195.3\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_107628_108563_2_239;Name=NTP_transferase;fake_percent_id=98.26;alignment_length=238;e-value=5.3e-55;model_start=1;model_end=245
nmdc:wfmgan-11-fw38xr59.1_0000001_109244_110152\tHMMER 3.1b2 (February 2015)\tPF04321\t1\t296\t302.4\t.\t.\tID=nmdc:wfmgan-11-fw38xr59.1_0000001_109244_110152_1_296;Name=RmlD_sub_bind;fake_percent_id=100.00;alignment_length=296;e-value=1.1e-87;model_start=2;model_end=283
"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gff', delete=False) as f:
            f.write(gff_content)
            temp_path = f.name

        yield Path(temp_path)

        # Cleanup
        Path(temp_path).unlink()

    def test_load_pfam_gff(self, pfam_gff_file):
        """Test that GFF file with PFAM in type column loads correctly."""
        from nmdc_api_utilities.gff_utils import GFFReader

        reader = GFFReader(pfam_gff_file, use_duckdb=False)

        # Should have 8 features
        assert len(reader.df) == 8

        # Check that type column contains PFAM IDs
        assert "PF01041" in reader.df["type"].values
        assert "PF14602" in reader.df["type"].values
        assert "PF00483" in reader.df["type"].values

    def test_pfam_column_populated_from_type(self, pfam_gff_file):
        """Test that pfam column is populated from type column when it contains PFAM IDs."""
        from nmdc_api_utilities.gff_utils import GFFReader

        reader = GFFReader(pfam_gff_file, use_duckdb=False)

        # The pfam column should be populated from the type column
        assert reader.df["pfam"].notna().sum() == 8  # All 8 rows should have PFAM

        # Specific PFAM IDs should be in the pfam column
        assert "PF01041" in reader.df["pfam"].values
        assert "PF14602" in reader.df["pfam"].values
        assert "PF01408" in reader.df["pfam"].values

    def test_query_by_pfam_from_type_column(self, pfam_gff_file):
        """Test that query_by_pfam works when PFAM is in type column."""
        from nmdc_api_utilities.gff_utils import GFFReader

        reader = GFFReader(pfam_gff_file, use_duckdb=False)

        # Query for PF00483 (appears twice in the test data)
        results = reader.query_by_pfam("PF00483")
        assert len(results) == 2

        # Verify they're the right features
        assert all(results["pfam"] == "PF00483")

    def test_query_by_pfam_single_result(self, pfam_gff_file):
        """Test querying for a PFAM that appears once."""
        from nmdc_api_utilities.gff_utils import GFFReader

        reader = GFFReader(pfam_gff_file, use_duckdb=False)

        # Query for PF01041 (appears once)
        results = reader.query_by_pfam("PF01041")
        assert len(results) == 1
        assert results.iloc[0]["pfam"] == "PF01041"
        # Verify it's the right feature by checking the ID
        assert "nmdc:wfmgan-11-fw38xr59.1_0000001_101492_102622" in results.iloc[0]["ID"]

    def test_mixed_format_gff(self):
        """Test GFF with PFAM in both type column AND attributes."""
        # Create a GFF with mixed formats
        gff_content = """gene1\tprodigal\tCDS\t100\t200\t50.0\t+\t0\tID=gene1;product=kinase;pfam=PF12345
gene2\tHMMER\tPF67890\t300\t400\t60.0\t+\t0\tID=gene2;product=transporter
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gff', delete=False) as f:
            f.write(gff_content)
            temp_path = f.name

        try:
            from nmdc_api_utilities.gff_utils import GFFReader
            reader = GFFReader(temp_path, use_duckdb=False)

            # Both should have PFAM populated
            assert len(reader.df) == 2
            assert reader.df["pfam"].notna().sum() == 2

            # First one from attributes
            assert reader.df.iloc[0]["pfam"] == "PF12345"

            # Second one from type column
            assert reader.df.iloc[1]["pfam"] == "PF67890"

        finally:
            Path(temp_path).unlink()

    def test_duckdb_mode_with_pfam_in_type(self, pfam_gff_file):
        """Test that DuckDB mode also works with PFAM in type column."""
        try:
            import duckdb  # noqa: F401
        except ImportError:
            pytest.skip("DuckDB not available")

        from nmdc_api_utilities.gff_utils import GFFReader

        reader = GFFReader(pfam_gff_file, use_duckdb=True)

        # Query for PF00483
        results = reader.query_by_pfam("PF00483")
        assert len(results) == 2

    def test_pfam_id_pattern_detection(self):
        """Test that we correctly identify PFAM ID patterns."""
        from nmdc_api_utilities.gff_utils import GFFReader
        import re

        # Should match PFAM IDs
        pfam_pattern = re.compile(r'^PF\d{5}$')
        assert pfam_pattern.match("PF00005")
        assert pfam_pattern.match("PF12345")
        assert pfam_pattern.match("PF01041")

        # Should not match non-PFAM
        assert not pfam_pattern.match("CDS")
        assert not pfam_pattern.match("gene")
        assert not pfam_pattern.match("PF123")  # Too short
        assert not pfam_pattern.match("PF1234567")  # Too long
        assert not pfam_pattern.match("pfam:PF00005")  # Has prefix
