# -*- coding: utf-8 -*-
"""
Enrichment analysis for NMDC data.

This module provides statistical enrichment analysis for comparing functional
annotations (or metabolites) across sample groups defined by biosample properties.

Examples
--------
Compare EC numbers between high and low depth samples:

>>> from nmdc_api_utilities.enrichment import EnrichmentAnalyzer
>>> analyzer = EnrichmentAnalyzer()
>>>
>>> # Load biosamples and annotations
>>> samples = {
...     "sample1": {"depth": 5.0, "annotations": {"EC:2.7.1.1": 10, "EC:3.2.1.1": 5}},
...     "sample2": {"depth": 15.0, "annotations": {"EC:2.7.1.1": 2, "EC:3.2.1.1": 20}}
... }
>>>
>>> # Run enrichment analysis
>>> results = analyzer.analyze(samples, group_by="depth", threshold=10.0)
>>>
>>> # Get significant results
>>> significant = [r for r in results if r["fdr"] < 0.05]
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import subprocess

logger = logging.getLogger(__name__)

# Cache for ontology term labels to avoid repeated lookups
_label_cache: Dict[str, str] = {}

# Cache for OAK adapters to avoid recreating them
_adapter_cache: Dict[str, Any] = {}


def get_ontology_labels_batch(term_ids: List[str], ontology: str = None) -> Dict[str, str]:
    """
    Get human-readable labels for multiple ontology terms using OAKlib batch lookup.

    Parameters
    ----------
    term_ids : List[str]
        List of ontology term IDs (e.g., ['EC:1.2.5.3', 'EC:2.7.7.49'])
    ontology : str, optional
        Ontology source adapter. If not provided, will be inferred from first term prefix

    Returns
    -------
    Dict[str, str]
        Mapping of term IDs to labels. Terms not found will not be in the dict.

    Examples
    --------
    >>> labels = get_ontology_labels_batch(['EC:1.2.5.3', 'EC:2.7.7.49'])  # doctest: +SKIP
    >>> print(labels['EC:1.2.5.3'])  # doctest: +SKIP
    'aerobic carbon monoxide dehydrogenase'
    """
    if not term_ids:
        return {}

    # Check cache first
    uncached_ids = [tid for tid in term_ids if tid not in _label_cache]
    result = {tid: _label_cache[tid] for tid in term_ids if tid in _label_cache}

    if not uncached_ids:
        return result

    # Determine ontology adapter if not provided
    if ontology is None:
        first_id = uncached_ids[0]
        if first_id.startswith('EC:'):
            ontology = 'sqlite:obo:eccode'
        elif first_id.startswith('ENVO:'):
            ontology = 'sqlite:obo:envo'
        else:
            logger.debug(f"Unknown ontology prefix for {first_id}, cannot batch lookup")
            return result

    try:
        # Try to use oaklib Python API for batch lookup
        try:
            from oaklib import get_adapter

            # Get or create cached adapter
            if ontology not in _adapter_cache:
                _adapter_cache[ontology] = get_adapter(ontology)
            adapter = _adapter_cache[ontology]

            # Batch lookup labels using labels() method (returns iterator of (id, label) tuples)
            for term_id, label in adapter.labels(uncached_ids):
                if label:
                    _label_cache[term_id] = label
                    result[term_id] = label
                    logger.debug(f"Looked up {term_id}: {label}")

            return result

        except ImportError:
            logger.debug("oaklib not available for batch lookup")
            pass
        except Exception as e:
            logger.debug(f"oaklib batch API failed: {e}")
            pass

    except Exception as e:
        logger.debug(f"Error in batch lookup: {e}")

    return result


def get_ontology_label(term_id: str, ontology: str = None) -> Optional[str]:
    """
    Get human-readable label for an ontology term using OAKlib.

    Parameters
    ----------
    term_id : str
        Ontology term ID (e.g., 'EC:1.2.5.3', 'ENVO:01000017')
    ontology : str, optional
        Ontology source adapter (e.g., 'sqlite:obo:eccode', 'sqlite:obo:envo')
        If not provided, will be inferred from term_id prefix

    Returns
    -------
    Optional[str]
        Human-readable label or None if lookup fails

    Examples
    --------
    >>> label = get_ontology_label('EC:1.2.5.3')  # doctest: +SKIP
    >>> print(label)  # doctest: +SKIP
    'aerobic carbon monoxide dehydrogenase'
    """
    # Check cache first
    if term_id in _label_cache:
        return _label_cache[term_id]

    # Determine ontology adapter if not provided
    if ontology is None:
        if term_id.startswith('EC:'):
            ontology = 'sqlite:obo:eccode'
        elif term_id.startswith('ENVO:'):
            ontology = 'sqlite:obo:envo'
        else:
            # Unknown prefix, can't look up
            logger.debug(f"Unknown ontology prefix for {term_id}, cannot lookup label")
            return None

    try:
        # Try to use oaklib Python API directly (much faster than subprocess)
        try:
            from oaklib import get_adapter

            # Get or create cached adapter
            if ontology not in _adapter_cache:
                _adapter_cache[ontology] = get_adapter(ontology)
            adapter = _adapter_cache[ontology]

            label = adapter.label(term_id)
            if label:
                _label_cache[term_id] = label
                logger.debug(f"Looked up {term_id}: {label}")
                return label
        except ImportError:
            # Fall back to subprocess if oaklib not available
            logger.debug("oaklib not available, falling back to subprocess")
            pass
        except Exception as e:
            logger.debug(f"oaklib API failed, trying subprocess: {e}")
            pass

        # Fallback: Call runoak subprocess
        result = subprocess.run(
            ['runoak', '-i', ontology, 'info', term_id],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout:
            # Parse output: format is "TERM_ID ! label"
            output = result.stdout.strip()
            if '!' in output:
                label = output.split('!', 1)[1].strip()
                _label_cache[term_id] = label
                logger.debug(f"Looked up {term_id}: {label}")
                return label
        else:
            logger.debug(f"Failed to lookup {term_id}: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout looking up {term_id}")
        return None
    except FileNotFoundError:
        logger.warning("runoak command not found - install oaklib for term label lookups")
        return None
    except Exception as e:
        logger.debug(f"Error looking up {term_id}: {e}")
        return None


@dataclass
class EnrichmentResult:
    """
    Result of enrichment analysis for a single feature.

    Attributes
    ----------
    feature_id : str
        Feature identifier (e.g., "EC:2.7.1.1")
    feature_name : str
        Human-readable name
    group1_name : str
        Name of first group
    group2_name : str
        Name of second group
    group1_count : int
        Count in first group
    group2_count : int
        Count in second group
    group1_total : int
        Total features in first group
    group2_total : int
        Total features in second group
    p_value : float
        Statistical p-value
    fdr : float
        False discovery rate (adjusted p-value)
    effect_size : float
        Effect size (fold change or odds ratio)
    enriched_in : str
        Which group the feature is enriched in
    """
    feature_id: str
    feature_name: str
    group1_name: str
    group2_name: str
    group1_count: int
    group2_count: int
    group1_total: int
    group2_total: int
    p_value: float
    fdr: float
    effect_size: float
    enriched_in: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name,
            "group1_name": self.group1_name,
            "group2_name": self.group2_name,
            "group1_count": self.group1_count,
            "group2_count": self.group2_count,
            "group1_total": self.group1_total,
            "group2_total": self.group2_total,
            "p_value": self.p_value,
            "fdr": self.fdr,
            "effect_size": self.effect_size,
            "enriched_in": self.enriched_in,
        }


class EnrichmentAnalyzer:
    """
    Statistical enrichment analysis for NMDC data.

    Compares feature abundances (e.g., EC numbers, metabolites) between
    groups of samples defined by biosample properties.

    Parameters
    ----------
    method : str, optional
        Statistical test method ('fisher', 'chi2'). Default: 'fisher'
    fdr_method : str, optional
        FDR correction method ('benjamini-hochberg', 'bonferroni'). Default: 'benjamini-hochberg'
    min_count : int, optional
        Minimum count required for a feature to be tested. Default: 5

    Examples
    --------
    >>> analyzer = EnrichmentAnalyzer(method='fisher', fdr_method='benjamini-hochberg')
    >>> results = analyzer.analyze(samples, group_by='depth', threshold=10.0)
    """

    def __init__(
        self,
        method: str = "fisher",
        fdr_method: str = "benjamini-hochberg",
        min_count: int = 5
    ):
        self.method = method
        self.fdr_method = fdr_method
        self.min_count = min_count

        # Import statistical libraries
        try:
            from scipy import stats
            self.stats = stats
        except ImportError:
            raise ImportError(
                "scipy is required for enrichment analysis. "
                "Install with: pip install scipy"
            )

        try:
            from statsmodels.stats import multitest
            self.multitest = multitest
        except ImportError:
            logger.warning(
                "statsmodels not available. FDR correction will use basic methods. "
                "Install with: pip install statsmodels"
            )
            self.multitest = None

    def analyze(
        self,
        samples: Dict[str, Dict[str, Any]],
        group_by: str,
        threshold: Optional[float] = None,
        bins: Optional[int] = None,
        categories: Optional[List[str]] = None
    ) -> List[EnrichmentResult]:
        """
        Perform enrichment analysis.

        Parameters
        ----------
        samples : Dict[str, Dict[str, Any]]
            Sample data with structure:
            {
                "sample_id": {
                    "property": value,  # e.g., "depth": 10.5
                    "annotations": {
                        "feature_id": count,  # e.g., "EC:2.7.1.1": 5
                    }
                }
            }
        group_by : str
            Property to group by (e.g., "depth", "ph", "ecosystem_type")
        threshold : float, optional
            Threshold for splitting continuous variables (e.g., depth > 10)
        bins : int, optional
            Number of bins for continuous variables (mutually exclusive with threshold)
        categories : List[str], optional
            Explicit categories for categorical variables

        Returns
        -------
        List[EnrichmentResult]
            Enrichment results sorted by FDR

        Examples
        --------
        >>> # Binary split by threshold
        >>> results = analyzer.analyze(samples, group_by="depth", threshold=10.0)

        >>> # Multiple bins
        >>> results = analyzer.analyze(samples, group_by="depth", bins=3)

        >>> # Categorical comparison
        >>> results = analyzer.analyze(samples, group_by="ecosystem_type",
        ...                            categories=["Soil", "Marine"])
        """
        # Group samples
        groups = self._group_samples(samples, group_by, threshold, bins, categories)

        if len(groups) != 2:
            raise ValueError(
                f"Enrichment requires exactly 2 groups, got {len(groups)}. "
                "Use threshold, bins, or categories to create 2 groups."
            )

        group_names = list(groups.keys())
        group1_name, group2_name = group_names[0], group_names[1]

        # Get human-readable labels for group names (e.g., ENVO terms)
        group1_label = get_ontology_label(group1_name) or group1_name
        group2_label = get_ontology_label(group2_name) or group2_name

        logger.info(f"Group 1 ({group1_label}): {len(groups[group1_name])} samples")
        logger.info(f"Group 2 ({group2_label}): {len(groups[group2_name])} samples")

        # Collect all features
        all_features = self._collect_features(groups)
        logger.info(f"Testing {len(all_features)} features")

        # Batch lookup feature labels for better performance
        logger.debug(f"Looking up labels for {len(all_features)} features...")
        feature_labels = get_ontology_labels_batch(list(all_features))

        # Perform statistical tests
        results = []
        for feature_id in all_features:
            # Count occurrences in each group
            group1_count = self._count_feature(groups[group1_name], feature_id)
            group2_count = self._count_feature(groups[group2_name], feature_id)

            # Skip if below minimum count
            if group1_count + group2_count < self.min_count:
                continue

            # Get totals
            group1_total = self._total_counts(groups[group1_name])
            group2_total = self._total_counts(groups[group2_name])

            # Perform statistical test
            p_value = self._statistical_test(
                group1_count, group1_total - group1_count,
                group2_count, group2_total - group2_count
            )

            # Calculate effect size
            effect_size = self._calculate_effect_size(
                group1_count, group1_total,
                group2_count, group2_total
            )

            # Determine enrichment direction
            rate1 = group1_count / group1_total if group1_total > 0 else 0
            rate2 = group2_count / group2_total if group2_total > 0 else 0
            enriched_in = group1_name if rate1 > rate2 else group2_name

            results.append(EnrichmentResult(
                feature_id=feature_id,
                feature_name=feature_labels.get(feature_id, feature_id),
                group1_name=group1_label,
                group2_name=group2_label,
                group1_count=group1_count,
                group2_count=group2_count,
                group1_total=group1_total,
                group2_total=group2_total,
                p_value=p_value,
                fdr=0.0,  # Will be filled in after FDR correction
                effect_size=effect_size,
                enriched_in=get_ontology_label(enriched_in) or enriched_in
            ))

        # Apply FDR correction
        results = self._apply_fdr_correction(results)

        # Sort by FDR
        results.sort(key=lambda r: (r.fdr, r.p_value))

        return results

    def _group_samples(
        self,
        samples: Dict[str, Dict[str, Any]],
        group_by: str,
        threshold: Optional[float],
        bins: Optional[int],
        categories: Optional[List[str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group samples based on property."""
        groups = {}

        # Determine if property is categorical or continuous
        values = [s[group_by] for s in samples.values() if group_by in s]

        if not values:
            raise ValueError(f"Property '{group_by}' not found in any samples")

        # Check if categorical (string values) or continuous (numeric)
        is_categorical = isinstance(values[0], str)

        if categories:
            # Explicit categories
            for cat in categories:
                groups[cat] = []

            for sample_id, sample in samples.items():
                if group_by not in sample:
                    continue
                value = sample[group_by]
                if value in categories:
                    groups[value].append(sample)

        elif is_categorical:
            # Auto-detect categories
            for sample_id, sample in samples.items():
                if group_by not in sample:
                    continue
                category = sample[group_by]
                if category not in groups:
                    groups[category] = []
                groups[category].append(sample)

        elif threshold is not None:
            # Binary split by threshold
            groups[f"{group_by} ≤ {threshold}"] = []
            groups[f"{group_by} > {threshold}"] = []

            for sample_id, sample in samples.items():
                if group_by not in sample:
                    continue
                value = sample[group_by]
                if value <= threshold:
                    groups[f"{group_by} ≤ {threshold}"].append(sample)
                else:
                    groups[f"{group_by} > {threshold}"].append(sample)

        elif bins is not None:
            # Create bins
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            min_val, max_val = min(numeric_values), max(numeric_values)
            bin_edges = [min_val + i * (max_val - min_val) / bins for i in range(bins + 1)]

            # For 2 groups, combine bins
            if bins == 2:
                group_names = [
                    f"{group_by} [{bin_edges[0]:.1f}, {bin_edges[1]:.1f})",
                    f"{group_by} [{bin_edges[1]:.1f}, {bin_edges[2]:.1f}]"
                ]
            else:
                raise ValueError(f"bins={bins} would create {bins} groups, need exactly 2")

            for name in group_names:
                groups[name] = []

            for sample_id, sample in samples.items():
                if group_by not in sample:
                    continue
                value = sample[group_by]
                if value < bin_edges[1]:
                    groups[group_names[0]].append(sample)
                else:
                    groups[group_names[1]].append(sample)

        else:
            # Auto-threshold at median
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            median = sorted(numeric_values)[len(numeric_values) // 2]
            logger.info(f"Auto-thresholding at median: {median}")
            return self._group_samples(samples, group_by, median, None, None)

        return groups

    def _collect_features(self, groups: Dict[str, List[Dict]]) -> List[str]:
        """Collect all unique features across all samples."""
        features = set()
        for group_samples in groups.values():
            for sample in group_samples:
                if "annotations" in sample:
                    features.update(sample["annotations"].keys())
        return list(features)

    def _count_feature(self, samples: List[Dict], feature_id: str) -> int:
        """Count occurrences of a feature across samples."""
        total = 0
        for sample in samples:
            if "annotations" in sample and feature_id in sample["annotations"]:
                total += sample["annotations"][feature_id]
        return total

    def _total_counts(self, samples: List[Dict]) -> int:
        """Get total annotation counts across samples."""
        total = 0
        for sample in samples:
            if "annotations" in sample:
                total += sum(sample["annotations"].values())
        return total

    def _statistical_test(
        self,
        a: int,  # feature in group 1
        b: int,  # not feature in group 1
        c: int,  # feature in group 2
        d: int   # not feature in group 2
    ) -> float:
        """Perform statistical test."""
        if self.method == "fisher":
            # Fisher's exact test
            # Contingency table:
            # [[a, b],
            #  [c, d]]
            odds_ratio, p_value = self.stats.fisher_exact([[a, b], [c, d]])
            return p_value

        elif self.method == "chi2":
            # Chi-square test
            chi2, p_value, dof, expected = self.stats.chi2_contingency([[a, b], [c, d]])
            return p_value

        else:
            raise ValueError(f"Unknown statistical method: {self.method}")

    def _calculate_effect_size(
        self,
        count1: int,
        total1: int,
        count2: int,
        total2: int
    ) -> float:
        """Calculate effect size (fold change)."""
        rate1 = count1 / total1 if total1 > 0 else 0
        rate2 = count2 / total2 if total2 > 0 else 0

        if rate2 == 0:
            return float('inf') if rate1 > 0 else 1.0

        return rate1 / rate2

    def _apply_fdr_correction(self, results: List[EnrichmentResult]) -> List[EnrichmentResult]:
        """Apply FDR correction to p-values."""
        if not results:
            return results

        p_values = [r.p_value for r in results]

        if self.multitest:
            # Use statsmodels for proper FDR correction
            if self.fdr_method == "benjamini-hochberg" or self.fdr_method == "fdr_bh":
                reject, fdr_values, _, _ = self.multitest.multipletests(
                    p_values, method='fdr_bh'
                )
            elif self.fdr_method == "bonferroni":
                reject, fdr_values, _, _ = self.multitest.multipletests(
                    p_values, method='bonferroni'
                )
            else:
                raise ValueError(f"Unknown FDR method: {self.fdr_method}")
        else:
            # Simple Bonferroni correction as fallback
            n = len(p_values)
            fdr_values = [min(p * n, 1.0) for p in p_values]

        # Update results with FDR values
        for result, fdr in zip(results, fdr_values):
            result.fdr = fdr

        return results

    def _get_feature_name(self, feature_id: str) -> str:
        """
        Get human-readable name for feature using ontology lookups.

        Uses OAKlib to look up labels for EC numbers and ENVO terms.
        Falls back to returning the ID if lookup fails or OAK is not available.

        Parameters
        ----------
        feature_id : str
            Feature identifier (e.g., 'EC:1.2.5.3', 'ENVO:01000017')

        Returns
        -------
        str
            Human-readable label or the feature_id if lookup fails
        """
        label = get_ontology_label(feature_id)
        return label if label else feature_id

    def export_results(
        self,
        results: List[EnrichmentResult],
        output_path: Union[str, Path],
        format: str = "tsv"
    ):
        """
        Export enrichment results to file.

        Parameters
        ----------
        results : List[EnrichmentResult]
            Enrichment results
        output_path : Union[str, Path]
            Output file path
        format : str, optional
            Output format ('tsv', 'json', 'csv'). Default: 'tsv'

        Examples
        --------
        >>> analyzer.export_results(results, "enrichment.tsv", format="tsv")
        >>> analyzer.export_results(results, "enrichment.json", format="json")
        """
        output_path = Path(output_path)

        if format == "json":
            with open(output_path, 'w') as f:
                json.dump([r.to_dict() for r in results], f, indent=2)

        elif format in ("tsv", "csv"):
            import csv
            delimiter = '\t' if format == "tsv" else ','

            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)

                # Header
                writer.writerow([
                    "feature_id", "feature_name",
                    "group1_name", "group1_count", "group1_total",
                    "group2_name", "group2_count", "group2_total",
                    "p_value", "fdr", "effect_size", "enriched_in"
                ])

                # Data
                for r in results:
                    writer.writerow([
                        r.feature_id, r.feature_name,
                        r.group1_name, r.group1_count, r.group1_total,
                        r.group2_name, r.group2_count, r.group2_total,
                        f"{r.p_value:.6e}", f"{r.fdr:.6e}",
                        f"{r.effect_size:.3f}", r.enriched_in
                    ])

        else:
            raise ValueError(f"Unknown format: {format}")

        logger.info(f"Exported {len(results)} results to {output_path}")


