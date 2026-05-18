# nmdc-client

[![PyPI version](https://badge.fury.io/py/nmdc-client.svg)](https://pypi.org/project/nmdc-client/)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/microbiomedata/nmdc-client/actions/workflows/prod_tests.yml/badge.svg)](https://github.com/microbiomedata/nmdc-client/actions)

> **Renamed:** This package was previously published on PyPI as `nmdc-api-utilities`. The old name still installs (and pulls in `nmdc-client` automatically with a `DeprecationWarning`), but new development happens here. Please migrate your installs to `pip install nmdc-client` and your imports to `from nmdc_client import ...` at your earliest convenience.

A Python client for the [NMDC (National Microbiome Data Collaborative)](https://microbiomedata.org/) Runtime API. NMDC is a multi-institutional effort to enable findable, accessible, interoperable, and reusable (FAIR) microbiome data. This library provides Pythonic access to NMDC metadata so you can query, filter, and traverse linked records without writing raw API calls. For more information on the NMDC Runtime API itself, see the [API documentation](https://api.microbiomedata.org/docs).

## What you can do

- Search and retrieve metadata for studies, biosamples, data objects, workflow executions, and more
- Traverse linked records across collections (e.g. study → biosamples → data objects)
- Apply MongoDB-style filters to build precise queries
- Work with geospatial filters for applicable records (e.g. biosample collection locations)
- Access privileged submission and staging endpoints (authorized users only)

## Documentation

Full documentation is at [microbiomedata.github.io/nmdc-client](https://microbiomedata.github.io/nmdc-client/).

For additional real-world examples, the [nmdc_notebooks](https://github.com/microbiomedata/nmdc_notebooks) repository contains Jupyter notebooks that use this package end-to-end.

## Installation

```bash
pip install nmdc-client
```

To stay up to date with new releases:

```bash
pip install --upgrade nmdc-client
```

## Quick start

### Single record lookup

```python
from nmdc_client import BiosampleSearch

biosample_client = BiosampleSearch()
biosample_client.get_record_by_id(record_id="nmdc:bsm-13-amrnys72")
```

### Multi-step workflow: study → biosamples → data objects

A more realistic workflow starts from a study name and traverses linked records:

```python
from nmdc_client import StudySearch, DataObjectSearch

# Step 1: Find a study by name
study_client = StudySearch()
studies = study_client.get_record_by_attribute(
    attribute_name="name",
    attribute_value="Molecular mechanisms underlying changes in the temperature sensitive "
                    "respiration response of forest soils to long-term experimental warming",
    exact_match=True,
)

study_id = studies[0]["id"]  # e.g. "nmdc:sty-11-8ws97026"

# Step 2: Retrieve all biosamples linked to that study
biosamples = study_client.get_linked_instances(
    ids=[study_id],
    types=["nmdc:Biosample"],
    hydrate=True,
)
biosample_ids = [b["id"] for b in biosamples]

# Step 3: Retrieve data objects linked to those biosamples
data_object_client = DataObjectSearch()
data_objects = data_object_client.get_linked_instances(
    ids=biosample_ids,
    types=["nmdc:DataObject"],
    hydrate=True,
)
```

`get_linked_instances` is available on all search clients and accepts any list of NMDC IDs and target record types.

### Filtering with MongoDB-style operators

```python
from nmdc_client import BiosampleSearch

client = BiosampleSearch()

# Find biosamples from soil
results = client.get_record_by_filter(
    filter={
        "env_medium.has_raw_value": {"$regex": "soil"},
    }
)
```

See the [MongoDB filters guide](https://microbiomedata.github.io/nmdc-client/filters.html) for supported operators and more examples.

## Available search clients

All clients share a common interface (`get_record_by_id`, `get_record_by_attribute`, `get_record_by_filter`, `get_records`, `get_linked_instances`).

**Biosample & study**\
*for retrieving metadata about biosamples, studies, and collection sites*\
`BiosampleSearch`, `StudySearch`, `CollectingBiosamplesFromSiteSearch`, `FieldResearchSiteSearch`

**Sample processing**\
*for retrieving metadata about sample processing and storage*\
`ProcessedSampleSearch`, `MaterialProcessingSearch`, `StorageProcessSearch`

**Data generation**\
*for retrieving metadata about data generation processes, instruments, and configurations for sequencing and mass spectrometry*\
`DataGenerationSearch`, `ManifestSearch`, `InstrumentSearch`, `ConfigurationSearch`

**Data & workflow**\
*for retrieving metadata about workflows for processing raw data, data objects, and functional annotations*\
`WorkflowExecutionSearch`, `DataObjectSearch`, `CalibrationSearch`, `FunctionalAnnotationAggSearch`

See the [CollectionSearch subclasses reference](https://microbiomedata.github.io/nmdc-client/public_subclasses.html) for full detail on each class.

## Public vs. privileged API

Most users will only need the public search clients above. A separate privileged API is available for users with NMDC submission and staging permissions. See the [Privileged API reference](https://microbiomedata.github.io/nmdc-client/privileged_api.html) for details.

## Migrating from `nmdc-api-utilities`

If you were previously installing `nmdc-api-utilities`, both of the following will continue to work:

- `pip install nmdc-api-utilities` — installs the tombstone shim, which pulls in `nmdc-client` and emits a `DeprecationWarning`.
- `from nmdc_api_utilities import ...` and `from nmdc_api_utilities.<submodule> import ...` — still resolve, with a `DeprecationWarning`.

To migrate fully:

```bash
pip uninstall nmdc-api-utilities
pip install nmdc-client
```

Then replace `nmdc_api_utilities` with `nmdc_client` in your imports.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues, suggesting features, and submitting pull requests.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
