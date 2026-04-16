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
_version = get_package_version("nmdc_api_utilities")
__version__ = _version if _version is not None else "0.0.0"

from nmdc_api_utilities.biosample_search import BiosampleSearch
from nmdc_api_utilities.calibration_search import CalibrationSearch
from nmdc_api_utilities.collecting_biosamples_from_site_search import (
    CollectingBiosamplesFromSiteSearch,
)
from nmdc_api_utilities.configuration_search import ConfigurationSearch
from nmdc_api_utilities.data_generation_search import DataGenerationSearch
from nmdc_api_utilities.data_object_search import DataObjectSearch
from nmdc_api_utilities.data_processing import DataProcessing
from nmdc_api_utilities.field_research_site_search import FieldResearchSiteSearch
from nmdc_api_utilities.functional_annotation_agg_search import (
    FunctionalAnnotationAggSearch,
)
from nmdc_api_utilities.functional_search import FunctionalSearch
from nmdc_api_utilities.instrument_search import InstrumentSearch
from nmdc_api_utilities.manifest_search import ManifestSearch
from nmdc_api_utilities.material_processing_search import MaterialProcessingSearch
from nmdc_api_utilities.nmdc_search import NMDCSearch
from nmdc_api_utilities.processed_sample_search import ProcessedSampleSearch
from nmdc_api_utilities.storage_process_search import StorageProcessSearch
from nmdc_api_utilities.study_search import StudySearch
from nmdc_api_utilities.workflow_execution_search import WorkflowExecutionSearch
