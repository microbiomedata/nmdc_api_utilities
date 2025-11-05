# -*- coding: utf-8 -*-
"""
Aggregation utilities for rolling up measurements from biosamples to studies.

This module provides functions for extracting numeric values from different
NMDC data formats and aggregating them into summary statistics.
"""

from typing import Union, Optional, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# Fields to EXCLUDE from property rollup
# Using exclusion list approach - aggregate everything EXCEPT these
EXCLUDED_FIELDS = {
    # Core metadata
    'id', 'type', 'name', 'description', '_downstream_of',
    # Already handled separately
    'lat_lon',  # Handled in geolocation_rollup
    # Ecosystem classification (handled in categorical_rollup)
    'ecosystem', 'ecosystem_category', 'ecosystem_type', 'ecosystem_subtype',
    'specific_ecosystem', 'habitat', 'location', 'community',
    # Taxonomy and sample naming
    'ncbi_taxonomy_name', 'sample_collection_site', 'samp_name',
    # Controlled term objects (not measurements)
    'env_broad_scale', 'env_local_scale', 'env_medium', 'geo_loc_name',
    'env_package', 'soil_horizon', 'samp_collec_device',
    # Identifier lists
    'associated_studies', 'gold_biosample_identifiers', 'emsl_biosample_identifiers',
    'insdc_biosample_identifiers', 'alternative_identifiers', 'img_identifiers',
    # Dates (handled as timestamps, not measurements)
    'collection_date', 'add_date', 'mod_date',
    # Categorical/list fields
    'biosample_categories', 'analysis_type',
    # Other non-measurement fields
    'has_credit_associations',
}

# Categorical fields to aggregate with counts
CATEGORICAL_FIELDS = {
    'ecosystem',
    'ecosystem_category',
    'ecosystem_type',
    'ecosystem_subtype',
    'specific_ecosystem',
}

# Unit normalization mapping - converts unit symbols to readable suffixes
UNIT_NORMALIZATION = {
    '%': 'percent',
    '°C': 'celsius',
    '℃': 'celsius',
    'Cel': 'celsius',
    '°F': 'fahrenheit',
    '℉': 'fahrenheit',
    'm': 'meters',
    'cm': 'centimeters',
    'mm': 'millimeters',
    'km': 'kilometers',
    'g': 'grams',
    'kg': 'kilograms',
    'mg': 'milligrams',
    'µg': 'micrograms',
    'L': 'liters',
    'mL': 'milliliters',
    'µL': 'microliters',
    'M': 'molar',
    'mM': 'millimolar',
    'µM': 'micromolar',
    'pH': 'pH',
    'ppm': 'ppm',
    'ppb': 'ppb',
}


def normalize_unit_for_key(unit: str) -> str:
    """
    Normalize a unit string to a readable key suffix.

    Uses UNIT_NORMALIZATION mapping for common units, otherwise sanitizes
    special characters to underscores.

    Parameters
    ----------
    unit : str
        The unit string to normalize

    Returns
    -------
    str
        Normalized unit string suitable for use as a dictionary key suffix

    Examples
    --------
    >>> normalize_unit_for_key('%')
    'percent'

    >>> normalize_unit_for_key('Cel')
    'celsius'

    >>> normalize_unit_for_key('mg/kg')
    'mg_kg'

    >>> normalize_unit_for_key('°C')
    'celsius'
    """
    # Check if we have a predefined normalization
    if unit in UNIT_NORMALIZATION:
        return UNIT_NORMALIZATION[unit]

    # Otherwise sanitize by replacing special chars with underscore
    import re
    return re.sub(r'[^\w]', '_', str(unit)).strip('_')


