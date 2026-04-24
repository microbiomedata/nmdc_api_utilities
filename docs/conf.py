# -*- coding: utf-8 -*-
# Add these lines to conf.py
import os
import sys

sys.path.insert(0, os.path.abspath(".."))  # Path to your project root
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "nmdc_api_utilities"
copyright = "2024, Olivia Hess"
author = "Olivia Hess"
release = "2/1/2025"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # For Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx_autodoc_typehints",  # For automatically including type hints in the documentation
]

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
