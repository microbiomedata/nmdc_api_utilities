# -*- coding: utf-8 -*-
"""
Preprocessors for NMDC data files.

This module provides a framework for transforming downloaded NMDC data files
into more analysis-friendly formats (e.g., adding headers to TSV files).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Preprocessor(ABC):
    """
    Abstract base class for data file preprocessors.

    Preprocessors transform downloaded data files to make them more usable
    (e.g., adding headers to headerless TSV files).

    Attributes
    ----------
    alias : str
        Short identifier for CLI use (e.g., "ko", "ec")
    cv_term : str
        NMDC controlled vocabulary term (e.g., "Annotation KEGG Orthology")
    expected_prefixes : list[str]
        Filename patterns this preprocessor handles (e.g., ["_ko.tsv", "_ko_"])
    """

    @property
    @abstractmethod
    def alias(self) -> str:
        """Short identifier for CLI use."""
        pass

    @property
    @abstractmethod
    def cv_term(self) -> str:
        """NMDC controlled vocabulary term."""
        pass

    @property
    @abstractmethod
    def expected_prefixes(self) -> list[str]:
        """Filename patterns this preprocessor handles."""
        pass

    @abstractmethod
    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        """
        Check if this preprocessor can handle the given file.

        Parameters
        ----------
        data_obj : dict
            Data object metadata from NMDC API
        filepath : Path
            Path to the downloaded file

        Returns
        -------
        bool
            True if this preprocessor can handle this file
        """
        pass

    @abstractmethod
    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        """
        Preprocess the file.

        Parameters
        ----------
        filepath : Path
            Path to the file to preprocess
        data_obj : dict
            Data object metadata (for context)

        Returns
        -------
        Path or None
            Path to the processed file, or None if processing failed
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get a human-readable description of what this preprocessor does."""
        pass


class KEGGAnnotationPreprocessor(Preprocessor):
    """
    Preprocessor for KEGG orthology annotation files.

    NMDC KEGG annotation files (*_ko.tsv) lack headers. This preprocessor adds
    the appropriate column names based on the NMDC Metagenome Annotation workflow output format.
    """

    # Column names for KEGG annotation files
    KEGG_COLUMNS = [
        "gene_id",
        "img_ko_flag",
        "ko_term",
        "percent_identity",
        "query_start",
        "query_end",
        "subj_start",
        "subj_end",
        "evalue",
        "bit_score",
        "align_length"
    ]

    @property
    def alias(self) -> str:
        return "ko"

    @property
    def cv_term(self) -> str:
        return "Annotation KEGG Orthology"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_ko.tsv", "_ko_"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        """Check if file is a KEGG annotation file."""
        # Check filename pattern
        if "_ko.tsv" in filepath.name.lower() or "_ko_" in filepath.name.lower():
            return True

        # Check data_object_type
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")

        if "KEGG" in data_obj_type or "KEGG" in description:
            if data_obj_type == "Functional Annotation" or "ko" in description.lower():
                return True

        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        """Add header to KEGG annotation TSV file."""
        try:
            # Read original file
            with open(filepath, "r") as f:
                lines = f.readlines()

            if not lines:
                logger.warning(f"Empty file: {filepath}")
                return None

            # Check if already has header
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "gene_id" or "gene_id" in first_line[0].lower():
                logger.debug(f"File already has header: {filepath}")
                return filepath

            # Create output path
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"

            # Write processed file with header
            with open(output_path, "w") as f:
                # Write header
                f.write("\t".join(self.KEGG_COLUMNS) + "\n")
                # Write original data
                f.writelines(lines)

            logger.info(f"Preprocessed KEGG file: {filepath.name} -> {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to KEGG orthology annotation TSV files"


class ECAnnotationPreprocessor(Preprocessor):
    """
    Preprocessor for EC number annotation files.

    Similar to KEGG annotations but for EC numbers.
    """

    # Column names for EC annotation files
    EC_COLUMNS = [
        "gene_id",
        "img_ko_flag",
        "EC",
        "percent_identity",
        "query_start",
        "query_end",
        "subj_start",
        "subj_end",
        "evalue",
        "bit_score",
        "align_length"
    ]

    @property
    def alias(self) -> str:
        return "ec"

    @property
    def cv_term(self) -> str:
        return "Annotation Enzyme Commission"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_ec.tsv", "_ec_"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        """Check if file is an EC annotation file."""
        # Check filename pattern
        if "_ec.tsv" in filepath.name.lower() or "_ec_" in filepath.name.lower():
            return True

        # Check data_object_type
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")

        if "EC" in data_obj_type or " EC " in description:
            if data_obj_type == "Functional Annotation" or "ec" in description.lower():
                return True

        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        """Add header to EC annotation TSV file."""
        try:
            # Read original file
            with open(filepath, "r") as f:
                lines = f.readlines()

            if not lines:
                logger.warning(f"Empty file: {filepath}")
                return None

            # Check if already has header
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "gene_id" or "gene_id" in first_line[0].lower():
                logger.debug(f"File already has header: {filepath}")
                return filepath

            # Create output path
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"

            # Write processed file with header
            with open(output_path, "w") as f:
                # Write header
                f.write("\t".join(self.EC_COLUMNS) + "\n")
                # Write original data
                f.writelines(lines)

            logger.info(f"Preprocessed EC file: {filepath.name} -> {output_path.name}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to EC number annotation TSV files"


class COGAnnotationPreprocessor(Preprocessor):
    """Preprocessor for COG (Clusters of Orthologous Groups) annotation files."""

    COG_COLUMNS = [
        "feature_id",
        "subject_id",
        "cog_id",
        "identity",
        "alignment_length",
        "mismatches",
        "gap_opens",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "evalue",
        "bitscore"
    ]

    @property
    def alias(self) -> str:
        return "cog"

    @property
    def cv_term(self) -> str:
        return "Annotation Clusters of Orthologous Groups"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_cog.tsv", "_cog_"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        if "_cog.tsv" in filepath.name.lower() or "_cog_" in filepath.name.lower():
            return True
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")
        if "COG" in data_obj_type or "COG" in description:
            return True
        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            if not lines:
                return None
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "feature_id":
                return filepath
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"
            with open(output_path, "w") as f:
                f.write("\t".join(self.COG_COLUMNS) + "\n")
                f.writelines(lines)
            logger.info(f"Preprocessed COG file: {filepath.name} -> {output_path.name}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to COG annotation TSV files"


class PFAMAnnotationPreprocessor(Preprocessor):
    """Preprocessor for PFAM (Protein families) annotation files."""

    PFAM_COLUMNS = [
        "feature_id",
        "subject_id",
        "pfam_id",
        "identity",
        "alignment_length",
        "mismatches",
        "gap_opens",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "evalue",
        "bitscore"
    ]

    @property
    def alias(self) -> str:
        return "pfam"

    @property
    def cv_term(self) -> str:
        return "Annotation PFAM"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_pfam.tsv", "_pfam_"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        if "_pfam.tsv" in filepath.name.lower() or "_pfam_" in filepath.name.lower():
            return True
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")
        if "PFAM" in data_obj_type or "PFAM" in description or "Pfam" in description:
            return True
        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            if not lines:
                return None
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "feature_id":
                return filepath
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"
            with open(output_path, "w") as f:
                f.write("\t".join(self.PFAM_COLUMNS) + "\n")
                f.writelines(lines)
            logger.info(f"Preprocessed PFAM file: {filepath.name} -> {output_path.name}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to PFAM annotation TSV files"


class CATHFunFamsAnnotationPreprocessor(Preprocessor):
    """Preprocessor for CATH-FunFams annotation files."""

    CATH_COLUMNS = [
        "feature_id",
        "subject_id",
        "cath_id",
        "identity",
        "alignment_length",
        "mismatches",
        "gap_opens",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "evalue",
        "bitscore"
    ]

    @property
    def alias(self) -> str:
        return "cath"

    @property
    def cv_term(self) -> str:
        return "Annotation CATH FunFams"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_cath.tsv", "_cath_", "_cath_funfam"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        if "_cath" in filepath.name.lower():
            return True
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")
        if "CATH" in data_obj_type or "CATH" in description:
            return True
        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            if not lines:
                return None
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "feature_id":
                return filepath
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"
            with open(output_path, "w") as f:
                f.write("\t".join(self.CATH_COLUMNS) + "\n")
                f.writelines(lines)
            logger.info(f"Preprocessed CATH-FunFams file: {filepath.name} -> {output_path.name}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to CATH-FunFams annotation TSV files"


class SUPERFAMAnnotationPreprocessor(Preprocessor):
    """Preprocessor for SUPERFAM annotation files."""

    SUPERFAM_COLUMNS = [
        "feature_id",
        "subject_id",
        "superfam_id",
        "identity",
        "alignment_length",
        "mismatches",
        "gap_opens",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "evalue",
        "bitscore"
    ]

    @property
    def alias(self) -> str:
        return "superfam"

    @property
    def cv_term(self) -> str:
        return "Annotation SUPERFAMILY"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_supfam.tsv", "_supfam_", "_superfam"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        if "_supfam" in filepath.name.lower() or "_superfam" in filepath.name.lower():
            return True
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")
        if "SUPERFAM" in data_obj_type or "SUPERFAM" in description:
            return True
        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            if not lines:
                return None
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "feature_id":
                return filepath
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"
            with open(output_path, "w") as f:
                f.write("\t".join(self.SUPERFAM_COLUMNS) + "\n")
                f.writelines(lines)
            logger.info(f"Preprocessed SUPERFAM file: {filepath.name} -> {output_path.name}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to SUPERFAMILY annotation TSV files"


class SMARTAnnotationPreprocessor(Preprocessor):
    """Preprocessor for SMART (Simple Modular Architecture Research Tool) annotation files."""

    SMART_COLUMNS = [
        "feature_id",
        "subject_id",
        "smart_id",
        "identity",
        "alignment_length",
        "mismatches",
        "gap_opens",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "evalue",
        "bitscore"
    ]

    @property
    def alias(self) -> str:
        return "smart"

    @property
    def cv_term(self) -> str:
        return "Annotation SMART"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_smart.tsv", "_smart_"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        if "_smart" in filepath.name.lower():
            return True
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")
        if "SMART" in data_obj_type or "SMART" in description:
            return True
        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            if not lines:
                return None
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "feature_id":
                return filepath
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"
            with open(output_path, "w") as f:
                f.write("\t".join(self.SMART_COLUMNS) + "\n")
                f.writelines(lines)
            logger.info(f"Preprocessed SMART file: {filepath.name} -> {output_path.name}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to SMART annotation TSV files"


class TIGRFAMAnnotationPreprocessor(Preprocessor):
    """Preprocessor for TIGRFAM annotation files."""

    TIGRFAM_COLUMNS = [
        "feature_id",
        "subject_id",
        "tigrfam_id",
        "identity",
        "alignment_length",
        "mismatches",
        "gap_opens",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "evalue",
        "bitscore"
    ]

    @property
    def alias(self) -> str:
        return "tigrfam"

    @property
    def cv_term(self) -> str:
        return "Annotation TIGRFAMs"

    @property
    def expected_prefixes(self) -> list[str]:
        return ["_tigrfam.tsv", "_tigrfam_"]

    def can_process(self, data_obj: dict, filepath: Path) -> bool:
        if "_tigrfam" in filepath.name.lower():
            return True
        data_obj_type = data_obj.get("data_object_type", "")
        description = data_obj.get("description", "")
        if "TIGRFAM" in data_obj_type or "TIGRFAM" in description:
            return True
        return False

    def preprocess(self, filepath: Path, data_obj: dict) -> Optional[Path]:
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            if not lines:
                return None
            first_line = lines[0].strip().split("\t")
            if first_line[0].lower() == "feature_id":
                return filepath
            output_path = filepath.parent / f"{filepath.stem}.processed{filepath.suffix}"
            with open(output_path, "w") as f:
                f.write("\t".join(self.TIGRFAM_COLUMNS) + "\n")
                f.writelines(lines)
            logger.info(f"Preprocessed TIGRFAM file: {filepath.name} -> {output_path.name}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to preprocess {filepath}: {e}")
            return None

    def get_description(self) -> str:
        return "Add column headers to TIGRFAM annotation TSV files"


class PreprocessorRegistry:
    """
    Registry for managing and applying preprocessors to files.
    """

    def __init__(self):
        self.preprocessors: list[Preprocessor] = []
        self._register_defaults()

    def _register_defaults(self):
        """Register default preprocessors."""
        self.register(KEGGAnnotationPreprocessor())
        self.register(ECAnnotationPreprocessor())
        self.register(COGAnnotationPreprocessor())
        self.register(PFAMAnnotationPreprocessor())
        self.register(CATHFunFamsAnnotationPreprocessor())
        self.register(SUPERFAMAnnotationPreprocessor())
        self.register(SMARTAnnotationPreprocessor())
        self.register(TIGRFAMAnnotationPreprocessor())

    def register(self, preprocessor: Preprocessor):
        """Register a new preprocessor."""
        self.preprocessors.append(preprocessor)
        logger.debug(f"Registered preprocessor: {preprocessor.get_description()}")

    def get_preprocessor(self, data_obj: dict, filepath: Path) -> Optional[Preprocessor]:
        """
        Find a preprocessor that can handle the given file.

        Parameters
        ----------
        data_obj : dict
            Data object metadata
        filepath : Path
            Path to the file

        Returns
        -------
        Preprocessor or None
            A preprocessor that can handle this file, or None
        """
        for preprocessor in self.preprocessors:
            if preprocessor.can_process(data_obj, filepath):
                return preprocessor
        return None

    def preprocess_file(self, data_obj: dict, filepath: Path) -> Optional[Path]:
        """
        Preprocess a file if a suitable preprocessor is available.

        Parameters
        ----------
        data_obj : dict
            Data object metadata
        filepath : Path
            Path to the file to preprocess

        Returns
        -------
        Path or None
            Path to processed file (might be same as input if no preprocessing needed),
            or None if preprocessing failed
        """
        preprocessor = self.get_preprocessor(data_obj, filepath)
        if preprocessor:
            logger.info(f"Preprocessing {filepath.name} with {preprocessor.__class__.__name__}")
            return preprocessor.preprocess(filepath, data_obj)
        return None

    def list_preprocessors(self) -> list[str]:
        """Get list of registered preprocessor descriptions."""
        return [p.get_description() for p in self.preprocessors]


# Global registry instance
_registry = PreprocessorRegistry()


def get_registry() -> PreprocessorRegistry:
    """Get the global preprocessor registry."""
    return _registry