def extract_numeric_value(field_value: Any) -> tuple[Optional[float], Optional[str]]:
    """
    Extract numeric value and unit from different NMDC data formats.

    Handles three formats:
    1. Scalar numeric: 6.04
    2. QuantityValue object: {"has_numeric_value": 6.6, "has_unit": "Cel"}
    3. Range values: {"has_minimum_numeric_value": 0, "has_maximum_numeric_value": 0.5}

    Parameters
    ----------
    field_value : Any
        The field value from a biosample record

    Returns
    -------
    tuple[Optional[float], Optional[str]]
        (numeric_value, unit) where unit is None if not specified.
        Returns (None, None) if value cannot be extracted.

    Examples
    --------
    >>> extract_numeric_value(6.04)
    (6.04, None)

    >>> extract_numeric_value({"has_numeric_value": 6.6, "has_unit": "Cel"})
    (6.6, 'Cel')

    >>> extract_numeric_value({"has_minimum_numeric_value": 0, "has_maximum_numeric_value": 0.5, "has_unit": "m"})
    (0.25, 'm')

    >>> extract_numeric_value("not a number")
    (None, None)
    """
    # Handle scalar numeric values
    if isinstance(field_value, (int, float)):
        return float(field_value), None

    # Handle QuantityValue objects
    if isinstance(field_value, dict):
        # Standard QuantityValue with single value
        if 'has_numeric_value' in field_value:
            value = field_value['has_numeric_value']
            unit = field_value.get('has_unit')
            if isinstance(value, (int, float)):
                return float(value), unit

        # Range value - use midpoint
        if 'has_minimum_numeric_value' in field_value and 'has_maximum_numeric_value' in field_value:
            min_val = field_value['has_minimum_numeric_value']
            max_val = field_value['has_maximum_numeric_value']
            unit = field_value.get('has_unit')
            if isinstance(min_val, (int, float)) and isinstance(max_val, (int, float)):
                midpoint = (float(min_val) + float(max_val)) / 2
                return midpoint, unit

    # Handle list values - extract from first element if it's a QuantityValue
    if isinstance(field_value, list) and len(field_value) > 0:
        # Try to parse string values like "2.667 g of water/g of dry soil"
        if isinstance(field_value[0], str):
            # Try to extract leading numeric value
            import re
            match = re.match(r'^([\d.]+)', field_value[0].strip())
            if match:
                try:
                    value = float(match.group(1))
                    # Try to extract unit (text after the number)
                    unit_match = re.search(r'^[\d.]+\s+(.+)$', field_value[0].strip())
                    unit = unit_match.group(1) if unit_match else None
                    return value, unit
                except ValueError:
                    pass

    return None, None


def calculate_stats(values: list[float]) -> dict[str, float]:
    """
    Calculate min, max, and mean for a list of values.

    Parameters
    ----------
    values : list[float]
        List of numeric values

    Returns
    -------
    dict[str, float]
        Dictionary with 'min', 'max', and 'mean' keys

    Examples
    --------
    >>> stats = calculate_stats([5.2, 6.4, 7.1, 5.8, 6.9])
    >>> stats['min']
    5.2
    >>> stats['max']
    7.1
    >>> abs(stats['mean'] - 6.28) < 0.01
    True
    """
    if not values:
        return {'min': None, 'max': None, 'mean': None}

    return {
        'min': min(values),
        'max': max(values),
        'mean': sum(values) / len(values)
    }


def aggregate_field(biosamples: list[dict], field_name: str) -> dict[str, dict]:
    """
    Calculate min, max, mean for a field across biosamples.

    Handles cases where the same field may have different units across samples.
    If units differ, creates separate aggregations keyed by field_name + normalized_unit.

    Parameters
    ----------
    biosamples : list[dict]
        List of biosample records
    field_name : str
        Name of the field to aggregate

    Returns
    -------
    dict[str, dict]
        Dictionary mapping field key to statistics.
        Field key is field_name (if no unit) or field_name_normalized_unit (if unit specified).
        Units are normalized using UNIT_NORMALIZATION (e.g., '%' -> 'percent', 'Cel' -> 'celsius').
        Each value contains 'min', 'max', 'mean', 'count', 'unit'.

    Examples
    --------
    >>> samples = [
    ...     {"ph": 6.04},
    ...     {"ph": 7.2},
    ...     {"ph": 5.8}
    ... ]
    >>> result = aggregate_field(samples, "ph")
    >>> result['ph']['min']
    5.8
    >>> result['ph']['max']
    7.2
    >>> result['ph']['count']
    3

    >>> samples_with_units = [
    ...     {"nitrogen": {"has_numeric_value": 0.5, "has_unit": "%"}},
    ...     {"nitrogen": {"has_numeric_value": 0.6, "has_unit": "%"}}
    ... ]
    >>> result = aggregate_field(samples_with_units, "nitrogen")
    >>> 'nitrogen_percent' in result
    True
    >>> result['nitrogen_percent']['unit']
    '%'
    """
    values_by_unit = defaultdict(list)

    for sample in biosamples:
        if field_name in sample:
            value, unit = extract_numeric_value(sample[field_name])
            if value is not None:
                values_by_unit[unit].append(value)

    results = {}
    for unit, values in values_by_unit.items():
        # Create key: field_name if no unit, otherwise field_name_normalized_unit
        if unit is None:
            key = field_name
        else:
            # Normalize unit for use as dict key (e.g., % -> percent, Cel -> celsius)
            normalized_unit = normalize_unit_for_key(str(unit))
            key = f"{field_name}_{normalized_unit}"

        stats = calculate_stats(values)
        results[key] = {
            'min': stats['min'],
            'max': stats['max'],
            'mean': stats['mean'],
            'count': len(values),
            'unit': unit
        }

    return results


