# nmdc_api_utilities
A library designed to simplify various research tasks for users looking to leverage the NMDC (National Microbiome Data Collaborative) APIs. The library provides a collection of general-purpose functions that facilitate easy access, manipulation, and analysis of microbiome data.

# Usage
Example use of the Biosample class:
```python
from nmdc_api_utilities.biosample_search import BiosampleSearch

# Create an instance of the module
biosample_client = BiosampleSearch()
# Use the variable to call the available functions
biosample_client.get_record_by_id(collection_id="nmdc:bsm-13-amrnys72")
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
To install, run:

```bash
python3 -m pip install nmdc_api_utilities
```

Peridodically run
```bash
python3 -m pip install --upgrade nmdc_api_utilities
```
to ensure you have the latest updates from this package.

# Documentation
Documentation about available functions and helpful usage notes can be found at https://microbiomedata.github.io/nmdc_api_utilities/.
