# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import requests
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging
import json
import yaml

logger = logging.getLogger(__name__)


def parse_filter(filter_str: str) -> str:
    """
    Parse a filter string that can be in JSON or YAML format and return valid JSON string.

    This function accepts multiple input formats for convenience:
    - JSON: '{"id": "nmdc:sty-11-8fb6t785"}'
    - YAML simple: 'id: nmdc:sty-11-8fb6t785'
    - YAML complex: 'ecosystem_category: Plants'

    Parameters
    ----------
    filter_str: str
        Filter in JSON or YAML format

    Returns
    -------
    str
        Valid JSON string suitable for NMDC API

    Raises
    ------
    ValueError
        If the filter cannot be parsed as valid JSON or YAML

    Examples
    --------
    >>> from nmdc_api_utilities.utils import parse_filter
    >>> # JSON input
    >>> parse_filter('{"id": "nmdc:sty-11-8fb6t785"}')
    '{"id": "nmdc:sty-11-8fb6t785"}'

    >>> # YAML simple input
    >>> import json
    >>> result = parse_filter('ecosystem_category: Plants')
    >>> json.loads(result)
    {'ecosystem_category': 'Plants'}

    >>> # YAML with nested fields
    >>> result = parse_filter('env_broad_scale.has_raw_value: Forest biome')
    >>> json.loads(result)
    {'env_broad_scale.has_raw_value': 'Forest biome'}
    """
    if not filter_str or not filter_str.strip():
        return ""

    filter_str = filter_str.strip()

    # If it looks like JSON (starts with {), try JSON first
    if filter_str.startswith('{'):
        try:
            # Validate it's proper JSON
            parsed = json.loads(filter_str)
            return json.dumps(parsed)  # Return normalized JSON
        except json.JSONDecodeError:
            # Fall through to try YAML
            pass

    # Try parsing as YAML (which also handles JSON as a subset)
    try:
        parsed = yaml.safe_load(filter_str)

        # YAML can parse simple strings as strings, not dicts
        if not isinstance(parsed, dict):
            raise ValueError(
                f"Filter must be a key-value mapping, got: {type(parsed).__name__}"
            )

        return json.dumps(parsed)

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid filter syntax: {e}")


class Utils:
    def __init__(self):
        pass
