# nmdc_api_utilities

A library designed to simplify various research tasks for users looking to leverage the NMDC (National Microbiome Data Collaborative) APIs. The library provides a collection of general-purpose functions that facilitate easy access, manipulation, and analysis of microbiome data.

## Features

- 🐍 **Python API**: Comprehensive Python library for NMDC API operations
- 🖥️ **Command-Line Interface**: Convenient `nmdc` CLI tool for common tasks
- 📦 **Lightweight**: Minimal core dependencies (pandas, requests)
- 🎨 **Optional extras**: Visualization support via matplotlib
- 🔐 **Authentication**: Built-in OAuth2 support for protected endpoints

# Usage

## Command-Line Interface

The `nmdc` command provides quick access to common NMDC API operations:

```bash
# Get help
nmdc --help

# Get a biosample by ID
nmdc biosample --id nmdc:bsm-13-amrnys72

# Search biosamples with a filter
nmdc biosample --filter 'env_broad_scale.has_raw_value:"Forest biome"' --limit 5

# Get all results and save to file
nmdc biosample --filter '{"lat_lon":{"$exists":true}}' --all -o biosamples.json

# Search studies
nmdc study --id nmdc:sty-11-34xj1150

# Get collection name for an ID
nmdc collection-name nmdc:bsm-13-amrnys72

# Search data objects
nmdc data-object --filter 'data_object_type:"Metagenome Raw Reads"' --limit 5

# Enable verbose logging (-v for INFO, -vv for DEBUG)
nmdc biosample --id nmdc:bsm-13-amrnys72 -v

# Validate metadata (requires authentication)
export CLIENT_ID="your_client_id"
export CLIENT_SECRET="your_client_secret"
nmdc validate metadata.json

# Mint new NMDC identifiers (requires authentication)
nmdc mint nmdc:Biosample
nmdc mint nmdc:DataObject --count 10
```

### Exporting Data (CSV/TSV/JSON)

The CLI automatically detects export format from file extension and intelligently flattens nested data:

```bash
# Export to JSON (default format)
nmdc biosample --filter 'ecosystem_category: Terrestrial' --limit 100 -o results.json

# Export to CSV with auto-flattened columns (100+ fields!)
nmdc biosample --filter 'ecosystem_category: Terrestrial' --limit 100 -o results.csv

# Export to TSV (tab-separated)
nmdc study --filter 'ecosystem_category: Aquatic' --all -o studies.tsv

# Works with all commands
nmdc data-object --filter 'data_object_type: QC Statistics' --limit 50 -o qc_data.csv
```

**Flattening Strategy:**
- **Nested objects:** `lat_lon.latitude`, `lat_lon.longitude`
- **Lists:** Concatenated with `|` (e.g., `metagenomics|metatranscriptomics`)
- **List aggregates:** Adds `_count` and `_ids` columns (e.g., `associated_studies_count`)

**Use Cases:**
- Import into Excel/Google Sheets for quick analysis
- Load into pandas: `pd.read_csv('results.csv')`
- Import into DuckDB: `CREATE TABLE data AS SELECT * FROM 'results.csv'`
- Compatible with R, Julia, and any data analysis tool

### Debugging with Verbose Mode

The CLI supports multiple verbosity levels using the `-v` flag:

```bash
# No verbosity (default) - quiet output, only results
nmdc biosample --id nmdc:bsm-13-amrnys72

# -v (INFO level) - Show API URLs and timing
nmdc biosample --filter '{"lat_lon":{"$exists":true}}' --limit 3 -v

# -vv (DEBUG level) - Show detailed request/response info
nmdc biosample --filter '{"lat_lon":{"$exists":true}}' --limit 3 -vv

# -vvv (DEBUG level) - Show all library-level details
nmdc biosample --filter '{"lat_lon":{"$exists":true}}' --limit 3 -vvv
```

**What each level shows:**

| Level | Flag | Shows |
|-------|------|-------|
| WARNING (default) | (none) | Only results and errors |
| INFO | `-v` | API URLs and timing (e.g., "completed in 0.12s") |
| DEBUG | `-vv` or `-vvv` | Full request details, URL encoding, HTTP connections, response data |

**Example output with `-v`:**
```
[08:11:05] INFO  Making API request to: https://api.microbiomedata.org/...
           INFO  API request completed in 0.11s (status: 200)
```

