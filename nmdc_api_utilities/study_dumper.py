# -*- coding: utf-8 -*-
"""
Module for dumping complete study data to a folder structure.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional
import requests
from urllib.parse import urlparse

from nmdc_api_utilities.study_search import StudySearch
from nmdc_api_utilities.biosample_search import BiosampleSearch
from nmdc_api_utilities.preprocessors import get_registry

logger = logging.getLogger(__name__)


class StudyDumper:
    """
    Dump a complete NMDC study to a folder structure with metadata and optional data files.

    Creates a folder structure:
    - study.json: Study metadata
    - manifest.json: Summary of what was dumped
    - One folder per biosample containing:
      - biosample.json: Biosample metadata
      - data_objects/: Folder with data object metadata and optional data files

    Parameters
    ----------
    study_id : str
        NMDC study ID (e.g., "nmdc:sty-11-547rwq94")
    output_dir : str or Path
        Output directory path
    env : str, optional
        API environment ("prod" or "dev"), default "prod"

    Examples
    --------
    >>> dumper = StudyDumper("nmdc:sty-11-547rwq94", "./my_study")
    >>> manifest = dumper.dump_study()  # Metadata only
    >>> manifest["study_id"]
    'nmdc:sty-11-547rwq94'

    >>> # With selective data download
    >>> manifest = dumper.dump_study(
    ...     download_data=True,
    ...     include_types=["Metagenome Raw Reads"],
    ...     max_size_mb=1000
    ... )
    """

    def __init__(self, study_id: str, output_dir: str | Path, env: str = "prod"):
        self.study_id = study_id
        self.output_dir = Path(output_dir)
        self.env = env

        # Initialize API clients
        self.study_client = StudySearch(env=env)
        self.biosample_client = BiosampleSearch(env=env)

        # Statistics
        self.stats = {
            "biosamples": 0,
            "data_objects": 0,
            "files_downloaded": 0,
            "bytes_downloaded": 0,
            "files_preprocessed": 0,
            "errors": []
        }

        # Preprocessor registry
        self.preprocessor_registry = get_registry()

    def dump_study(
        self,
        download_data: bool = False,
        include_types: list[str] | None = None,
        max_size_mb: int | None = None,
        skip_existing: bool = True,
        preprocess: bool = True,
        progress_callback: callable = None
    ) -> dict:
        """
        Dump complete study to folder structure.

        Parameters
        ----------
        download_data : bool, default False
            Whether to download actual data files from URLs
        include_types : list[str], optional
            Only download data files of these types (e.g., ["Metagenome Raw Reads"])
            If None and download_data=True, downloads all types
        max_size_mb : int, optional
            Skip downloading files larger than this size in MB
        skip_existing : bool, default True
            Skip downloading files that already exist
        preprocess : bool, default True
            Whether to preprocess downloaded files (e.g., add headers to TSV files)
        progress_callback : callable, optional
            Function to call with progress updates (message: str, current: int, total: int)

        Returns
        -------
        dict
            Manifest with summary of what was dumped

        Raises
        ------
        ValueError
            If study_id is invalid
        RuntimeError
            If study cannot be retrieved from API
        """
        logger.info(f"Starting study dump: {self.study_id} -> {self.output_dir}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Get and save study metadata
        self._report_progress(progress_callback, "Fetching study metadata...", 0, 5)
        study_data = self._get_study_metadata()
        self._save_json(self.output_dir / "study.json", study_data)

        # 2. Get all biosamples for study
        self._report_progress(progress_callback, "Fetching biosamples...", 1, 5)
        biosamples = self.study_client.get_linked_biosamples(self.study_id, hydrate=True)
        self.stats["biosamples"] = len(biosamples)
        logger.info(f"Found {len(biosamples)} biosamples")

        # 3. Process each biosample
        self._report_progress(progress_callback, f"Processing {len(biosamples)} biosamples...", 2, 5)
        for i, biosample in enumerate(biosamples):
            self._process_biosample(
                biosample,
                download_data=download_data,
                include_types=include_types,
                max_size_mb=max_size_mb,
                skip_existing=skip_existing,
                preprocess=preprocess,
                progress_callback=progress_callback,
                biosample_index=i,
                total_biosamples=len(biosamples)
            )

        # 4. Create manifest
        self._report_progress(progress_callback, "Creating manifest...", 4, 5)
        manifest = self._create_manifest(study_data, biosamples)
        self._save_json(self.output_dir / "manifest.json", manifest)

        self._report_progress(progress_callback, "Complete!", 5, 5)
        logger.info(f"Study dump complete: {self.stats}")

        return manifest

    def _get_study_metadata(self) -> dict:
        """Fetch study metadata from API."""
        try:
            study_data = self.study_client.get_record_by_id(self.study_id)
            if not study_data:
                raise RuntimeError(f"Study not found: {self.study_id}")
            return study_data
        except Exception as e:
            logger.error(f"Failed to fetch study metadata: {e}")
            raise RuntimeError(f"Could not retrieve study {self.study_id}") from e

    def _process_biosample(
        self,
        biosample: dict,
        download_data: bool,
        include_types: list[str] | None,
        max_size_mb: int | None,
        skip_existing: bool,
        preprocess: bool,
        progress_callback: callable,
        biosample_index: int,
        total_biosamples: int
    ):
        """Process a single biosample: save metadata and data objects."""
        biosample_id = biosample["id"]
        logger.info(f"Processing biosample {biosample_index + 1}/{total_biosamples}: {biosample_id}")

        # Create biosample directory
        biosample_dir = self.output_dir / self._sanitize_filename(biosample_id)
        biosample_dir.mkdir(parents=True, exist_ok=True)

        # Save biosample metadata
        self._save_json(biosample_dir / "biosample.json", biosample)

        # Get data objects for this biosample
        try:
            data_objects = self.biosample_client.get_linked_data_objects(
                biosample_id,
                hydrate=True
            )

            # Filter by include_types if specified (before processing to save API calls and disk space)
            if include_types:
                original_count = len(data_objects)
                data_objects = [
                    obj for obj in data_objects
                    if obj.get("data_object_type") in include_types
                ]
                logger.info(f"  Found {len(data_objects)} matching data objects (filtered from {original_count})")
            else:
                logger.info(f"  Found {len(data_objects)} data objects")

            self.stats["data_objects"] += len(data_objects)
        except Exception as e:
            error_msg = f"Failed to get data objects for {biosample_id}: {e}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return

        # Create data_objects subdirectory
        data_objects_dir = biosample_dir / "data_objects"
        data_objects_dir.mkdir(exist_ok=True)

        # Process each data object
        for data_obj in data_objects:
            self._process_data_object(
                data_obj,
                data_objects_dir,
                download_data=download_data,
                include_types=include_types,
                max_size_mb=max_size_mb,
                skip_existing=skip_existing,
                preprocess=preprocess
            )

    def _process_data_object(
        self,
        data_obj: dict,
        output_dir: Path,
        download_data: bool,
        include_types: list[str] | None,
        max_size_mb: int | None,
        skip_existing: bool,
        preprocess: bool
    ):
        """Process a single data object: save metadata and optionally download data."""
        data_obj_id = data_obj["id"]

        # Save data object metadata
        metadata_file = output_dir / f"{self._sanitize_filename(data_obj_id)}.json"
        self._save_json(metadata_file, data_obj)

        # Download data if requested
        if download_data:
            self._download_data_file(
                data_obj,
                output_dir,
                include_types=include_types,
                max_size_mb=max_size_mb,
                skip_existing=skip_existing,
                preprocess=preprocess
            )

    def _download_data_file(
        self,
        data_obj: dict,
        output_dir: Path,
        include_types: list[str] | None,
        max_size_mb: int | None,
        skip_existing: bool,
        preprocess: bool
    ):
        """Download actual data file from URL."""
        data_obj_id = data_obj["id"]
        url = data_obj.get("url")
        file_size_bytes = data_obj.get("file_size_bytes")

        # Check if URL exists
        if not url:
            logger.warning(f"  No URL for {data_obj_id}")
            return

        # Note: type filtering is done earlier in _process_biosample to avoid processing unwanted metadata

        # Check size limit
        if max_size_mb and file_size_bytes:
            size_mb = file_size_bytes / (1024 * 1024)
            if size_mb > max_size_mb:
                logger.info(f"  Skipping {data_obj_id} ({size_mb:.1f} MB > {max_size_mb} MB limit)")
                return

        # Determine output filename from URL
        filename = self._get_filename_from_url(url, data_obj)
        output_file = output_dir / filename

        # Skip if exists
        if skip_existing and output_file.exists():
            logger.debug(f"  Skipping {data_obj_id} (file exists)")
            return

        # Download file
        try:
            logger.info(f"  Downloading {data_obj_id} -> {filename}")
            self._download_file(url, output_file)
            self.stats["files_downloaded"] += 1
            if file_size_bytes:
                self.stats["bytes_downloaded"] += file_size_bytes

            # Preprocess file if enabled
            if preprocess:
                processed_file = self.preprocessor_registry.preprocess_file(data_obj, output_file)
                if processed_file:
                    self.stats["files_preprocessed"] += 1
        except Exception as e:
            error_msg = f"Failed to download {data_obj_id} from {url}: {e}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)

    def _download_file(self, url: str, output_path: Path, chunk_size: int = 8192):
        """Download file from URL with streaming."""
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)

    def _get_filename_from_url(self, url: str, data_obj: dict) -> str:
        """Extract filename from URL or data object metadata."""
        # Try to get from name field first
        if "name" in data_obj and data_obj["name"]:
            return self._sanitize_filename(data_obj["name"])

        # Try to get from URL path
        parsed_url = urlparse(url)
        path = Path(parsed_url.path)
        if path.name:
            return self._sanitize_filename(path.name)

        # Fallback: use data object ID + extension from description
        data_obj_id = data_obj["id"]
        description = data_obj.get("description", "")

        # Try to infer extension from data_object_type or description
        ext = ".dat"  # Default
        if "fastq" in description.lower() or "Raw Reads" in data_obj.get("data_object_type", ""):
            ext = ".fastq.gz"
        elif "assembly" in description.lower() or "Assembly" in data_obj.get("data_object_type", ""):
            ext = ".fasta"

        return f"{self._sanitize_filename(data_obj_id)}{ext}"

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use as filename."""
        # Replace characters that might cause issues
        return name.replace(":", "_").replace("/", "_").replace("\\", "_")

    def _save_json(self, path: Path, data: dict):
        """Save data as pretty-printed JSON."""
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _create_manifest(self, study_data: dict, biosamples: list[dict]) -> dict:
        """Create manifest summary."""
        return {
            "study_id": self.study_id,
            "study_title": study_data.get("title", ""),
            "dump_location": str(self.output_dir),
            "statistics": {
                "biosamples": self.stats["biosamples"],
                "data_objects": self.stats["data_objects"],
                "files_downloaded": self.stats["files_downloaded"],
                "bytes_downloaded": self.stats["bytes_downloaded"],
                "download_size_mb": round(self.stats["bytes_downloaded"] / (1024 * 1024), 2),
                "files_preprocessed": self.stats["files_preprocessed"]
            },
            "preprocessing": {
                "enabled": self.stats["files_preprocessed"] > 0,
                "files_processed": self.stats["files_preprocessed"],
                "preprocessors_available": [p.get_description() for p in self.preprocessor_registry.preprocessors]
            },
            "errors": self.stats["errors"],
            "biosample_ids": [b["id"] for b in biosamples]
        }

    def _report_progress(self, callback: callable, message: str, current: int, total: int):
        """Report progress if callback provided."""
        if callback:
            callback(message, current, total)

    def sniff_preprocessable_files(self) -> dict:
        """
        Preview what files would be preprocessed without downloading.

        Returns
        -------
        dict
            Summary of preprocessable files grouped by preprocessor type
        """
        logger.info(f"Sniffing preprocessable files for study: {self.study_id}")

        # Get study and biosamples
        study_data = self._get_study_metadata()
        biosamples = self.study_client.get_linked_biosamples(self.study_id, hydrate=True)

        preprocessable_files = {}
        total_files = 0

        for biosample in biosamples:
            biosample_id = biosample["id"]
            try:
                data_objects = self.biosample_client.get_linked_data_objects(
                    biosample_id, hydrate=True
                )

                for data_obj in data_objects:
                    data_obj_id = data_obj["id"]
                    url = data_obj.get("url")
                    if not url:
                        continue

                    # Get filename
                    filename = self._get_filename_from_url(url, data_obj)
                    filepath = Path(filename)  # Mock path for checking

                    # Check if any preprocessor can handle this
                    preprocessor = self.preprocessor_registry.get_preprocessor(data_obj, filepath)
                    if preprocessor:
                        alias = preprocessor.alias
                        if alias not in preprocessable_files:
                            preprocessable_files[alias] = {
                                "cv_term": preprocessor.cv_term,
                                "description": preprocessor.get_description(),
                                "expected_prefixes": preprocessor.expected_prefixes,
                                "files": []
                            }

                        preprocessable_files[alias]["files"].append({
                            "data_object_id": data_obj_id,
                            "biosample_id": biosample_id,
                            "filename": filename,
                            "file_size_mb": round(data_obj.get("file_size_bytes", 0) / (1024 * 1024), 2) if data_obj.get("file_size_bytes") else None
                        })
                        total_files += 1

            except Exception as e:
                logger.error(f"Failed to get data objects for {biosample_id}: {e}")
                continue

        return {
            "study_id": self.study_id,
            "study_title": study_data.get("title", ""),
            "total_biosamples": len(biosamples),
            "total_preprocessable_files": total_files,
            "by_preprocessor": preprocessable_files
        }
