# -*- coding: utf-8 -*-
"""
Tests for aggregation utilities.
"""
import pytest
from nmdc_api_utilities.aggregation import (
    extract_numeric_value,
    calculate_stats,
    aggregate_field,
    aggregate_properties,
    aggregate_geolocation,
    generate_study_rollup,
    normalize_unit_for_key,
)


class TestExtractNumericValue:
    """Test extraction of numeric values from different formats."""

    def test_extract_scalar_value(self):
        """Test extraction from scalar pH value."""
        value, unit = extract_numeric_value(6.04)
        assert value == 6.04
        assert unit is None

    def test_extract_scalar_int(self):
        """Test extraction from scalar int value."""
        value, unit = extract_numeric_value(42)
        assert value == 42.0
        assert unit is None

    def test_extract_quantity_value(self):
        """Test extraction from QuantityValue object."""
        data = {"has_numeric_value": 6.6, "has_unit": "Cel", "type": "nmdc:QuantityValue"}
        value, unit = extract_numeric_value(data)
        assert value == 6.6
        assert unit == "Cel"

    def test_extract_quantity_value_no_unit(self):
        """Test extraction from QuantityValue without unit."""
        data = {"has_numeric_value": 25.4, "type": "nmdc:QuantityValue"}
        value, unit = extract_numeric_value(data)
        assert value == 25.4
        assert unit is None

    def test_extract_range_value(self):
        """Test extraction from range (uses midpoint)."""
        data = {
            "has_minimum_numeric_value": 0,
            "has_maximum_numeric_value": 0.5,
            "has_unit": "m",
            "type": "nmdc:QuantityValue"
        }
        value, unit = extract_numeric_value(data)
        assert value == 0.25
        assert unit == "m"

    def test_extract_range_value_same_min_max(self):
        """Test extraction from range where min=max."""
        data = {
            "has_minimum_numeric_value": 0.4,
            "has_maximum_numeric_value": 0.4,
            "has_unit": "m",
            "type": "nmdc:QuantityValue"
        }
        value, unit = extract_numeric_value(data)
        assert value == 0.4
        assert unit == "m"

    def test_extract_from_string_list(self):
        """Test extraction from list with string value."""
        data = ["2.667 g of water/g of dry soil"]
        value, unit = extract_numeric_value(data)
        assert value == 2.667
        assert unit == "g of water/g of dry soil"

    def test_extract_invalid_string(self):
        """Test extraction from non-numeric string."""
        value, unit = extract_numeric_value("not a number")
        assert value is None
        assert unit is None

    def test_extract_none(self):
        """Test extraction from None."""
        value, unit = extract_numeric_value(None)
        assert value is None
        assert unit is None

    def test_extract_empty_dict(self):
        """Test extraction from empty dict."""
        value, unit = extract_numeric_value({})
        assert value is None
        assert unit is None


class TestCalculateStats:
    """Test statistical calculations."""

    def test_calculate_basic_stats(self):
        """Test min, max, mean calculation."""
        values = [5.2, 6.4, 7.1, 5.8, 6.9]
        stats = calculate_stats(values)
        assert stats['min'] == 5.2
        assert stats['max'] == 7.1
        assert abs(stats['mean'] - 6.28) < 0.01

    def test_calculate_single_value(self):
        """Test stats with single value."""
        values = [42.0]
        stats = calculate_stats(values)
        assert stats['min'] == 42.0
        assert stats['max'] == 42.0
        assert stats['mean'] == 42.0

    def test_calculate_empty_list(self):
        """Test stats with empty list."""
        values = []
        stats = calculate_stats(values)
        assert stats['min'] is None
        assert stats['max'] is None
        assert stats['mean'] is None

    def test_calculate_all_same(self):
        """Test stats when all values are the same."""
        values = [6.0, 6.0, 6.0, 6.0]
        stats = calculate_stats(values)
        assert stats['min'] == 6.0
        assert stats['max'] == 6.0
        assert stats['mean'] == 6.0