**Example output with `-vv`:**
```
[08:11:05] DEBUG get_records Filter: {"lat_lon":{"$exists":true}}
           DEBUG get_records encoded Filter: %7B%22lat_lon%22%3A%7B...
           INFO  Making API request to: https://api.microbiomedata.org/...
           DEBUG Starting new HTTPS connection (1): api.microbiomedata.org:443
           DEBUG https://api.microbiomedata.org:443 "GET /nmdcschema/..." 200
           INFO  API request completed in 0.22s (status: 200)
           DEBUG API request response: {'resources': [...]}
```

**Use cases:**
- `-v` for diagnosing slow queries and monitoring performance
- `-vv` for debugging filter syntax issues and understanding encoding
- Use verbosity when reporting API issues to support

### Searching by Functional Annotations

**NEW**: Search for biosamples containing specific functional annotations (PFAM, KEGG, COG, GO):

```bash
# Find biosamples with a specific PFAM domain
nmdc search-by-function PF00005 --limit 10

# Find biosamples with BOTH PFAMs (AND logic)
nmdc search-by-function PF00005 PF00072 --require-all

# Find biosamples with EITHER PFAM (OR logic)
nmdc search-by-function PF00005 PF00072 --any

# Mix different annotation types
nmdc search-by-function PFAM:PF00005 KEGG.ORTHOLOGY:K00001

# Show omics processing activities
nmdc search-by-function PF00005 --show-activities

# Save results to JSON/CSV
nmdc search-by-function PF00005 PF00072 -o results.json
nmdc search-by-function PF00005 --any -o results.csv
```

**Supported Function Types:**
- **PFAM domains**: `PF00005` or `PFAM:PF00005`
- **KEGG Orthology**: `K00001` or `KEGG.ORTHOLOGY:K00001`
- **COG**: `COG0001` or `COG:COG0001`
- **Gene Ontology**: `GO0000001` or `GO:GO0000001`

**How it works:**
This uses a specialized NMDC endpoint (`data.microbiomedata.org/api/biosample/search`) that can directly search biosamples by their functional annotations. Unlike the standard API, this endpoint returns complete biosample records with omics processing data and associated data objects.

### Building Local Data Mirrors with DuckDB

Exported CSV/TSV files can be imported into DuckDB for fast local queries:

```bash
# 1. Export NMDC data
nmdc biosample --filter 'ecosystem_type: Soil' --all -o soil_samples.csv
nmdc study --all -o studies.csv

# 2. Import into DuckDB
duckdb nmdc_local.db <<EOF
CREATE TABLE biosamples AS SELECT * FROM 'soil_samples.csv';
CREATE TABLE studies AS SELECT * FROM 'studies.csv';
EOF

# 3. Run fast analytical queries locally
duckdb nmdc_local.db <<EOF
SELECT
  ecosystem_subtype,
  COUNT(*) as sample_count,
  AVG(CAST(depth_has_maximum_numeric_value AS FLOAT)) as avg_depth
FROM biosamples
WHERE depth_has_maximum_numeric_value != ''
GROUP BY ecosystem_subtype
ORDER BY sample_count DESC;
EOF
```

**Benefits:**
- No API rate limits - query millions of records instantly
- Complex SQL joins across collections
- Offline analysis capability
- Perfect for reproducible research

See [DUCKDB_STRATEGY.md](DUCKDB_STRATEGY.md) for future integration plans.
```

## Python API Examples

### Searching Biosamples

```python
from nmdc_api_utilities.biosample_search import BiosampleSearch

# Create an instance of the biosample search client
biosample_client = BiosampleSearch()

# Get a single biosample by ID
biosample = biosample_client.get_record_by_id(collection_id="nmdc:bsm-13-amrnys72")
print(biosample)

# Search for biosamples with filters
# Get first page of results (default max 100 records)
results = biosample_client.get_records(filter='env_broad_scale.has_raw_value:"Forest biome"')

# Get ALL pages of results
all_forest_biosamples = biosample_client.get_records(
    filter='env_broad_scale.has_raw_value:"Forest biome"',
    all_pages=True
)

# Limit returned fields for efficiency
results = biosample_client.get_records(
    filter='env_broad_scale.has_raw_value:"Forest biome"',
    fields="id,name,lat_lon",
    max_page_size=50
)
```

### Searching Studies

```python
from nmdc_api_utilities.study_search import StudySearch

study_client = StudySearch()

# Get a specific study
study = study_client.get_record_by_id(collection_id="nmdc:sty-11-34xj1150")

# Search for studies by principal investigator
studies = study_client.get_records(
    filter='principal_investigator.has_raw_value:"Smith"',
    all_pages=True
)
```

### Working with Data Objects

```python
from nmdc_api_utilities.data_object_search import DataObjectSearch

