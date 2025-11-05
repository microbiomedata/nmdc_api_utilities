=====================================
Filtering and Querying NMDC Data
=====================================

This guide explains how to use filters to query the NMDC API using ``nmdc_api_utilities``, from simple CLI queries to advanced MongoDB filters.

Overview
========

The NMDC API supports MongoDB-style filtering to query biosamples, studies, data objects, and other collections. The ``nmdc_api_utilities`` package provides multiple ways to construct and use filters:

1. **CLI filter strings** - Simple command-line filtering
2. **Python filter dictionaries** - Programmatic filter construction
3. **MongoDB query syntax** - Advanced queries with regex, operators, and nested fields

Filter Formats
==============

MongoDB JSON Filters
--------------------

The NMDC API uses MongoDB query syntax. Filters are JSON objects that specify field criteria:

**Simple equality match:**

.. code-block:: json

   {"id": "nmdc:sty-11-8fb6t785"}

**Regex pattern matching (case-insensitive):**

.. code-block:: json

   {"name": {"$regex": "forest", "$options": "i"}}

**Multiple criteria (AND):**

.. code-block:: json

   {
     "ecosystem_category": "Plants",
     "geo_loc_name.has_raw_value": {"$regex": "Colorado"}
   }

**Checking field existence:**

.. code-block:: json

   {"lat_lon": {"$exists": true}}

**Nested field access (dot notation):**

.. code-block:: json

   {"env_broad_scale.has_raw_value": "Forest biome"}

MongoDB Operators
-----------------

Common MongoDB query operators supported:

* ``$regex`` - Pattern matching with regular expressions
* ``$options`` - Regex options (e.g., ``"i"`` for case-insensitive)
* ``$exists`` - Check if field exists
* ``$in`` - Match any value in array
* ``$gte`` / ``$lte`` - Greater/less than or equal (for numeric/date fields)
* ``$and`` / ``$or`` - Logical operators

For full MongoDB query syntax, see the `MongoDB Query Documentation <https://www.mongodb.com/docs/manual/tutorial/query-documents/>`_.

Using Filters in the CLI
=========================

The ``nmdc`` CLI accepts filter strings using the ``--filter`` option:

Simple ID Lookup
-----------------

.. code-block:: bash

   # Find a specific biosample by ID
   nmdc biosample --filter '{"id": "nmdc:bsm-11-006pnx90"}'

   # Find a specific study
   nmdc study --filter '{"id": "nmdc:sty-11-8fb6t785"}'

Regex Pattern Matching
-----------------------

.. code-block:: bash

   # Find biosamples with "forest" in name (case-insensitive)
   nmdc biosample --filter '{"name": {"$regex": "forest", "$options": "i"}}'

   # Search by ecosystem category
   nmdc biosample --filter '{"ecosystem_category": "Plants"}'

Field Existence
---------------

.. code-block:: bash

   # Find biosamples that have lat/lon coordinates
   nmdc biosample --filter '{"lat_lon": {"$exists": true}}' --limit 10

Nested Field Access
-------------------

.. code-block:: bash

   # Search nested fields using dot notation
   nmdc biosample --filter '{"env_broad_scale.has_raw_value": "Forest biome"}' --limit 5

   # Search studies by principal investigator
   nmdc study --filter '{"principal_investigator.has_raw_value": {"$regex": "Smith"}}'

Complex Queries
---------------

.. code-block:: bash

   # Multiple criteria - biosamples from a specific study in Colorado
   nmdc biosample --filter '{
     "part_of": "nmdc:sty-11-28tm5d36",
     "geo_loc_name.has_raw_value": {"$regex": "Colorado"}
   }'

   # Data objects of a specific type
   nmdc data-object --filter '{"data_object_type": "Metagenome Raw Reads"}' --limit 10

Saving Results
--------------

.. code-block:: bash

   # Save filtered results to JSON file
   nmdc biosample --filter '{"ecosystem_category": "Plants"}' --all -o plants.json

Using Filters in Python
========================

Direct Filter Strings
---------------------

