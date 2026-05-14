# -*- coding: utf-8 -*-
# Add these lines to conf.py
import os
import sys

sys.path.insert(0, os.path.abspath(".."))  # Path to your project root

# Make the pandoc binary that `pypandoc-binary` installs into the venv discoverable on
# PATH so `nbsphinx` (which calls pandoc via subprocess, not pypandoc) can find it
# without a system-level install. Falls back silently to system pandoc if the package
# isn't installed.
try:
    import pypandoc

    _pandoc_dir = os.path.dirname(pypandoc.get_pandoc_path())
    os.environ["PATH"] = _pandoc_dir + os.pathsep + os.environ.get("PATH", "")
except (ImportError, OSError):
    pass
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "nmdc_api_utilities"
copyright = "2026, NMDC"
author = "NMDC"

from nmdc_api_utilities import __version__

release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # For Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "nbsphinx",  # Render Jupyter notebooks as documentation pages
    "sphinx_autodoc_typehints",  # For automatically including type hints in the documentation
]

# Execute notebook cells during docs builds so HTML includes cell output.
nbsphinx_execute = "always"
nbsphinx_timeout = 300

templates_path = ["_templates"]
exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]

# This setting adds the default values of function parameters to the documentation without needing to include them in the docstring.
typehints_defaults = "comma"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_js_files = [
    "external_links.js",
]