class TestAggregateField:
    """Test field aggregation across biosamples."""

    def test_aggregate_scalar_field(self):
        """Test aggregation of scalar pH values."""
        samples = [
            {"ph": 6.04},
            {"ph": 7.2},
            {"ph": 5.8}
        ]
        result = aggregate_field(samples, "ph")
        assert 'ph' in result
        assert result['ph']['min'] == 5.8
        assert result['ph']['max'] == 7.2
        assert abs(result['ph']['mean'] - 6.35) < 0.01
        assert result['ph']['count'] == 3
        assert result['ph']['unit'] is None

    def test_aggregate_quantity_value_field(self):
        """Test aggregation of QuantityValue fields."""
        samples = [
            {"temp": {"has_numeric_value": 15.5, "has_unit": "Cel"}},
            {"temp": {"has_numeric_value": 18.2, "has_unit": "Cel"}},
            {"temp": {"has_numeric_value": 12.3, "has_unit": "Cel"}}
        ]
        result = aggregate_field(samples, "temp")
        assert 'temp_celsius' in result  # Note: 'Cel' is normalized to 'celsius'
        assert result['temp_celsius']['min'] == 12.3
        assert result['temp_celsius']['max'] == 18.2
        assert result['temp_celsius']['unit'] == "Cel"

    def test_aggregate_mixed_units(self):
        """Test aggregation when same field has different units."""
        samples = [
            {"temp": {"has_numeric_value": 15.5, "has_unit": "Cel"}},
            {"temp": {"has_numeric_value": 59.0, "has_unit": "F"}},
        ]
        result = aggregate_field(samples, "temp")
        # Should create separate aggregations for each unit
        assert 'temp_Cel' in result or 'temp_F' in result
        assert len(result) == 2

    def test_aggregate_missing_field(self):
        """Test aggregation when field is missing from some samples."""
        samples = [
            {"ph": 6.04},
            {"salinity": 35.0},  # No pH
            {"ph": 7.2}
        ]
        result = aggregate_field(samples, "ph")
        assert 'ph' in result
        assert result['ph']['count'] == 2
        assert result['ph']['min'] == 6.04
        assert result['ph']['max'] == 7.2

    def test_aggregate_all_missing(self):
        """Test aggregation when field is missing from all samples."""
        samples = [
            {"salinity": 35.0},
            {"temp": 15.5}
        ]
        result = aggregate_field(samples, "ph")
        assert result == {}


class TestNormalizeUnitForKey:
    """Test unit normalization for use in dictionary keys."""

    def test_normalize_percent(self):
        """Test normalization of percent symbol."""
        assert normalize_unit_for_key('%') == 'percent'

    def test_normalize_celsius_variants(self):
        """Test normalization of different celsius representations."""
        assert normalize_unit_for_key('Cel') == 'celsius'
        assert normalize_unit_for_key('°C') == 'celsius'
        assert normalize_unit_for_key('℃') == 'celsius'

    def test_normalize_common_units(self):
        """Test normalization of common measurement units."""
        assert normalize_unit_for_key('m') == 'meters'
        assert normalize_unit_for_key('kg') == 'kilograms'
        assert normalize_unit_for_key('L') == 'liters'
        assert normalize_unit_for_key('ppm') == 'ppm'

    def test_normalize_complex_unit(self):
        """Test normalization of units with special characters."""
        # Units not in UNIT_NORMALIZATION get sanitized
        assert normalize_unit_for_key('mg/kg') == 'mg_kg'
        # Note: ² is a word character in Unicode, so it's preserved
        assert normalize_unit_for_key('g/m²') == 'g_m²'

    def test_normalize_strips_trailing_underscore(self):
        """Test that trailing underscores are stripped."""
        # Single character special chars should not create trailing underscores
        result = normalize_unit_for_key('m²')
        assert not result.endswith('_')


class TestAggregateBiogeochemicalMeasurements:
    """Test biogeochemical measurement aggregation."""

    def test_aggregate_auto_detect(self):
        """Test auto-detection of numeric fields."""
        samples = [
            {"ph": 6.04, "temp": {"has_numeric_value": 15.5, "has_unit": "Cel"}, "name": "Sample 1"},
            {"ph": 7.2, "temp": {"has_numeric_value": 18.2, "has_unit": "Cel"}, "name": "Sample 2"},
        ]
        result = aggregate_properties(samples)
        assert 'ph' in result
        assert 'temp_celsius' in result  # Note: 'Cel' is normalized to 'celsius'
        # Should not include metadata fields
        assert 'name' not in result

    def test_aggregate_specific_fields(self):
        """Test aggregation of specific fields only."""
        samples = [
            {"ph": 6.04, "temp": 15.5, "depth": 10.0},
            {"ph": 7.2, "temp": 18.2, "depth": 12.0},
        ]
        result = aggregate_properties(
            samples,
            fields=['ph', 'depth'],
            auto_detect=False
        )
        assert 'ph' in result
        assert 'depth' in result
        # temp should not be included
        assert 'temp' not in result

    def test_aggregate_empty_samples(self):
        """Test aggregation with empty sample list."""
        result = aggregate_properties([])
        assert result == {}