Pass MongoDB filter strings directly to ``get_record_by_filter()``:

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch

   client = BiosampleSearch()

   # Simple ID filter
   results = client.get_record_by_filter('{"id": "nmdc:bsm-11-006pnx90"}')

   # Regex filter
   results = client.get_record_by_filter(
       '{"name": {"$regex": "forest", "$options": "i"}}'
   )

   # Multiple criteria
   filter_str = '{"ecosystem_category": "Plants", "lat_lon": {"$exists": true}}'
   results = client.get_record_by_filter(filter_str)

Building Filters Programmatically
----------------------------------

Use ``DataProcessing.build_filter()`` to construct filters from Python dictionaries:

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch
   from nmdc_api_utilities.data_processing import DataProcessing

   client = BiosampleSearch()
   dp = DataProcessing()

   # Simple filter (uses regex by default)
   filter_dict = {"name": "G6R2_NF_20JUN2016"}
   filter_str = dp.build_filter(filter_dict)
   results = client.get_record_by_filter(filter_str)

   # Multiple attributes
   filter_dict = {
       "name": "G6R2_NF_20JUN2016",
       "id": "nmdc:bsm-11-006pnx90"
   }
   filter_str = dp.build_filter(filter_dict)
   results = client.get_record_by_filter(filter_str)

   # Exact match (no regex)
   filter_str = dp.build_filter(
       {"ecosystem_category": "Plants"},
       exact_match=True
   )

How ``build_filter()`` Works
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, ``build_filter()`` creates case-insensitive regex filters:

.. code-block:: python

   # Input
   {"name": "forest"}

   # Output (internal)
   {"name": {"$regex": "forest", "$options": "i"}}

Special characters are automatically escaped for MongoDB:

.. code-block:: python

   # Input with special chars
   {"name": "GC-MS (2009)"}

   # Output (escaped)
   {"name": {"$regex": "GC\\-MS \\(2009\\)", "$options": "i"}}

Attribute-Based Search
----------------------

Use ``get_record_by_attribute()`` for simple attribute searches:

.. code-block:: python

   from nmdc_api_utilities.study_search import StudySearch

   client = StudySearch()

   # Regex search (default)
   results = client.get_record_by_attribute(
       attribute_name="name",
       attribute_value="tropical soil"
   )

   # Exact match
   results = client.get_record_by_attribute(
       attribute_name="ecosystem_category",
       attribute_value="Plants",
       exact_match=True
   )

Under the hood, this method:

1. Escapes special characters in the value
2. Wraps it in a MongoDB regex filter (unless ``exact_match=True``)
3. Calls ``get_records()`` with the constructed filter

Using ``get_records()`` Directly
---------------------------------

The most flexible approach is using ``get_records()`` with filter parameters:

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch

   client = BiosampleSearch()

   # Empty filter - get all records (paginated)
   all_biosamples = client.get_records(max_page_size=100)

   # With filter string
   filter_str = '{"ecosystem_category": "Plants"}'
   results = client.get_records(
       filter=filter_str,
       max_page_size=50,
       all_pages=False
   )

   # Get all pages
   all_results = client.get_records(
       filter='{"lat_lon": {"$exists": true}}',
       max_page_size=100,
       all_pages=True  # Fetches all pages automatically
   )

Filter Flow: CLI to API
========================

This section traces how filters flow through the system from CLI to API request.

CLI Input
---------

.. code-block:: bash

   nmdc biosample --filter '{"name": {"$regex": "forest", "$options": "i"}}' --limit 10

1. CLI Processing (cli.py)
---------------------------

The ``biosample`` command receives:

* ``filter`` = ``'{"name": {"$regex": "forest", "$options": "i"}}'``
* ``limit`` = ``10``

Calls:

.. code-block:: python

   client = BiosampleSearch(env=env)
   results = client.get_records(filter=filter, max_page_size=limit)

2. Filter Encoding (collection_search.py)
------------------------------------------

``get_records()`` URL-encodes the filter:

.. code-block:: python

   filter = urllib.parse.quote(filter)
   # '{"name": {"$regex": "forest", "$options": "i"}}'
   # becomes:
   # '%7B%22name%22%3A%7B%22%24regex%22%3A%22forest%22%2C%22%24options%22%3A%22i%22%7D%7D'

3. API Request Construction
----------------------------

Builds the final URL:

.. code-block:: python

   url = f"{self.base_url}/nmdcschema/{self.collection_name}?filter={filter}&max_page_size={max_page_size}&projection={fields}"

