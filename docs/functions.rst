Public Core API Reference
=========================

This page documents public, reusable core classes.
Collection-specific subclasses are documented in :doc:`public_subclasses`.

NMDC Search Base
----------------

The foundational class for cross-collection queries and linked-instance retrieval.
Use this class for custom workflows that span multiple schema classes.

.. autoclass:: nmdc_api_utilities.nmdc_search.NMDCSearch
   :members:
   :undoc-members:
   :show-inheritance:

Collection Search Base
----------------------

Extends ``NMDCSearch`` with collection-focused query helpers.
Use this class for generic collection operations, or use :doc:`public_subclasses` for preconfigured collection targets.

.. autoclass:: nmdc_api_utilities.collection_search.CollectionSearch
   :members:
   :undoc-members:
   :show-inheritance:

Functional Search
-----------------

Provides search utilities focused on functional annotation and related retrieval patterns.

.. autoclass:: nmdc_api_utilities.functional_search.FunctionalSearch
   :members:
   :undoc-members:
   :show-inheritance:

Latitude and Longitude Utilities
--------------------------------

Provides geospatial helper methods for lat/lon-based filtering and coordinate handling.

.. autoclass:: nmdc_api_utilities.lat_long_filters.LatLongFilters
   :members:
   :undoc-members:
   :show-inheritance:

Data Processing Utilities
-------------------------

Provides helpers for transforming and reshaping query outputs.

.. autoclass:: nmdc_api_utilities.data_processing.DataProcessing
   :members:
   :undoc-members:
   :show-inheritance:

General Utilities
-----------------

General-purpose helper utilities used across workflows.

.. autoclass:: nmdc_api_utilities.utils.Utils
   :members:
   :undoc-members:
   :show-inheritance:
