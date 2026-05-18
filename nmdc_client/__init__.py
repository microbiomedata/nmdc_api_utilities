# -*- coding: utf-8 -*-
"""
This file contains two kinds of things:
(1) metadata about this package, itself; and
(2) things that we want to make it particularly convenient for package users to import.

Reference: https://realpython.com/python-init-py/#what-kind-of-code-should-i-put-in-__init__py
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Optional


def get_package_version(package_name: str) -> Optional[str]:
    """
    Returns the version identifier (e.g., "1.2.3") of the package having the specified name.

    Args:
        package_name: The name of the package

    Returns:
        The version identifier of the package, or `None` if package not found
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


# The version identifier of this package.
# NOTE: Must be defined before the re-exports below, since some submodules
# (e.g. `api_client`) import `__version__` from this package at import time.
_version = get_package_version("nmdc-client")
__version__ = _version if _version is not None else "0.0.0"

# Enumeration of every submodule shipped by this package. Consumed by the
# `nmdc-api-utilities` backwards-compatibility shim to alias each submodule
# (e.g. `nmdc_api_utilities.config` → `nmdc_client.config`) via `sys.modules`.
__all_modules__ = (
    "api_client",
    "auth",
    "biosample_search",
    "calibration_search",
    "collecting_biosamples_from_site_search",
    "collection_search",
    "config",
    "configuration_search",
    "data_generation_search",
    "data_object_search",
    "data_processing",
    "data_staging",
    "decorators",
    "field_research_site_search",
    "functional_annotation_agg_search",
    "functional_search",
    "instrument_search",
    "lat_long_filters",
    "manifest_search",
    "material_processing_search",
    "metadata",
    "minter",
    "nmdc_search",
    "processed_sample_search",
    "storage_process_search",
    "study_search",
    "utils",
    "workflow_execution_search",
)

from nmdc_client.biosample_search import BiosampleSearch
from nmdc_client.calibration_search import CalibrationSearch
from nmdc_client.collecting_biosamples_from_site_search import (
    CollectingBiosamplesFromSiteSearch,
)
from nmdc_client.configuration_search import ConfigurationSearch
from nmdc_client.data_generation_search import DataGenerationSearch
from nmdc_client.data_object_search import DataObjectSearch
from nmdc_client.data_processing import DataProcessing
from nmdc_client.field_research_site_search import FieldResearchSiteSearch
from nmdc_client.functional_annotation_agg_search import (
    FunctionalAnnotationAggSearch,
)
from nmdc_client.functional_search import FunctionalSearch
from nmdc_client.instrument_search import InstrumentSearch
from nmdc_client.manifest_search import ManifestSearch
from nmdc_client.material_processing_search import MaterialProcessingSearch
from nmdc_client.nmdc_search import NMDCSearch
from nmdc_client.processed_sample_search import ProcessedSampleSearch
from nmdc_client.storage_process_search import StorageProcessSearch
from nmdc_client.study_search import StudySearch
from nmdc_client.workflow_execution_search import WorkflowExecutionSearch