Example URL:

.. code-block:: text

   https://api.microbiomedata.org/nmdcschema/biosample_set?filter=%7B%22name%22%3A%7B%22%24regex%22%3A%22forest%22%2C%22%24options%22%3A%22i%22%7D%7D&max_page_size=10&projection=

4. HTTP GET Request
-------------------

Sends the GET request to NMDC API:

.. code-block:: python

   response = requests.get(url)
   response.raise_for_status()

5. Response Processing
----------------------

Extracts results from JSON response:

.. code-block:: python

   results = response.json()["resources"]

6. CLI Output
-------------

Displays results as formatted JSON or saves to file.

Advanced Filter Examples
=========================

Finding Related Records
-----------------------

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch
   from nmdc_api_utilities.study_search import StudySearch

   # Find a study
   study_client = StudySearch()
   study = study_client.get_record_by_id("nmdc:sty-11-28tm5d36")

   # Find all biosamples from that study
   biosample_client = BiosampleSearch()
   filter_str = '{"part_of": "nmdc:sty-11-28tm5d36"}'
   biosamples = biosample_client.get_record_by_filter(filter_str)

   print(f"Found {len(biosamples)} biosamples from study")

Geographic Filtering
--------------------

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch

   client = BiosampleSearch()

   # Find biosamples from Colorado
   colorado_samples = client.get_record_by_filter(
       '{"geo_loc_name.has_raw_value": {"$regex": "Colorado", "$options": "i"}}'
   )

   # Find samples with coordinates
   samples_with_coords = client.get_record_by_filter(
       '{"lat_lon": {"$exists": true}}'
   )

Data Object Type Filtering
---------------------------

.. code-block:: python

   from nmdc_api_utilities.data_object_search import DataObjectSearch

   client = DataObjectSearch()

   # Find FASTQ files
   fastq_files = client.get_record_by_filter(
       '{"data_object_type": "Metagenome Raw Reads"}'
   )

   # Find analysis results
   analysis_results = client.get_record_by_filter(
       '{"data_object_type": {"$regex": "Analysis Results"}}'
   )

Batch ID Checking
-----------------

.. code-block:: python

   from nmdc_api_utilities.collection_search import CollectionSearch

   client = CollectionSearch("biosample_set")

   # Check if multiple IDs exist
   ids = [
       "nmdc:bsm-11-002vgm56",
       "nmdc:bsm-11-006pnx90",
       "nmdc:bsm-11-00dkyf35"
   ]

   all_exist = client.check_ids_exist(ids)
   print(f"All IDs exist: {all_exist}")

Pagination and Performance
===========================

Single Page Queries
-------------------

Default behavior fetches one page:

.. code-block:: python

   client = BiosampleSearch()

   # Gets first 100 records only
   results = client.get_records(max_page_size=100)

Multi-Page Queries
------------------

Use ``all_pages=True`` to fetch everything:

.. code-block:: python

   # Fetches all matching records across all pages
   all_results = client.get_records(
       filter='{"ecosystem_category": "Plants"}',
       max_page_size=100,
       all_pages=True
   )

.. warning::

   Using ``all_pages=True`` can be slow for large result sets. The API will make multiple requests to fetch all pages.

Performance Tips
----------------

1. **Use specific filters** - Narrow your query to reduce result size
2. **Set appropriate page size** - Default is 100, max varies by endpoint
3. **Avoid all_pages for exploration** - Use for data export only
4. **Use field projection** - Request only needed fields (when supported)

.. code-block:: python

   # Request specific fields only
   results = client.get_records(
       filter='{"ecosystem_category": "Plants"}',
       fields="id,name,lat_lon",  # Comma-separated field names
       max_page_size=50
   )

Common Patterns
===============

Finding by Name (Partial Match)
--------------------------------

.. code-block:: python

   from nmdc_api_utilities.study_search import StudySearch

   client = StudySearch()
   results = client.get_record_by_attribute(
       "name",
       "tropical soil"  # Matches any study name containing this
   )

Finding by ID (Exact Match)
---------------------------

