Filtering and Querying Data (Python)
====================================

This guide covers Python-first filtering with NMDC API Utilities.
Filters use MongoDB query syntax and can be passed directly or built with helper methods.

Quick Start
-----------

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch

   client = BiosampleSearch()
   results = client.get_record_by_filter('{"id": "nmdc:bsm-11-006pnx90"}')

Filter Formats
--------------

Mongo-style JSON filter strings are accepted by ``get_record_by_filter`` and ``get_records``.

Examples:

.. code-block:: python

   # Exact match
   '{"id": "nmdc:sty-11-8fb6t785"}'

   # Case-insensitive partial match
   '{"name": {"$regex": "forest", "$options": "i"}}'

   # Multiple criteria (implicit AND)
   '{"ecosystem_category": "Plants", "lat_lon": {"$exists": true}}'

   # Nested field (dot notation)
   '{"env_broad_scale.has_raw_value": "Forest biome"}'

Supported Mongo Operators
-------------------------

- ``$regex`` for pattern matching
- ``$options`` for regex options (for example, ``"i"``)
- ``$exists`` for field presence
- ``$in`` for matching any value in an array
- ``$gte`` and ``$lte`` for range filters
- ``$and`` and ``$or`` for compound logic

Direct Filter Usage
-------------------

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch

   client = BiosampleSearch()

   filter_str = '{"name": {"$regex": "forest", "$options": "i"}}'
   records = client.get_record_by_filter(filter_str)

Build Filters Programmatically
------------------------------

Use ``DataProcessing.build_filter`` to create filters from Python dictionaries.
By default, it builds case-insensitive regex filters and escapes special characters.

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch
   from nmdc_api_utilities.data_processing import DataProcessing

   client = BiosampleSearch()
   dp = DataProcessing()

   filter_str = dp.build_filter({"name": "GC-MS (2009)"})
   records = client.get_record_by_filter(filter_str)

   exact_filter = dp.build_filter({"ecosystem_category": "Plants"}, exact_match=True)
   exact_records = client.get_record_by_filter(exact_filter)

Attribute-Based Query Helper
----------------------------

For straightforward attribute lookups, use ``get_record_by_attribute``.

.. code-block:: python

   from nmdc_api_utilities.study_search import StudySearch

   client = StudySearch()

   partial = client.get_record_by_attribute(
       attribute_name="name",
       attribute_value="tropical soil",
   )

   exact = client.get_record_by_attribute(
       attribute_name="ecosystem_category",
       attribute_value="Plants",
       exact_match=True,
   )

Pagination and Performance
--------------------------

- Use ``max_page_size`` to tune result size for iterative exploration.
- Use ``all_pages=True`` only when full export is required.
- Use narrow filters and projection fields where possible.

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch

   client = BiosampleSearch()

   records = client.get_records(
       filter='{"ecosystem_category": "Plants"}',
       fields="id,name,lat_lon",
       max_page_size=50,
       all_pages=False,
   )

Troubleshooting
---------------

Filter returns no results:

- Confirm field names against schema documentation.
- Try regex + ``$options: i`` instead of strict equality.
- Confirm the selected collection class matches your target records.

JSON syntax errors:

- Use double quotes for keys and string values.
- Validate JSON structure before passing filter strings.

Special character issues:

- Prefer ``build_filter`` for automatic escaping.
- If writing raw regex filters, escape special characters carefully.

References
----------

- :doc:`usage`
- :doc:`functions`
- :doc:`public_subclasses`
- NMDC Schema docs: https://microbiomedata.github.io/nmdc-schema/
- NMDC API docs: https://api.microbiomedata.org/docs
- MongoDB query docs: https://www.mongodb.com/docs/manual/tutorial/query-documents/