data_client = DataObjectSearch()

# Search for specific file types
fastq_files = data_client.get_records(
    filter='data_object_type:"Metagenome Raw Reads"',
    max_page_size=100
)
```

### Searching by Functional Annotations

**NEW**: Search biosamples by functional annotations (PFAM, KEGG, COG, GO):

```python
from nmdc_api_utilities.functional_biosample_search import FunctionalBiosampleSearch

# Create a functional search client
func_client = FunctionalBiosampleSearch()

# Search by PFAM domain (auto-detects prefix)
results = func_client.search_by_pfam(["PF00005"], limit=10)
print(f"Found {results['count']} biosamples")

# Search with multiple PFAMs (AND logic - all must be present)
results = func_client.search_by_pfam(
    ["PF00005", "PF00072"],
    require_all=True,  # AND logic (default)
    limit=20
)

# Search with OR logic (any PFAM can be present)
results = func_client.search_by_pfam(
    ["PF00005", "PF00072"],
    require_all=False,  # OR logic
    limit=50
)

# Search by KEGG Orthology
results = func_client.search_by_kegg(["K00001"], limit=10)

# Search by COG
results = func_client.search_by_cog(["COG0001"], limit=10)

# Search by Gene Ontology
results = func_client.search_by_go(["GO0000001"], limit=10)

# Mix different annotation types
results = func_client.search_by_functions(
    ["PFAM:PF00005", "KEGG.ORTHOLOGY:K00001"],
    limit=10,
    logic="AND"  # or "OR"
)

# Access results
for biosample in results["results"]:
    print(f"Biosample: {biosample['id']}")
    print(f"Study: {biosample.get('study_id', 'N/A')}")

    # Access omics processing data
    for omics in biosample.get("omics_processing", []):
        for omics_data in omics.get("omics_data", []):
            print(f"  Activity: {omics_data.get('type')}")
            print(f"  Outputs: {len(omics_data.get('outputs', []))} files")
```

### Metadata Validation and Submission (Requires Authentication)

```python
from nmdc_api_utilities.metadata import Metadata
from nmdc_api_utilities.auth import NMDCAuth

# Set up authentication
auth = NMDCAuth(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Create metadata client
metadata_client = Metadata(env="prod", auth=auth)

# Validate JSON records
records = [
    {
        "id": "nmdc:bsm-example-001",
        "name": "Example Biosample",
        # ... other fields
    }
]
status = metadata_client.validate_json(records)
print(f"Validation status: {status}")

# Or validate from a file
status = metadata_client.validate_json("path/to/metadata.json")

# Submit validated metadata
response = metadata_client.submit_json(records)
```

### Minting New NMDC Identifiers (Requires Authentication)

```python
from nmdc_api_utilities.minter import Minter
from nmdc_api_utilities.auth import NMDCAuth

# Set up authentication
auth = NMDCAuth(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Create minter client
minter = Minter(env="prod", auth=auth)

# Mint a single ID
new_id = minter.mint(nmdc_type="nmdc:Biosample")
print(f"New biosample ID: {new_id}")

# Mint multiple IDs at once
new_ids = minter.mint(nmdc_type="nmdc:DataObject", count=10)
print(f"Created {len(new_ids)} new data object IDs")
```

### Using Different Environments

```python
from nmdc_api_utilities.biosample_search import BiosampleSearch

# Use production API (default)
prod_client = BiosampleSearch(env="prod")

# Use development API for testing
dev_client = BiosampleSearch(env="dev")
```

For real use case examples, see the [nmdc_notebooks](https://github.com/microbiomedata/nmdc_notebooks) repository. Each of the Python Jupyter notebooks use this package.

## Logging - Debug Mode
To see debugging information, include these two lines where ever you are running the functions:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# when this is run, you will see debug information in the console.
biosample_client.get_record_by_id(collection_id="nmdc:bsm-13-amrnys72")
```

# Installation

## For Users

To install the latest stable version:

```bash
pip install nmdc_api_utilities
```

To upgrade to the latest version:
```bash
pip install --upgrade nmdc_api_utilities
```

If you need visualization features (matplotlib):
```bash
pip install nmdc_api_utilities[viz]
```

## For Development

This project uses `uv` for dependency management. To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/microbiomedata/nmdc_api_utilities.git
cd nmdc_api_utilities

# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Or activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate   # On Windows
pytest
```

# Documentation
Documentation about available functions and helpful usage notes can be found at https://microbiomedata.github.io/nmdc_api_utilities/.