.. code-block:: python

   from nmdc_api_utilities.biosample_search import BiosampleSearch

   client = BiosampleSearch()

   # Method 1: Using get_record_by_id
   result = client.get_record_by_id("nmdc:bsm-11-006pnx90")

   # Method 2: Using filter
   results = client.get_record_by_filter(
       '{"id": "nmdc:bsm-11-006pnx90"}'
   )

Field Existence Checks
----------------------

.. code-block:: python

   # Has coordinates
   '{"lat_lon": {"$exists": true}}'

   # Missing specific field
   '{"some_field": {"$exists": false}}'

Case-Insensitive Search
-----------------------

.. code-block:: python

   # All these match "Forest", "forest", "FOREST", etc.
   '{"ecosystem_category": {"$regex": "forest", "$options": "i"}}'

Reference
=========

Available Collections
---------------------

Common NMDC collections you can query:

* ``biosample_set`` - Biosample records
* ``study_set`` - Study records
* ``data_object_set`` - Data objects (files)
* ``functional_annotation_agg`` - Functional annotation aggregations
* ``instrument_set`` - Instrument records

Field Names
-----------

Fields vary by collection. Refer to:

* `NMDC Schema Documentation <https://microbiomedata.github.io/nmdc-schema/>`_
* `API Interactive Docs <https://api.microbiomedata.org/docs>`_

Common fields:

* ``id`` - NMDC identifier
* ``name`` - Record name
* ``description`` - Description text
* ``type`` - Record type
* ``part_of`` - Parent relationship (studies, etc.)
* ``env_broad_scale`` - Environmental context
* ``ecosystem_category`` - Ecosystem classification
* ``geo_loc_name`` - Geographic location
* ``lat_lon`` - Coordinates

Environment Selection
---------------------

All classes support ``env`` parameter:

.. code-block:: python

   # Production API (default)
   client = BiosampleSearch(env="prod")

   # Development/testing API
   client = BiosampleSearch(env="dev")

CLI equivalent:

.. code-block:: bash

   # Production (default)
   nmdc biosample --filter '{"id": "nmdc:bsm-11-006pnx90"}'

   # Development
   nmdc biosample --filter '{"id": "nmdc:bsm-11-006pnx90"}' --env dev

Troubleshooting
===============

Filter Not Working
------------------

**Problem:** No results returned but you expect matches.

**Solutions:**

1. Check for typos in field names
2. Verify the field exists in the schema
3. Try case-insensitive regex instead of exact match
4. Check if the collection name is correct

.. code-block:: python

   # Instead of exact match
   '{"name": "Forest Sample"}'  # Might not match

   # Try regex
   '{"name": {"$regex": "Forest Sample", "$options": "i"}}'

JSON Syntax Errors
------------------

**Problem:** ``JSONDecodeError`` or filter parsing errors.

**Solutions:**

1. Use double quotes for JSON keys and string values
2. Escape special characters properly
3. Validate JSON with a linter

.. code-block:: python

   # Wrong - single quotes
   "{'name': 'sample'}"

   # Correct - double quotes
   '{"name": "sample"}'

Special Character Escaping
--------------------------

**Problem:** Filters with special characters fail.

**Solution:** Use ``build_filter()`` which auto-escapes:

.. code-block:: python

   from nmdc_api_utilities.data_processing import DataProcessing

   dp = DataProcessing()

   # Automatically escapes (, ), -, etc.
   filter_str = dp.build_filter({"name": "GC-MS (2009)"})

Or manually escape in JSON:

.. code-block:: python

   # Double backslash for MongoDB
   '{"name": {"$regex": "GC\\\\-MS \\\\(2009\\\\)"}}'

API Timeout
-----------

**Problem:** Request times out (524 error).

**Solutions:**

1. Make filter more specific to reduce result set
2. Use smaller page sizes
3. Check API status at https://api.microbiomedata.org/docs
4. Retry after brief wait

See Also
========

* :doc:`usage` - General usage guide
* :doc:`functions` - API reference
* `NMDC Schema <https://microbiomedata.github.io/nmdc-schema/>`_ - Field documentation
* `NMDC API Docs <https://api.microbiomedata.org/docs>`_ - Interactive API explorer
* `MongoDB Query Docs <https://www.mongodb.com/docs/manual/tutorial/query-documents/>`_ - Query syntax reference
