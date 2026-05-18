``CollectionSearch`` Subclasses
============================

Collection-specific subclasses are the recommended public entry points.
Each class inherits ``CollectionSearch`` behavior while preconfiguring a collection target.

Choosing a Subclass
-------------------

- Pick the subclass matching the record type you want to query.
- Use inherited methods such as ``get_record_by_id``, ``get_record_by_attribute``, ``get_record_by_filter``, and ``get_records``.
- See :doc:`filters` for query construction and operator examples.
- NMDC Schema reference: https://microbiomedata.github.io/nmdc-schema/
- Typecode-to-class map: https://microbiomedata.github.io/nmdc-schema/typecode-to-class-map/

Biosample and Study Related
---------------------------

These classes focus on study-level and site-level discovery.
Use them when starting from study metadata, biosamples, or collection events.

.. autoclass:: nmdc_client.biosample_search.BiosampleSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.study_search.StudySearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.collecting_biosamples_from_site_search.CollectingBiosamplesFromSiteSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.field_research_site_search.FieldResearchSiteSearch
   :members:
   :undoc-members:
   :show-inheritance:

Sample Processing Related
-------------------------

These classes target records produced through sample processing lifecycle, including processed sample entities and upstream material/storage processes.
Use NMDC Schema docs to confirm class semantics and filterable fields.

.. autoclass:: nmdc_client.processed_sample_search.ProcessedSampleSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.material_processing_search.MaterialProcessingSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.storage_process_search.StorageProcessSearch
   :members:
   :undoc-members:
   :show-inheritance:

Data Generation Related
-----------------------

These classes cover records tied to generation setup and instrumentation.
Use schema and typecode map when selecting classes for linked-instance queries.

.. autoclass:: nmdc_client.data_generation_search.DataGenerationSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.manifest_search.ManifestSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.instrument_search.InstrumentSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.configuration_search.ConfigurationSearch
   :members:
   :undoc-members:
   :show-inheritance:

Data and Processing Related
---------------------------

These classes are useful for workflow context, calibration context, data objects, and functional annotation aggregation outputs.
Use NMDC Schema docs for exact field meanings and schema class names.

.. autoclass:: nmdc_client.workflow_execution_search.WorkflowExecutionSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.calibration_search.CalibrationSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.data_object_search.DataObjectSearch
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: nmdc_client.functional_annotation_agg_search.FunctionalAnnotationAggSearch
   :members:
   :undoc-members:
   :show-inheritance:
