# -*- coding: utf-8 -*-
"""
This file contains (or will contain) two kinds of things:
(1) metadata about this package, itself; and
(2) things that we want to make it particularly convenient for package users to import.

Reference: https://realpython.com/python-init-py/#what-kind-of-code-should-i-put-in-__init__py
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Optional


def get_package_version(package_name: str) -> Optional[str]:
    """
    Returns the version identifier (e.g., "1.2.3") of the package having the specified name.

    Args:
        package_name: The name of the package

    Returns:
        The version identifier of the package, or `None` if package not found
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


# The version identifier of this package.
_version = get_package_version("nmdc_api_utilities")
__version__ = _version if _version is not None else "0.0.0"
