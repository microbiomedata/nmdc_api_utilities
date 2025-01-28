# nmdc_notebook_tools
A library designed to simplify various research tasks for users looking to leverage the NMDC (National Microbiome Data Collaborative) APIs. The library provides a collection of general-purpose functions that facilitate easy access, manipulation, and analysis of microbiome data.

# Usage
Example use of the Biosample class:
```python
from nmdc_notebook_tools.biosample_search import BiosampleSearch

# Create an instance of the module
biosample_client = BiosampleSearch()
# Use the variable to call the available functions
biosample_client.get_collection_by_id("biosample", "id")
```

## Logging - Debug Mode
To see debugging information, include these two lines where ever you are running the functions:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# when this is run, you will see debug information in the console.
biosample_client.get_collection_by_id("biosample", "id")
```

# Installation
To install, run:

```bash
python3 -m pip install nmdc_notebook_tool
```

Peridodically run
```bash
python3 -m pip install --upgrade nmdc_notebook_tools
```
to ensure you have the latest updates from this package.

# Documentation
Documentation about available functions and helpful usage notes can be found at https://microbiomedata.github.io/nmdc_notebook_tools/.