def load_samples_from_gff_and_biosamples(
    biosample_file: Union[str, Path, List[Dict]],
    gff_files: Dict[str, Union[str, Path]],
    annotation_type: str = "ec_number"
) -> Dict[str, Dict[str, Any]]:
    """
    Load sample data from biosample JSON and GFF files.

    Parameters
    ----------
    biosample_file : Union[str, Path, List[Dict]]
        Path to biosample JSON file (from study dump) OR a list of biosample dicts
    gff_files : Dict[str, Union[str, Path]]
        Mapping of biosample_id to GFF file path
    annotation_type : str, optional
        Type of annotation to extract ('ec_number', 'pfam', 'cog', 'ko')

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Sample data structure ready for enrichment analysis

    Examples
    --------
    >>> samples = load_samples_from_gff_and_biosamples(
    ...     "biosamples.json",
    ...     {"sample1": "sample1.gff", "sample2": "sample2.gff"},
    ...     annotation_type="ec_number"
    ... )
    """
    from nmdc_api_utilities.gff_utils import load_gff

    # Load biosample metadata
    if isinstance(biosample_file, list):
        # Already a list of biosamples
        biosamples = biosample_file
    else:
        # Load from file
        biosample_file = Path(biosample_file)
        with open(biosample_file) as f:
            biosamples = json.load(f)

        # If biosamples is a dict with single key, extract the list
        if isinstance(biosamples, dict) and len(biosamples) == 1:
            biosamples = list(biosamples.values())[0]

    # Create biosample lookup
    biosample_lookup = {b["id"]: b for b in biosamples}

    samples = {}

    for biosample_id, gff_file in gff_files.items():
        if biosample_id not in biosample_lookup:
            logger.warning(f"Biosample {biosample_id} not found in metadata")
            continue

        biosample = biosample_lookup[biosample_id]

        # Load GFF and count annotations
        gff_file = Path(gff_file)
        if not gff_file.exists():
            logger.warning(f"GFF file not found: {gff_file}")
            continue

        reader = load_gff(gff_file, use_duckdb=True)
        df = reader.df

        # Count annotations
        annotations = {}
        for idx, row in df.iterrows():
            annot_value = row.get(annotation_type)
            if annot_value and str(annot_value) != "nan":
                # Handle comma-separated values
                if "," in str(annot_value):
                    for val in str(annot_value).split(","):
                        val = val.strip()
                        annotations[val] = annotations.get(val, 0) + 1
                else:
                    annot_value = str(annot_value)
                    annotations[annot_value] = annotations.get(annot_value, 0) + 1

        reader.close()

        # Extract biosample properties
        sample_data = {
            "biosample_id": biosample_id,
            "annotations": annotations
        }

        # Add numeric properties
        for key in ["depth", "ph", "temperature", "salinity", "latitude", "longitude"]:
            # Check various possible field names
            for field_name in [key, f"{key}_has_numeric_value", f"{key}_has_maximum_numeric_value"]:
                if field_name in biosample:
                    value = biosample[field_name]
                    if isinstance(value, dict) and "has_numeric_value" in value:
                        value = value["has_numeric_value"]
                    if isinstance(value, (int, float)):
                        sample_data[key] = value
                        break

        # Add categorical properties
        for key in ["ecosystem", "ecosystem_category", "ecosystem_type", "ecosystem_subtype", "env_medium", "env_broad_scale", "env_local_scale"]:
            if key in biosample:
                value = biosample[key]
                # Extract has_raw_value if it's a nested dict
                if isinstance(value, dict) and "has_raw_value" in value:
                    value = value["has_raw_value"]
                sample_data[key] = value

        samples[biosample_id] = sample_data

    logger.info(f"Loaded {len(samples)} samples")
    return samples