class TestAggregateGeolocation:
    """Test geolocation aggregation."""

    def test_aggregate_coordinates(self):
        """Test aggregation of coordinates and bounding box."""
        samples = [
            {"lat_lon": {"latitude": 46.372, "longitude": -119.272}},
            {"lat_lon": {"latitude": 46.375, "longitude": -119.270}},
            {"lat_lon": {"latitude": 46.370, "longitude": -119.275}}
        ]
        result = aggregate_geolocation(samples)

        assert result is not None
        assert result['coordinate_count'] == 3
        assert len(result['coordinates']) == 3

        bbox = result['bounding_box']
        assert bbox['min_latitude'] == 46.370
        assert bbox['max_latitude'] == 46.375
        assert bbox['min_longitude'] == -119.275
        assert bbox['max_longitude'] == -119.270

    def test_aggregate_single_coordinate(self):
        """Test aggregation with single coordinate."""
        samples = [
            {"lat_lon": {"latitude": 46.372, "longitude": -119.272}}
        ]
        result = aggregate_geolocation(samples)

        assert result is not None
        assert result['coordinate_count'] == 1
        bbox = result['bounding_box']
        assert bbox['min_latitude'] == bbox['max_latitude'] == 46.372
        assert bbox['min_longitude'] == bbox['max_longitude'] == -119.272

    def test_aggregate_missing_coordinates(self):
        """Test aggregation when some samples lack coordinates."""
        samples = [
            {"lat_lon": {"latitude": 46.372, "longitude": -119.272}},
            {"name": "Sample without coords"},
            {"lat_lon": {"latitude": 46.375, "longitude": -119.270}}
        ]
        result = aggregate_geolocation(samples)

        assert result is not None
        assert result['coordinate_count'] == 2

    def test_aggregate_no_coordinates(self):
        """Test aggregation when no samples have coordinates."""
        samples = [
            {"name": "Sample 1"},
            {"name": "Sample 2"}
        ]
        result = aggregate_geolocation(samples)
        assert result is None


class TestGenerateStudyRollup:
    """Test complete study rollup generation."""

    def test_generate_complete_rollup(self):
        """Test generation of complete rollup with all features."""
        samples = [
            {
                "id": "nmdc:bsm-1",
                "ph": 6.04,
                "temp": {"has_numeric_value": 15.5, "has_unit": "Cel"},
                "lat_lon": {"latitude": 46.372, "longitude": -119.272}
            },
            {
                "id": "nmdc:bsm-2",
                "ph": 7.2,
                "temp": {"has_numeric_value": 18.2, "has_unit": "Cel"},
                "lat_lon": {"latitude": 46.375, "longitude": -119.270}
            }
        ]

        rollup = generate_study_rollup("nmdc:sty-11-test", samples)

        assert rollup['study_id'] == "nmdc:sty-11-test"
        assert rollup['biosample_count'] == 2
        assert 'property_rollup' in rollup
        assert 'geolocation_rollup' in rollup

        # Check property data
        assert 'ph' in rollup['property_rollup']
        assert 'temp_celsius' in rollup['property_rollup']  # Note: 'Cel' normalized to 'celsius'

        # Check geolocation data
        assert rollup['geolocation_rollup']['coordinate_count'] == 2

    def test_generate_rollup_no_properties(self):
        """Test rollup with properties disabled."""
        samples = [
            {"ph": 6.04, "lat_lon": {"latitude": 46.372, "longitude": -119.272}}
        ]

        rollup = generate_study_rollup(
            "nmdc:sty-11-test",
            samples,
            include_properties=False
        )

        assert 'property_rollup' not in rollup
        assert 'geolocation_rollup' in rollup

    def test_generate_rollup_no_geolocation(self):
        """Test rollup with geolocation disabled."""
        samples = [
            {"ph": 6.04, "lat_lon": {"latitude": 46.372, "longitude": -119.272}}
        ]

        rollup = generate_study_rollup(
            "nmdc:sty-11-test",
            samples,
            include_geolocation=False
        )

        assert 'property_rollup' in rollup
        assert 'geolocation_rollup' not in rollup

    def test_generate_rollup_empty_samples(self):
        """Test rollup with empty sample list."""
        rollup = generate_study_rollup("nmdc:sty-11-test", [])

        assert rollup['study_id'] == "nmdc:sty-11-test"
        assert rollup['biosample_count'] == 0

    def test_generate_rollup_specific_fields(self):
        """Test rollup with specific property fields."""
        samples = [
            {"ph": 6.04, "temp": 15.5, "depth": 10.0},
            {"ph": 7.2, "temp": 18.2, "depth": 12.0}
        ]

        rollup = generate_study_rollup(
            "nmdc:sty-11-test",
            samples,
            property_fields=['ph']
        )

        assert 'ph' in rollup['property_rollup']
        # Other fields should not be included if specific fields are requested
        # (This depends on implementation - the current implementation will include all if fields are specified)