def aggregate_properties(
    biosamples: list[dict],
    fields: Optional[list[str]] = None,
    auto_detect: bool = True
) -> dict[str, dict]:
    """
    Aggregate numeric properties across all biosamples.

    Uses exclusion-based approach: aggregates ALL numeric fields except those
    in EXCLUDED_FIELDS (metadata, identifiers, already-handled fields).

    Parameters
    ----------
    biosamples : list[dict]
        List of biosample records
    fields : Optional[list[str]]
        Specific fields to aggregate. If None and auto_detect=True, auto-detects
        all numeric fields (excluding EXCLUDED_FIELDS).
    auto_detect : bool, default True
        If True, automatically detect numeric fields to aggregate (default behavior)

    Returns
    -------
    dict[str, dict]
        Dictionary mapping field names to aggregated statistics

    Examples
    --------
    >>> samples = [
    ...     {"ph": 6.04, "temp": {"has_numeric_value": 15.5, "has_unit": "Cel"}},
    ...     {"ph": 7.2, "temp": {"has_numeric_value": 18.2, "has_unit": "Cel"}},
    ... ]
    >>> result = aggregate_properties(samples)
    >>> 'ph' in result
    True
    >>> 'temp_celsius' in result  # Note: 'Cel' is normalized to 'celsius'
    True
    """
    # Determine which fields to aggregate
    if fields is None and auto_detect:
        # Auto-detect numeric fields (default)
        fields = _detect_numeric_fields(biosamples)
    elif fields is None:
        # No fields specified and auto-detect disabled - return empty
        return {}

    # Aggregate each field
    aggregated = {}
    for field in fields:
        field_results = aggregate_field(biosamples, field)
        if field_results:  # Only include if we found values
            aggregated.update(field_results)

    return aggregated


def _detect_numeric_fields(biosamples: list[dict]) -> list[str]:
    """
    Detect which fields contain numeric values across biosamples.

    Uses exclusion-based approach: finds all numeric fields EXCEPT those
    in EXCLUDED_FIELDS.

    Parameters
    ----------
    biosamples : list[dict]
        List of biosample records

    Returns
    -------
    list[str]
        List of field names that contain numeric values (excluding EXCLUDED_FIELDS)
    """
    numeric_fields = set()

    # Sample first N biosamples to detect fields
    sample_size = min(10, len(biosamples))
    for biosample in biosamples[:sample_size]:
        for field_name, field_value in biosample.items():
            # Skip excluded fields (metadata, identifiers, etc.)
            if field_name in EXCLUDED_FIELDS:
                continue

            value, _ = extract_numeric_value(field_value)
            if value is not None:
                numeric_fields.add(field_name)

    return sorted(numeric_fields)


def aggregate_categorical_fields(
    biosamples: list[dict],
    fields: Optional[list[str]] = None
) -> dict[str, dict]:
    """
    Aggregate categorical fields by counting occurrences of each value.

    Parameters
    ----------
    biosamples : list[dict]
        List of biosample records
    fields : Optional[list[str]]
        Specific categorical fields to aggregate. If None, uses CATEGORICAL_FIELDS.

    Returns
    -------
    dict[str, dict]
        Dictionary mapping field names to value counts

    Examples
    --------
    >>> samples = [
    ...     {"ecosystem": "Environmental", "ecosystem_category": "Terrestrial"},
    ...     {"ecosystem": "Environmental", "ecosystem_category": "Aquatic"},
    ...     {"ecosystem": "Engineered", "ecosystem_category": "Terrestrial"}
    ... ]
    >>> result = aggregate_categorical_fields(samples)
    >>> result['ecosystem']['Environmental']
    2
    >>> result['ecosystem']['Engineered']
    1
    >>> result['ecosystem_category']['Terrestrial']
    2
    """
    if fields is None:
        fields = list(CATEGORICAL_FIELDS)

    aggregated = {}

    for field_name in fields:
        value_counts = defaultdict(int)

        for sample in biosamples:
            if field_name in sample:
                value = sample[field_name]
                # Handle string values
                if isinstance(value, str):
                    value_counts[value] += 1
                # Handle None/null
                elif value is None:
                    value_counts['null'] += 1

        # Convert to regular dict and sort by count (descending)
        if value_counts:
            sorted_counts = dict(sorted(
                value_counts.items(),
                key=lambda x: (-x[1], x[0])  # Sort by count desc, then name asc
            ))
            aggregated[field_name] = sorted_counts

    return aggregated


