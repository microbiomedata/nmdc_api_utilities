# nmdc_api_utilities

[![PyPI version](https://badge.fury.io/py/nmdc-api-utilities.svg)](https://pypi.org/project/nmdc_api_utilities/)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![CI](https://github.com/microbiomedata/nmdc_api_utilities/actions/workflows/python-package.yml/badge.svg)](https://github.com/microbiomedata/nmdc_api_utilities/actions)

A Python client for the [NMDC (National Microbiome Data Collaborative)](https://microbiomedata.org/) Runtime API. NMDC is a multi-institutional effort to enable findable, accessible, interoperable, and reusable (FAIR) microbiome data. This library provides Pythonic access to NMDC metadata so you can query, filter, and traverse linked records without writing raw API calls.

## What you can do

- Search and retrieve metadata for studies, biosamples, data objects, workflow executions, and more
- Traverse linked records across collections (e.g. study → biosamples → data objects)
- Apply MongoDB-style filters to build precise queries
- Work with geospatial filters on biosample collection sites
- Access privileged submission and staging endpoints (authorized users only)
- Enable debug logging to inspect requests and responses

## Documentation

Full documentation is at [microbiomedata.github.io/nmdc_api_utilities](https://microbiomedata.github.io/nmdc_api_utilities/).

For additional real-world examples, the [nmdc_notebooks](https://github.com/microbiomedata/nmdc_notebooks) repository contains Jupyter notebooks that use this package end-to-end.

## Installation

```bash
pip install nmdc_api_utilities
```

To stay up to date with new releases:

```bash
pip install --upgrade nmdc_api_utilities
```

## Quick start

### Single record lookup

```python
from nmdc_api_utilities import BiosampleSearch

biosample_client = BiosampleSearch()
biosample_client.get_record_by_id(collection_id="nmdc:bsm-13-amrnys72")
```

### Multi-step workflow: study → biosamples → data objects

A more realistic workflow starts from a study name and traverses linked records:

```python
from nmdc_api_utilities import StudySearch, DataObjectSearch

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
from nmdc_api_utilities import BiosampleSearch

client = BiosampleSearch()

# Find biosamples from soil collected at a depth between 0 and 0.1 m
results = client.get_record_by_filter(
    filter={
        "env_medium.has_raw_value": {"$regex": "soil"},
        "depth.has_minimum_numeric_value": {"$gte": 0},
        "depth.has_maximum_numeric_value": {"$lte": 0.1},
    }
)
```

See the [MongoDB filters guide](https://microbiomedata.github.io/nmdc_api_utilities/filters.html) for supported operators and more examples.

## Available search clients

All clients share a common interface (`get_record_by_id`, `get_record_by_attribute`, `get_record_by_filter`, `get_records`, `get_linked_instances`).

**Biosample & study**
These clients are for searching core metadata about biosamples, studies, and collection sites:
`BiosampleSearch`, `StudySearch`, `CollectingBiosamplesFromSiteSearch`, `FieldResearchSiteSearch`

**Sample processing**
These clients are for searching metadata about sample processing and storage:
`ProcessedSampleSearch`, `MaterialProcessingSearch`, `StorageProcessSearch`

**Data generation**
These clients are for searching metadata about data generation processes, instruments, and configurations for sequencing and mass spectrometry:
`DataGenerationSearch`, `ManifestSearch`, `InstrumentSearch`, `ConfigurationSearch`

**Data & workflow**
These clients are for searching metadata about workflows for processing raw data, data objects, and functional annotations:
`WorkflowExecutionSearch`, `DataObjectSearch`, `CalibrationSearch`, `FunctionalAnnotationAggSearch`

See the [CollectionSearch subclasses reference](https://microbiomedata.github.io/nmdc_api_utilities/public_subclasses.html) for full detail on each class.

## Public vs. privileged API

Most users will only need the public search clients above. A separate privileged API is available for users with NMDC submission and staging permissions. See the [Privileged API reference](https://microbiomedata.github.io/nmdc_api_utilities/privileged_api.html) for details.


## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues, suggesting features, and submitting pull requests.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
