# -*- coding: utf-8 -*-
"""
Utilities for exporting NMDC data to flat formats (CSV, TSV).

Handles intelligent flattening of nested JSON structures:
- Simple dicts: "lat_lon.latitude" or "lat_lon_latitude"
- Lists: concatenate with '|'
- Nested structures: recursive flattening with dot notation
"""
import csv
import json
from typing import Any, Dict, List, Union
from pathlib import Path


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary using dot notation.

    Args:
        data: Dictionary to flatten
        parent_key: Key prefix for nested keys
        sep: Separator between nested keys (default: '.')

    Returns:
        Flattened dictionary

    Examples:
        >>> flatten_dict({'a': 1, 'b': {'c': 2, 'd': 3}})
        {'a': 1, 'b.c': 2, 'b.d': 3}

        >>> flatten_dict({'lat_lon': {'latitude': 63.875, 'longitude': -149.210, 'type': 'nmdc:GeolocationValue'}})
        {'lat_lon.latitude': 63.875, 'lat_lon.longitude': -149.210, 'lat_lon.type': 'nmdc:GeolocationValue'}
    """
    items = []

    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            # Skip 'type' fields from NMDC schema objects as they're often redundant
            if 'type' in v and v['type'].startswith('nmdc:'):
                # Extract useful fields from typed objects
                useful_fields = {key: val for key, val in v.items() if key != 'type' or len(v) == 1}
                if len(useful_fields) == 0:
                    items.append((new_key, v['type']))
                elif len(useful_fields) == 1 and 'type' not in useful_fields:
                    # Single field object, flatten directly
                    items.extend(flatten_dict(useful_fields, new_key, sep=sep).items())
                else:
                    # Multiple fields, recurse
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Handle lists by concatenating with '|'
            if len(v) == 0:
                items.append((new_key, ''))
            elif all(isinstance(item, (str, int, float, bool)) or item is None for item in v):
                # Simple list of primitives
                items.append((new_key, '|'.join(str(item) for item in v if item is not None)))
            elif all(isinstance(item, dict) for item in v):
                # List of dicts - for now, just count them and extract IDs if present
                ids = [item.get('id', item.get('name', str(i))) for i, item in enumerate(v)]
                items.append((f"{new_key}_count", len(v)))
                items.append((f"{new_key}_ids", '|'.join(ids)))
            else:
                # Mixed list, convert to JSON string
                items.append((new_key, json.dumps(v)))
        elif v is None:
            items.append((new_key, ''))
        else:
            items.append((new_key, v))

    return dict(items)


def flatten_records(records: List[Dict[str, Any]], sep: str = '.') -> List[Dict[str, Any]]:
    """
    Flatten a list of records.

    Args:
        records: List of dictionaries to flatten
        sep: Separator for nested keys

    Returns:
        List of flattened dictionaries
    """
    return [flatten_dict(record, sep=sep) for record in records]


def export_to_csv(
    records: List[Dict[str, Any]],
    output_path: Union[str, Path],
    delimiter: str = ',',
    flatten: bool = True,
    sep: str = '.'
) -> None:
    """
    Export records to CSV or TSV format.

    Args:
        records: List of record dictionaries
        output_path: Path to output file
        delimiter: Field delimiter (',' for CSV, '\\t' for TSV)
        flatten: Whether to flatten nested structures
        sep: Separator for nested keys when flattening

    Examples:
        >>> records = [{'id': 'nmdc:123', 'lat_lon': {'latitude': 63.875, 'longitude': -149.210}}]
        >>> export_to_csv(records, 'output.csv')  # Creates flattened CSV
        >>> export_to_csv(records, 'output.tsv', delimiter='\\t')  # Creates TSV
    """
    if not records:
        # Create empty file
        Path(output_path).touch()
        return

    # Flatten if requested
    if flatten:
        flattened = flatten_records(records, sep=sep)
    else:
        flattened = records

    # Get all unique keys across all records (for comprehensive headers)
    all_keys = set()
    for record in flattened:
        all_keys.update(record.keys())

    # Sort keys for consistent column order (id first if present)
    sorted_keys = sorted(all_keys)
    if 'id' in sorted_keys:
        sorted_keys.remove('id')
        sorted_keys.insert(0, 'id')

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted_keys, delimiter=delimiter, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(flattened)


def get_export_format(output_path: Union[str, Path]) -> str:
    """
    Determine export format from file extension.

    Args:
        output_path: Path to output file

    Returns:
        Format string: 'csv', 'tsv', or 'json'

    Examples:
        >>> get_export_format('data.csv')
        'csv'
        >>> get_export_format('data.tsv')
        'tsv'
        >>> get_export_format('data.json')
        'json'
    """
    suffix = Path(output_path).suffix.lower()
    if suffix == '.csv':
        return 'csv'
    elif suffix in ('.tsv', '.tab'):
        return 'tsv'
    elif suffix == '.json':
        return 'json'
    else:
        # Default to CSV
        return 'csv'


def export_records(
    records: List[Dict[str, Any]],
    output_path: Union[str, Path],
    format: str = 'auto',
    flatten: bool = True
) -> str:
    """
    Export records to specified format (auto-detected from extension).

    Args:
        records: List of record dictionaries
        output_path: Path to output file
        format: Output format ('csv', 'tsv', 'json', or 'auto')
        flatten: Whether to flatten nested structures (for CSV/TSV)

    Returns:
        Format used for export

    Examples:
        >>> records = [{'id': 'nmdc:123', 'name': 'Sample 1'}]
        >>> export_records(records, 'data.csv')  # Auto-detects CSV
        'csv'
        >>> export_records(records, 'data.tsv')  # Auto-detects TSV
        'tsv'
    """
    if format == 'auto':
        format = get_export_format(output_path)

    if format == 'csv':
        export_to_csv(records, output_path, delimiter=',', flatten=flatten)
    elif format == 'tsv':
        export_to_csv(records, output_path, delimiter='\t', flatten=flatten)
    elif format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")

    return format