def aggregate_geolocation(biosamples: list[dict]) -> Optional[dict]:
    """
    Extract coordinates and calculate bounding box from biosamples.

    Parameters
    ----------
    biosamples : list[dict]
        List of biosample records

    Returns
    -------
    Optional[dict]
        Dictionary with 'coordinates', 'bounding_box', and 'coordinate_count'.
        Returns None if no valid coordinates found.

    Examples
    --------
    >>> samples = [
    ...     {"lat_lon": {"latitude": 46.372, "longitude": -119.272}},
    ...     {"lat_lon": {"latitude": 46.375, "longitude": -119.270}},
    ...     {"lat_lon": {"latitude": 46.370, "longitude": -119.275}}
    ... ]
    >>> result = aggregate_geolocation(samples)
    >>> result['coordinate_count']
    3
    >>> result['bounding_box']['min_latitude']
    46.37
    >>> result['bounding_box']['max_latitude']
    46.375
    """
    coordinates = []

    for sample in biosamples:
        if 'lat_lon' in sample:
            lat_lon = sample['lat_lon']
            if isinstance(lat_lon, dict):
                lat = lat_lon.get('latitude')
                lon = lat_lon.get('longitude')
                if lat is not None and lon is not None:
                    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                        coordinates.append({
                            'latitude': float(lat),
                            'longitude': float(lon)
                        })

    if not coordinates:
        return None

    lats = [c['latitude'] for c in coordinates]
    lons = [c['longitude'] for c in coordinates]

    return {
        'coordinates': coordinates,
        'bounding_box': {
            'min_latitude': min(lats),
            'max_latitude': max(lats),
            'min_longitude': min(lons),
            'max_longitude': max(lons)
        },
        'coordinate_count': len(coordinates)
    }


def generate_study_rollup(
    study_id: str,
    biosamples: list[dict],
    include_properties: bool = True,
    include_categorical: bool = True,
    include_geolocation: bool = True,
    property_fields: Optional[list[str]] = None,
    categorical_fields: Optional[list[str]] = None
) -> dict:
    """
    Generate complete rollup for a study from its biosamples.

    Aggregates numeric properties (using exclusion-based approach),
    categorical fields (count by value), and geolocation data from all biosamples.

    Parameters
    ----------
    study_id : str
        NMDC study ID
    biosamples : list[dict]
        List of biosample records
    include_properties : bool, default True
        Include numeric property rollup
    include_categorical : bool, default True
        Include categorical field rollup (count by value)
    include_geolocation : bool, default True
        Include geolocation rollup
    property_fields : Optional[list[str]]
        Specific property fields to aggregate. If None, auto-detects all
        numeric fields (excluding EXCLUDED_FIELDS).
    categorical_fields : Optional[list[str]]
        Specific categorical fields to aggregate. If None, uses CATEGORICAL_FIELDS.

    Returns
    -------
    dict
        Complete rollup data structure with:
        - study_id: Study identifier
        - biosample_count: Number of biosamples
        - property_rollup: Aggregated numeric properties (if include_properties=True)
        - categorical_rollup: Count by value for categorical fields (if include_categorical=True)
        - geolocation_rollup: Geolocation data (if include_geolocation=True)

    Examples
    --------
    >>> samples = [
    ...     {"ph": 6.04, "ecosystem": "Environmental", "lat_lon": {"latitude": 46.372, "longitude": -119.272}},
    ...     {"ph": 7.2, "ecosystem": "Environmental", "lat_lon": {"latitude": 46.375, "longitude": -119.270}}
    ... ]
    >>> rollup = generate_study_rollup("nmdc:sty-11-test", samples)
    >>> rollup['study_id']
    'nmdc:sty-11-test'
    >>> rollup['biosample_count']
    2
    >>> 'property_rollup' in rollup
    True
    >>> 'categorical_rollup' in rollup
    True
    >>> 'geolocation_rollup' in rollup
    True
    """
    rollup = {
        'study_id': study_id,
        'biosample_count': len(biosamples)
    }

    if include_properties:
        logger.info(f"Aggregating numeric properties for {len(biosamples)} biosamples")
        properties = aggregate_properties(
            biosamples,
            fields=property_fields
        )
        rollup['property_rollup'] = properties

    if include_categorical:
        logger.info(f"Aggregating categorical fields for {len(biosamples)} biosamples")
        categorical = aggregate_categorical_fields(
            biosamples,
            fields=categorical_fields
        )
        rollup['categorical_rollup'] = categorical

    if include_geolocation:
        logger.info(f"Aggregating geolocation data for {len(biosamples)} biosamples")
        geolocation = aggregate_geolocation(biosamples)
        rollup['geolocation_rollup'] = geolocation

    return rollup
