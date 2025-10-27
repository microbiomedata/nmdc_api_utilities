# -*- coding: utf-8 -*-
"""
Command-line interface for nmdc_api_utilities.

Provides convenient access to NMDC API operations via the command line.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from rich.logging import RichHandler

from nmdc_api_utilities.biosample_search import BiosampleSearch
from nmdc_api_utilities.study_search import StudySearch
from nmdc_api_utilities.data_object_search import DataObjectSearch
from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch
from nmdc_api_utilities.study_dumper import StudyDumper
from nmdc_api_utilities.collection_helpers import CollectionHelpers
from nmdc_api_utilities.metadata import Metadata
from nmdc_api_utilities.minter import Minter
from nmdc_api_utilities.auth import NMDCAuth
from nmdc_api_utilities.utils import parse_filter
from nmdc_api_utilities.export_utils import export_records
from nmdc_api_utilities.functional_biosample_search import FunctionalBiosampleSearch

app = typer.Typer(
    name="nmdc",
    help="NMDC API utilities command-line interface",
    add_completion=False,
)

console = Console()
error_console = Console(stderr=True)

# Common options for all commands
env_option = typer.Option(
    "prod",
    "--env", "-e",
    help="API environment (prod, dev, or backup)",
    envvar="NMDC_ENV"
)
verbose_option = typer.Option(
    0,
    "--verbose", "-v",
    count=True,
    help="Increase verbosity: -v (INFO: show API URLs and timing), -vv (DEBUG: show full requests/responses), -vvv (DEBUG: show all library details)"
)
format_option = typer.Option(
    "auto",
    "--format", "-f",
    help="Output format: json, csv, tsv, or auto (detect from file extension)"
)


def setup_logging(verbose: int = 0):
    """
    Configure logging based on verbosity level.

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG)
    """
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:  # 2 or more
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=True, show_path=False)],
        force=True  # Override any existing logging configuration
    )


@app.command()
def biosample(
    id: Optional[str] = typer.Option(None, "--id", help="Get biosample by ID"),
    filter: Optional[str] = typer.Option(None, "--filter", help="Filter query (YAML or JSON format)"),
    bbox: Optional[str] = typer.Option(None, "--bbox", help="Bounding box filter: min_lat,min_lon,max_lat,max_lon"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of records to return"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages of results"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON/CSV/TSV)"),
    format: str = format_option,
    # NEW LINKING OPTIONS
    get_studies: bool = typer.Option(False, "--get-studies", help="Get linked studies for this biosample (requires --id)"),
    get_data_objects: bool = typer.Option(False, "--get-data-objects", help="Get all linked data objects (requires --id)"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Search and retrieve biosample records.

    Filter syntax supports both YAML and JSON formats:
    - Simple: 'ecosystem_category: Terrestrial'
    - Nested: 'env_broad_scale.has_raw_value: agricultural biome [ENVO:01001442]'
    - JSON with operators: '{"lat_lon": {"$exists": true}}'

    NEW: Geographic bounding box filtering:
    - --bbox: Filter by geographic coordinates (min_lat,min_lon,max_lat,max_lon)
    - Can be combined with other filters

    Linking options to find related objects (requires --id):
    - --get-studies: Find studies associated with a biosample
    - --get-data-objects: Find all data files derived from a biosample

    Examples:

    \b
        # Get a specific biosample by ID
        nmdc biosample --id nmdc:bsm-13-amrnys72

    \b
        # Simple YAML filter by ecosystem
        nmdc biosample --filter 'ecosystem_category: Terrestrial' --limit 5

    \b
        # Nested field filter (note: must match full value)
        nmdc biosample --filter 'env_broad_scale.has_raw_value: agricultural biome [ENVO:01001442]' --limit 5

    \b
        # JSON filter with MongoDB operators ($exists, $regex, etc.)
        nmdc biosample --filter '{"lat_lon": {"$exists": true}}' --all -o biosamples.json

    \b
        # NEW: Filter by bounding box (California region)
        nmdc biosample --bbox "32.5,-124.5,42.0,-114.0" --all

    \b
        # NEW: Combine geographic and ecosystem filters
        nmdc biosample --filter 'ecosystem_category: Terrestrial' --bbox "30,-120,40,-100" --limit 50

    \b
        # Export to CSV with auto-flattened columns
        nmdc biosample --filter 'ecosystem_category: Terrestrial' --limit 100 -o results.csv

    \b
        # Get linked studies for a biosample
        nmdc biosample --id nmdc:bsm-11-x5xj6p33 --get-studies

    \b
        # Get all data objects for a biosample
        nmdc biosample --id nmdc:bsm-11-x5xj6p33 --get-data-objects
    """
    setup_logging(verbose)
    client = BiosampleSearch(env=env)

    try:
        if id:
            # Handle linking operations
            if get_studies:
                with console.status("[bold green]Finding linked studies..."):
                    results = client.get_linked_studies(id, hydrate=True)
                console.print(f"\n[green]Found {len(results)} linked study(ies)[/green]")
                _display_results(results, output, format)
            elif get_data_objects:
                with console.status("[bold green]Finding linked data objects..."):
                    results = client.get_linked_data_objects(id, hydrate=True)
                console.print(f"\n[green]Found {len(results)} data object(s)[/green]")

                # Group by type for display
                by_type = {}
                for obj in results:
                    obj_type = obj.get("data_object_type", "Unknown")
                    by_type.setdefault(obj_type, []).append(obj)

                console.print("\n[bold]Data objects by type:[/bold]")
                for obj_type, objs in sorted(by_type.items()):
                    console.print(f"  {obj_type}: {len(objs)} file(s)")

                _display_results(results, output, format)
            else:
                # Regular get by ID
                results = client.get_record_by_id(collection_id=id)
                _display_results([results] if isinstance(results, dict) else results, output, format)
        else:
            if get_studies or get_data_objects:
                error_console.print("[red]Error:[/red] --get-studies and --get-data-objects require --id")
                raise typer.Exit(1)

            # Parse filter to handle both YAML and JSON
            parsed_filter = ""
            if filter:
                try:
                    parsed_filter = parse_filter(filter)
                except ValueError as e:
                    error_console.print(f"[red]Invalid filter syntax:[/red] {e}")
                    raise typer.Exit(1)

            # Handle bounding box filter
            if bbox:
                from nmdc_api_utilities.data_processing import DataProcessing
                dp = DataProcessing()
                try:
                    # Parse bbox: min_lat,min_lon,max_lat,max_lon
                    parts = [float(x.strip()) for x in bbox.split(',')]
                    if len(parts) != 4:
                        raise ValueError("Bounding box must have exactly 4 values: min_lat,min_lon,max_lat,max_lon")
                    min_lat, min_lon, max_lat, max_lon = parts

                    # Convert bbox to filter
                    bbox_filter = dp.bbox_to_filter(min_lat, min_lon, max_lat, max_lon)

                    # Merge with existing filter if present
                    if parsed_filter:
                        parsed_filter = dp.merge_filters(parsed_filter, bbox_filter)
                    else:
                        parsed_filter = bbox_filter

                except ValueError as e:
                    error_console.print(f"[red]Invalid bounding box:[/red] {e}")
                    raise typer.Exit(1)

            results = client.get_records(filter=parsed_filter, max_page_size=limit, all_pages=all_pages)
            _display_results(results, output, format)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def study(
    id: Optional[str] = typer.Option(None, "--id", help="Get study by ID"),
    filter: Optional[str] = typer.Option(None, "--filter", help="Filter query (YAML or JSON format)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of records to return"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages of results"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON/CSV/TSV)"),
    format: str = format_option,
    # NEW LINKING OPTIONS
    get_biosamples: bool = typer.Option(False, "--get-biosamples", help="Get all biosamples in this study (requires --id)"),
    get_data_objects: bool = typer.Option(False, "--get-data-objects", help="Get all data objects for this study (requires --id)"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Search and retrieve study records.

    Filter syntax supports both YAML and JSON formats.

    NEW: Linking options to find related objects (requires --id):
    - --get-biosamples: Find all biosamples in a study
    - --get-data-objects: Find all data files across all biosamples in a study

    Examples:

    \b
        # Get a specific study by ID
        nmdc study --id nmdc:sty-11-34xj1150

    \b
        # Simple YAML filter by ecosystem
        nmdc study --filter 'ecosystem_category: Aquatic' --limit 5

    \b
        # Search by principal investigator (must match full name)
        nmdc study --filter 'principal_investigator.has_raw_value: Jennifer Pett-Ridge' --limit 5

    \b
        # NEW: Get all biosamples in a study
        nmdc study --id nmdc:sty-11-547rwq94 --get-biosamples

    \b
        # NEW: Get all data objects for a study (may be large!)
        nmdc study --id nmdc:sty-11-547rwq94 --get-data-objects -o study_data.json
    """
    setup_logging(verbose)
    client = StudySearch(env=env)

    try:
        if id:
            # Handle linking operations
            if get_biosamples:
                with console.status("[bold green]Finding biosamples in study..."):
                    results = client.get_linked_biosamples(id, hydrate=True)
                console.print(f"\n[green]Found {len(results)} biosample(s)[/green]")
                _display_results(results, output, format)
            elif get_data_objects:
                with console.status("[bold green]Finding all data objects for study (this may take a while)..."):
                    results_dict = client.get_all_linked_data_objects(id, hydrate=True, group_by_type=True)

                total = sum(len(objs) for objs in results_dict.values())
                console.print(f"\n[green]Found {total} data object(s) across {len(results_dict)} type(s)[/green]")

                console.print("\n[bold]Data objects by type:[/bold]")
                for obj_type, objs in sorted(results_dict.items(), key=lambda x: -len(x[1])):
                    console.print(f"  {obj_type}: {len(objs)} file(s)")

                # Flatten for output
                all_results = []
                for objs in results_dict.values():
                    all_results.extend(objs)
                _display_results(all_results, output, format)
            else:
                # Regular get by ID
                results = client.get_record_by_id(collection_id=id)
                _display_results([results] if isinstance(results, dict) else results, output, format)
        else:
            if get_biosamples or get_data_objects:
                error_console.print("[red]Error:[/red] --get-biosamples and --get-data-objects require --id")
                raise typer.Exit(1)

            # Parse filter to handle both YAML and JSON
            parsed_filter = ""
            if filter:
                try:
                    parsed_filter = parse_filter(filter)
                except ValueError as e:
                    error_console.print(f"[red]Invalid filter syntax:[/red] {e}")
                    raise typer.Exit(1)

            results = client.get_records(filter=parsed_filter, max_page_size=limit, all_pages=all_pages)
            _display_results(results, output, format)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def data_object(
    id: Optional[str] = typer.Option(None, "--id", help="Get data object by ID"),
    filter: Optional[str] = typer.Option(None, "--filter", help="Filter query (YAML or JSON format)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of records to return"),
    all_pages: bool = typer.Option(False, "--all", "-a", help="Fetch all pages of results"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON/CSV/TSV)"),
    format: str = format_option,
    get_biosample: bool = typer.Option(False, "--get-biosample", help="Trace data object back to source biosample(s) (requires --id)"),
    get_study: bool = typer.Option(False, "--get-study", help="Find which study this data object belongs to (requires --id)"),
    trace_provenance: bool = typer.Option(False, "--trace-provenance", help="Get complete provenance chain (requires --id)"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Search and retrieve data object records.

    Filter syntax supports both YAML and JSON formats.

    Examples:

    \b
        # Get a specific data object by ID
        nmdc data-object --id nmdc:dobj-11-abc123

    \b
        # Simple YAML filter by type
        nmdc data-object --filter 'data_object_type: QC Statistics' --limit 5

    \b
        # JSON filter with regex to find multiple types
        nmdc data-object --filter '{"data_object_type": {"$regex": "Assembly"}}' --limit 5

    \b
        # NEW: Trace a data object back to its source biosample
        nmdc data-object --id nmdc:dobj-11-abc123 --get-biosample

    \b
        # NEW: Find which study a data object belongs to
        nmdc data-object --id nmdc:dobj-11-abc123 --get-study

    \b
        # NEW: Get complete provenance chain (all upstream entities)
        nmdc data-object --id nmdc:dobj-11-abc123 --trace-provenance
    """
    setup_logging(verbose)
    client = DataObjectSearch(env=env)

    try:
        if id:
            # Handle linking operations
            if get_biosample:
                with console.status("[bold green]Tracing data object to source biosample(s)..."):
                    results = client.get_linked_biosample(id, hydrate=True)
                console.print(f"\n[green]Found {len(results)} linked biosample(s)[/green]")
                _display_results(results, output, format)
            elif get_study:
                with console.status("[bold green]Finding study for data object..."):
                    results = client.get_linked_study(id, hydrate=True)
                console.print(f"\n[green]Found {len(results)} linked study(ies)[/green]")
                _display_results(results, output, format)
            elif trace_provenance:
                with console.status("[bold green]Tracing complete provenance chain..."):
                    provenance = client.get_provenance_chain(id, hydrate=True)

                # Display summary of provenance chain
                console.print("\n[bold]Provenance Chain Summary:[/bold]\n")
                total_entities = sum(len(entities) for entities in provenance.values())
                console.print(f"[green]Found {total_entities} total entities in provenance chain[/green]\n")

                for entity_type, entities in provenance.items():
                    if entities:
                        console.print(f"  [cyan]{entity_type}:[/cyan] {len(entities)}")

                # Save full provenance to output file if requested
                if output:
                    output_abs = output.resolve()
                    with open(output_abs, "w") as f:
                        json.dump(provenance, f, indent=2)
                    console.print(f"\n[green]✓[/green] Saved complete provenance chain to {output_abs}")
                else:
                    console.print("\n[dim]Tip: Use --output to save complete provenance chain to a file[/dim]")

                    # Display first few entities from each category
                    console.print("\n[bold]Sample Entities:[/bold]")
                    for entity_type, entities in provenance.items():
                        if entities:
                            console.print(f"\n[cyan]{entity_type}:[/cyan]")
                            for entity in entities[:2]:
                                console.print(f"  • {entity.get('id', 'N/A')}")
                            if len(entities) > 2:
                                console.print(f"  [dim]... and {len(entities) - 2} more[/dim]")
            else:
                # Regular ID lookup
                results = client.get_record_by_id(collection_id=id)
                _display_results([results] if isinstance(results, dict) else results, output, format)
        else:
            # Validate linking flags require --id
            if get_biosample or get_study or trace_provenance:
                error_console.print("[red]Error:[/red] Linking operations (--get-biosample, --get-study, --trace-provenance) require --id")
                raise typer.Exit(1)

            # Parse filter to handle both YAML and JSON
            parsed_filter = ""
            if filter:
                try:
                    parsed_filter = parse_filter(filter)
                except ValueError as e:
                    error_console.print(f"[red]Invalid filter syntax:[/red] {e}")
                    raise typer.Exit(1)

            results = client.get_records(filter=parsed_filter, max_page_size=limit, all_pages=all_pages)
            _display_results(results, output, format)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def link(
    ids: list[str] = typer.Argument(..., help="One or more NMDC IDs to use as nexus points"),
    types: Optional[str] = typer.Option(None, "--types", "-t", help="Comma-separated list of types to filter (e.g., 'nmdc:Study,nmdc:DataObject')"),
    direction: str = typer.Option("both", "--direction", "-d", help="Filter by relationship direction: upstream, downstream, or both"),
    hydrate: bool = typer.Option(False, "--hydrate", help="Return full documents instead of slim id/type only"),
    limit: int = typer.Option(1000, "--limit", "-l", help="Maximum results per page"),
    group_by_type: bool = typer.Option(True, "--group-by-type", help="Group results by entity type"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON/CSV/TSV)"),
    format: str = format_option,
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Generic interface for finding linked/related NMDC objects.

    This command performs transitive graph traversal to find all objects linked
    to the specified nexus IDs, both upstream (provenance) and downstream (derived data).

    Examples:

    \b
        # Find all data objects linked to a biosample
        nmdc link nmdc:bsm-11-x5xj6p33 --types nmdc:DataObject

    \b
        # Find studies and biosamples for multiple IDs
        nmdc link nmdc:dobj-11-abc123 nmdc:dobj-11-def456 --types nmdc:Study,nmdc:Biosample

    \b
        # Get only upstream entities (provenance)
        nmdc link nmdc:dobj-11-abc123 --direction upstream --hydrate

    \b
        # Explore all relationships (no type filter)
        nmdc link nmdc:bsm-11-x5xj6p33 --group-by-type
    """
    setup_logging(verbose)
    client = LinkedInstancesSearch(env=env)

    try:
        # Parse types if provided
        type_list = None
        if types:
            type_list = [t.strip() for t in types.split(",")]

        # Get linked instances
        with console.status(f"[bold green]Finding linked instances for {len(ids)} ID(s)..."):
            if direction == "both":
                results = client.get_linked_instances(
                    ids=ids,
                    types=type_list,
                    hydrate=hydrate,
                    max_page_size=limit,
                    all_pages=True
                )
            else:
                results_dict = client.get_linked_by_direction(
                    ids=ids,
                    types=type_list,
                    direction=direction,
                    hydrate=hydrate,
                    max_page_size=limit
                )
                # Extract the relevant direction
                results = results_dict.get(direction, [])

        console.print(f"\n[green]Found {len(results)} linked instance(s)[/green]")

        if group_by_type and results:
            # Group results by type
            grouped = {}
            for item in results:
                item_type = item.get("type", "Unknown")
                if item_type not in grouped:
                    grouped[item_type] = []
                grouped[item_type].append(item)

            # Display summary
            console.print("\n[bold]Results by Type:[/bold]")
            for entity_type in sorted(grouped.keys()):
                count = len(grouped[entity_type])
                console.print(f"  [cyan]{entity_type}:[/cyan] {count}")

            # Save or display
            if output:
                output_abs = output.resolve()
                with open(output_abs, "w") as f:
                    json.dump(grouped, f, indent=2)
                console.print(f"\n[green]✓[/green] Saved grouped results to {output_abs}")
            else:
                console.print("\n[bold]Sample Entities:[/bold]")
                for entity_type in sorted(grouped.keys()):
                    console.print(f"\n[cyan]{entity_type}:[/cyan]")
                    for entity in grouped[entity_type][:3]:
                        console.print(f"  • {entity.get('id', 'N/A')}")
                    if len(grouped[entity_type]) > 3:
                        console.print(f"  [dim]... and {len(grouped[entity_type]) - 3} more[/dim]")
                console.print("\n[dim]Tip: Use --output to save complete results to a file[/dim]")
        else:
            # Display as flat list
            _display_results(results, output, format)

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def dump_study(
    study_id: str = typer.Argument(..., help="NMDC study ID"),
    output: Path = typer.Argument(..., help="Output directory path"),
    download_data: bool = typer.Option(False, "--download-data", "-d", help="Download actual data files (not just metadata)"),
    include_types: Optional[str] = typer.Option(None, "--include-types", "-t", help="Comma-separated list of data object types to download (e.g., 'Metagenome Raw Reads,Assembly')"),
    max_size: Optional[int] = typer.Option(None, "--max-size", "-s", help="Skip downloading files larger than this size in MB"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--overwrite", help="Skip files that already exist"),
    preprocess: bool = typer.Option(True, "--preprocess/--no-preprocess", help="Preprocess downloaded files (e.g., add headers to TSV files)"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Dump complete study data to a folder structure.

    Creates a folder with:
    - study.json: Study metadata
    - manifest.json: Summary of what was dumped
    - One folder per biosample with metadata and data objects

    By default, only metadata is saved. Use --download-data to download actual data files.

    Examples:

    \b
        # Dump metadata only
        nmdc dump-study nmdc:sty-11-547rwq94 ./my_study

    \b
        # Download all data files (careful - can be huge!)
        nmdc dump-study nmdc:sty-11-547rwq94 ./my_study --download-data

    \b
        # Download only specific data types, with size limit
        nmdc dump-study nmdc:sty-11-547rwq94 ./my_study \\
          --download-data \\
          --include-types "Metagenome Raw Reads,Assembly" \\
          --max-size 1000
    """
    setup_logging(verbose)

    try:
        # Parse include_types
        include_types_list = None
        if include_types:
            include_types_list = [t.strip() for t in include_types.split(",")]

        # Resolve output path to absolute path relative to current working directory
        # This ensures relative paths work correctly regardless of where the command is run
        output_abs = output.resolve()

        # Create dumper
        dumper = StudyDumper(study_id, output_abs, env=env)

        # Progress callback
        def progress_callback(message: str, current: int, total: int):
            console.print(f"[cyan]{message}[/cyan] ({current}/{total})")

        # Start dump
        console.print(f"\n[bold]Dumping study {study_id} to {output}[/bold]\n")

        manifest = dumper.dump_study(
            download_data=download_data,
            include_types=include_types_list,
            max_size_mb=max_size,
            skip_existing=skip_existing,
            preprocess=preprocess,
            progress_callback=progress_callback
        )

        # Display summary
        stats = manifest["statistics"]
        console.print("\n[bold green]✓ Dump Complete![/bold green]\n")
        console.print(f"  Study: [cyan]{manifest['study_title']}[/cyan]")
        console.print(f"  Location: [cyan]{manifest['dump_location']}[/cyan]")
        console.print(f"  Biosamples: [green]{stats['biosamples']}[/green]")
        console.print(f"  Data Objects: [green]{stats['data_objects']}[/green]")

        if download_data:
            console.print(f"  Files Downloaded: [green]{stats['files_downloaded']}[/green]")
            console.print(f"  Total Size: [green]{stats['download_size_mb']} MB[/green]")

            if preprocess and "preprocessing" in manifest:
                preprocessing = manifest["preprocessing"]
                if preprocessing["files_processed"] > 0:
                    console.print(f"  Files Preprocessed: [green]{preprocessing['files_processed']}[/green]")

        if manifest["errors"]:
            console.print(f"\n[yellow]⚠ {len(manifest['errors'])} error(s) occurred:[/yellow]")
            for error in manifest["errors"][:5]:
                console.print(f"  [yellow]• {error}[/yellow]")
            if len(manifest["errors"]) > 5:
                console.print(f"  [yellow]... and {len(manifest['errors']) - 5} more (see manifest.json)[/yellow]")

        console.print(f"\nManifest saved to: [cyan]{output}/manifest.json[/cyan]")

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def collection_name(
    id: str = typer.Argument(..., help="NMDC ID to look up"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Get the collection name for a given NMDC ID.

    Example:

    \b
        nmdc collection-name nmdc:bsm-13-amrnys72
    """
    setup_logging(verbose)
    helper = CollectionHelpers(env=env)

    try:
        collection = helper.get_record_name_from_id(id)
        console.print(f"[green]{id}[/green] → [cyan]{collection}[/cyan]")
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def validate(
    file: Path = typer.Argument(..., help="JSON file to validate", exists=True),
    env: str = env_option,
):
    """
    Validate a JSON metadata file against NMDC schema.

    Requires authentication via CLIENT_ID and CLIENT_SECRET environment variables.

    Example:

    \b
        nmdc validate metadata.json
    """
    import os

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        error_console.print(
            "[red]Error:[/red] Authentication required. Set CLIENT_ID and CLIENT_SECRET environment variables."
        )
        raise typer.Exit(1)

    auth = NMDCAuth(client_id=client_id, client_secret=client_secret, env=env)
    metadata_client = Metadata(env=env, auth=auth)

    try:
        with console.status(f"[bold green]Validating {file}..."):
            status = metadata_client.validate_json(str(file))

        if status == 200:
            console.print(f"[green]✓[/green] Validation successful! Status: {status}")
        else:
            console.print(f"[yellow]![/yellow] Validation returned status: {status}")
    except Exception as e:
        error_console.print(f"[red]✗ Validation failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def mint(
    nmdc_type: str = typer.Argument(..., help="NMDC type (e.g., 'nmdc:Biosample', 'nmdc:DataObject')"),
    count: int = typer.Option(1, "--count", "-c", help="Number of IDs to mint"),
    env: str = env_option,
):
    """
    Mint new NMDC identifiers.

    Requires authentication via CLIENT_ID and CLIENT_SECRET environment variables.

    Examples:

    \b
        # Mint a single biosample ID
        nmdc mint nmdc:Biosample

    \b
        # Mint 10 data object IDs
        nmdc mint nmdc:DataObject --count 10
    """
    import os

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if not client_id or not client_secret:
        error_console.print(
            "[red]Error:[/red] Authentication required. Set CLIENT_ID and CLIENT_SECRET environment variables."
        )
        raise typer.Exit(1)

    auth = NMDCAuth(client_id=client_id, client_secret=client_secret, env=env)
    minter_client = Minter(env=env, auth=auth)

    try:
        with console.status(f"[bold green]Minting {count} {nmdc_type} ID(s)..."):
            result = minter_client.mint(nmdc_type=nmdc_type, count=count)

        if count == 1:
            console.print(f"[green]✓[/green] Minted ID: [cyan]{result}[/cyan]")
        else:
            console.print(f"[green]✓[/green] Minted {len(result)} IDs:")
            for id in result:
                console.print(f"  [cyan]{id}[/cyan]")
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def list_preprocessors():
    """
    List all available file preprocessors with metadata.

    Shows preprocessor aliases, CV terms, and expected file patterns.
    """
    from nmdc_api_utilities.preprocessors import get_registry

    registry = get_registry()

    console.print(f"\n[bold]Available Preprocessors ({len(registry.preprocessors)})[/bold]\n")

    for preprocessor in registry.preprocessors:
        console.print(f"[bold cyan]{preprocessor.alias}[/bold cyan]")
        console.print(f"  CV Term: {preprocessor.cv_term}")
        console.print(f"  Patterns: {', '.join(preprocessor.expected_prefixes)}")
        console.print(f"  {preprocessor.get_description()}")
        console.print()


@app.command()
def sniff_study(
    study_id: str = typer.Argument(..., help="NMDC study ID"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Preview preprocessable files in a study without downloading.

    Shows what files would be preprocessed, grouped by type.

    Examples:

    \b
        # Preview preprocessable files
        nmdc sniff-study nmdc:sty-11-547rwq94

    \b
        # Save results to JSON
        nmdc sniff-study nmdc:sty-11-547rwq94 --output sniff_results.json
    """
    setup_logging(verbose)
    from nmdc_api_utilities.study_dumper import StudyDumper

    try:
        dumper = StudyDumper(study_id, "./temp", env=env)

        with console.status("[bold green]Analyzing study files..."):
            results = dumper.sniff_preprocessable_files()

        # Display results
        console.print(f"\n[bold]Study:[/bold] {results['study_title']}")
        console.print(f"[bold]Study ID:[/bold] {results['study_id']}")
        console.print(f"[bold]Biosamples:[/bold] {results['total_biosamples']}")
        console.print(f"[bold]Preprocessable Files:[/bold] {results['total_preprocessable_files']}\n")

        if results['by_preprocessor']:
            console.print("[bold]Files by Preprocessor Type:[/bold]\n")

            for alias, info in results['by_preprocessor'].items():
                console.print(f"[bold cyan]{alias}[/bold cyan] - {info['cv_term']}")
                console.print(f"  Files: {len(info['files'])}")

                if info['files']:
                    console.print(f"  Examples:")
                    for file_info in info['files'][:3]:
                        size_str = f" ({file_info['file_size_mb']} MB)" if file_info['file_size_mb'] else ""
                        console.print(f"    • {file_info['filename']}{size_str}")

                    if len(info['files']) > 3:
                        console.print(f"    ... and {len(info['files']) - 3} more")

                console.print()
        else:
            console.print("[yellow]No preprocessable files found in this study.[/yellow]")

        # Save to file if requested
        if output:
            import json
            output_abs = output.resolve()
            with open(output_abs, 'w') as f:
                json.dump(results, f, indent=2)
            console.print(f"[green]✓[/green] Results saved to {output_abs}")

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def cache_links(
    ids: list[str] = typer.Argument(..., help="One or more NMDC IDs to cache links for"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Cache relationship links for NMDC objects.

    This fetches links from the API and stores them in a local DuckDB cache
    for fast subsequent queries. Only relationships are cached, not full objects.

    Examples:

    \b
        # Cache links for a biosample
        nmdc cache-links nmdc:bsm-11-x5xj6p33

    \b
        # Cache links for multiple IDs
        nmdc cache-links nmdc:bsm-11-x5xj6p33 nmdc:bsm-11-abc123

    \b
        # Cache links for all biosamples in a study (combine with xargs)
        nmdc biosample --filter 'associated_studies: nmdc:sty-11-34xj1150' -o temp.json
        jq -r '.[].id' temp.json | xargs nmdc cache-links
    """
    setup_logging(verbose)

    from nmdc_api_utilities.link_cache import LinkCache
    from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

    try:
        cache = LinkCache()
        client = LinkedInstancesSearch(env=env)

        total_links = 0

        for entity_id in ids:
            with console.status(f"[bold green]Fetching links for {entity_id}..."):
                # Fetch from API
                results = client.get_linked_instances(
                    ids=[entity_id],
                    hydrate=False,
                    max_page_size=1000,
                    all_pages=True
                )

                # Cache the links
                link_count = cache.cache_from_linked_instances(results, entity_id)
                total_links += link_count

                console.print(f"[green]✓[/green] Cached {link_count} links for {entity_id}")

        cache.close()

        console.print(f"\n[bold green]Total: {total_links} links cached[/bold green]")

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def query_links(
    id: str = typer.Argument(..., help="NMDC ID to query"),
    direction: str = typer.Option("both", "--direction", "-d", help="Direction: both, outgoing, or incoming"),
    relationship_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by relationship type"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON)"),
    verbose: int = verbose_option,
):
    """
    Query cached links for an NMDC object.

    Fast local lookups from the link cache. Run 'nmdc cache-links' first to populate cache.

    Examples:

    \b
        # Get all links for a biosample
        nmdc query-links nmdc:bsm-11-x5xj6p33

    \b
        # Get only downstream links
        nmdc query-links nmdc:bsm-11-x5xj6p33 --direction outgoing

    \b
        # Get only specific relationship type
        nmdc query-links nmdc:bsm-11-x5xj6p33 --type part_of
    """
    setup_logging(verbose)

    from nmdc_api_utilities.link_cache import LinkCache

    try:
        cache = LinkCache()
        links = cache.get_links_for_id(id, direction=direction, relationship_type=relationship_type)

        if not links:
            console.print(f"[yellow]No cached links found for {id}[/yellow]")
            console.print("[dim]Run 'nmdc cache-links' to populate cache[/dim]")
            return

        if output:
            import json
            output_abs = output.resolve()
            with open(output_abs, 'w') as f:
                json.dump(links, f, indent=2, default=str)
            console.print(f"[green]✓[/green] Saved {len(links)} links to {output_abs}")
        else:
            # Display to console
            console.print(f"\n[bold]Found {len(links)} cached link(s)[/bold]\n")

            # Group by relationship type
            from collections import defaultdict
            by_type = defaultdict(list)
            for link in links:
                by_type[link['relationship_type']].append(link)

            for rel_type, type_links in sorted(by_type.items()):
                console.print(f"[bold cyan]{rel_type}[/bold cyan] ({len(type_links)} links)")
                for link in type_links[:5]:  # Show first 5
                    console.print(f"  {link['source_id']} → {link['target_id']}")
                if len(type_links) > 5:
                    console.print(f"  [dim]... and {len(type_links) - 5} more[/dim]")
                console.print()

        cache.close()

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def cache_stats(
    verbose: int = verbose_option,
):
    """
    Show link cache statistics.

    Displays information about cached links, including total count,
    relationship types, and last sync times.

    Examples:

    \b
        # Show cache statistics
        nmdc cache-stats
    """
    setup_logging(verbose)

    from nmdc_api_utilities.link_cache import LinkCache

    try:
        cache = LinkCache()
        stats = cache.get_stats()

        console.print("\n[bold]Link Cache Statistics[/bold]\n")
        console.print(f"  Cache Location: [cyan]{stats['cache_path']}[/cyan]")
        console.print(f"  Total Links: [green]{stats['total_links']:,}[/green]")
        console.print(f"  Entities Cached: [green]{stats['total_entities_cached']:,}[/green]")

        if stats['oldest_sync']:
            console.print(f"  Oldest Sync: {stats['oldest_sync']}")
        if stats['newest_sync']:
            console.print(f"  Newest Sync: {stats['newest_sync']}")

        if stats['relationship_types']:
            console.print("\n[bold]Links by Relationship Type:[/bold]\n")
            for rel_type, count in sorted(stats['relationship_types'].items(), key=lambda x: -x[1]):
                console.print(f"  {rel_type}: [cyan]{count:,}[/cyan]")

        console.print()

        cache.close()

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def cache_clear(
    id: Optional[str] = typer.Option(None, "--id", help="Clear cache for specific ID only"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    verbose: int = verbose_option,
):
    """
    Clear the link cache.

    Examples:

    \b
        # Clear cache for specific ID
        nmdc cache-clear --id nmdc:bsm-11-x5xj6p33

    \b
        # Clear entire cache (with confirmation)
        nmdc cache-clear

    \b
        # Clear entire cache (skip confirmation)
        nmdc cache-clear --yes
    """
    setup_logging(verbose)

    from nmdc_api_utilities.link_cache import LinkCache

    try:
        if not id and not confirm:
            response = typer.confirm("This will clear the entire link cache. Continue?")
            if not response:
                console.print("[yellow]Cancelled[/yellow]")
                return

        cache = LinkCache()

        if id:
            cache.clear_cache(entity_id=id)
            console.print(f"[green]✓[/green] Cleared cache for {id}")
        else:
            cache.clear_cache()
            console.print(f"[green]✓[/green] Cleared entire link cache")

        cache.close()

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _display_results(results: list, output: Optional[Path] = None, format: str = 'auto'):
    """
    Display or save results.

    Automatically detects format from file extension, or uses explicit format:
    - .json: JSON format (default)
    - .csv: CSV format with flattened columns
    - .tsv/.tab: TSV format with flattened columns

    Args:
        results: List of result dictionaries
        output: Output file path (optional)
        format: Output format ('auto', 'json', 'csv', 'tsv')
    """
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    if output:
        # Resolve to absolute path relative to current working directory
        output_abs = output.resolve()

        # Export with specified or auto-detected format
        format_used = export_records(results, output_abs, format=format, flatten=True)

        if format_used in ('csv', 'tsv'):
            console.print(f"[green]✓[/green] Saved {len(results)} record(s) to {output_abs} ({format_used.upper()} format, flattened)")
        else:
            console.print(f"[green]✓[/green] Saved {len(results)} record(s) to {output_abs}")
    else:
        # Display to console
        console.print(f"\n[bold]Found {len(results)} record(s)[/bold]\n")

        # Show first few records as pretty JSON
        display_count = min(3, len(results))
        for i, record in enumerate(results[:display_count]):
            if i > 0:
                console.print("\n" + "─" * 80 + "\n")
            console.print(JSON(json.dumps(record, indent=2)))

        if len(results) > display_count:
            console.print(f"\n[dim]... and {len(results) - display_count} more record(s)[/dim]")
            console.print("[dim]Tip: Use --output with .json, .csv, or .tsv extension (or --format) to save results[/dim]")


# ============================================================================
# Functional Search Commands
# ============================================================================

@app.command(name="search-by-function")
def search_by_function(
    function_ids: list[str] = typer.Argument(
        ...,
        help="Function IDs to search (e.g., PFAM:PF00005, KEGG.ORTHOLOGY:K00001, or PF00005, K00001)"
    ),
    limit: int = typer.Option(100, "--limit", "-l", help="Maximum biosamples to return"),
    require_all: bool = typer.Option(
        True,
        "--require-all/--any",
        help="Require ALL functions (AND) or ANY function (OR)"
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON/CSV/TSV)"),
    format: str = format_option,
    show_activities: bool = typer.Option(False, "--show-activities", help="Show omics processing activities"),
    env: str = env_option,
    verbose: int = verbose_option,
):
    """
    Search for biosamples by functional annotations (PFAM, KEGG, COG, GO).

    This command uses a specialized NMDC endpoint that can find biosamples
    containing specific functional annotations. Function IDs can be provided
    with or without prefixes.

    Supported function types:
    - PFAM domains: PF00005 or PFAM:PF00005
    - KEGG Orthology: K00001 or KEGG.ORTHOLOGY:K00001
    - COG: COG0001 or COG:COG0001
    - Gene Ontology: GO0000001 or GO:GO0000001

    Examples:

    \b
        # Find biosamples with a specific PFAM domain
        nmdc search-by-function PFAM:PF00005 --limit 10

    \b
        # Search without prefix (auto-detected)
        nmdc search-by-function PF00005 --limit 10

    \b
        # Find biosamples with BOTH PFAMs (AND logic)
        nmdc search-by-function PF00005 PF00072 --require-all

    \b
        # Find biosamples with EITHER PFAM (OR logic)
        nmdc search-by-function PF00005 PF00072 --any

    \b
        # Mix different annotation types
        nmdc search-by-function PFAM:PF00005 KEGG.ORTHOLOGY:K00001 --limit 50

    \b
        # Save results to JSON with omics activities
        nmdc search-by-function PF00005 --show-activities -o results.json

    \b
        # Export to CSV (flattened structure)
        nmdc search-by-function PF00005 PF00072 -o results.csv
    """
    setup_logging(verbose)
    client = FunctionalBiosampleSearch(env=env)

    try:
        logic = "AND" if require_all else "OR"

        with console.status(f"[bold green]Searching for biosamples with {logic} logic..."):
            results = client.search_by_functions(
                function_ids=function_ids,
                limit=limit,
                logic=logic
            )

        # Extract results
        count = results.get("count", 0)
        biosamples = results.get("results", [])
        search_criteria = results.get("search_criteria", {})

        # Display summary
        console.print(f"\n[green]Found {count} biosample(s) matching criteria[/green]")
        console.print(f"[cyan]Function IDs:[/cyan] {', '.join(search_criteria.get('function_ids', []))}")
        console.print(f"[cyan]Logic:[/cyan] {search_criteria.get('logic', 'AND')}")
        console.print(f"[cyan]Returned:[/cyan] {len(biosamples)} biosample(s)\n")

        if not biosamples:
            console.print("[yellow]No biosamples found matching the criteria.[/yellow]")
            console.print("[dim]Try adjusting your function IDs or using --any for OR logic[/dim]")
            return

        # Display sample information
        if not output:
            # Create summary table
            table = Table(
                title=f"Biosamples with {', '.join(function_ids)}",
                show_header=True,
                header_style="bold cyan"
            )
            table.add_column("Biosample ID", style="cyan", max_width=30)
            table.add_column("Study ID", style="yellow", max_width=30)
            table.add_column("Activities", justify="right", style="green")
            table.add_column("Data Objects", justify="right", style="magenta")

            display_count = min(20, len(biosamples))
            for biosample in biosamples[:display_count]:
                biosample_id = biosample.get("id", "N/A")
                study_id = biosample.get("study_id", "N/A")

                # Count activities and data objects
                activity_count = 0
                data_object_count = 0

                for omics in biosample.get("omics_processing", []):
                    for omics_data in omics.get("omics_data", []):
                        activity_count += 1
                        data_object_count += len(omics_data.get("outputs", []))

                table.add_row(
                    biosample_id,
                    study_id,
                    str(activity_count),
                    str(data_object_count)
                )

            console.print(table)

            if len(biosamples) > display_count:
                console.print(f"\n[dim]... showing first {display_count} of {len(biosamples)} biosamples[/dim]")
                console.print("[dim]Use --output to save all results[/dim]")

            # Show detailed activity info if requested
            if show_activities and biosamples:
                console.print("\n[bold cyan]Omics Processing Activities:[/bold cyan]\n")
                for biosample in biosamples[:5]:  # Show activities for first 5
                    console.print(f"[bold]{biosample.get('id', 'N/A')}[/bold]")

                    for omics in biosample.get("omics_processing", []):
                        for omics_data in omics.get("omics_data", []):
                            activity_id = omics_data.get("id", "N/A")
                            activity_type = omics_data.get("type", "N/A")
                            output_count = len(omics_data.get("outputs", []))

                            console.print(f"  • {activity_type}")
                            console.print(f"    ID: {activity_id}")
                            console.print(f"    Outputs: {output_count} file(s)")

                    console.print()

                if len(biosamples) > 5:
                    console.print(f"[dim]... showing activities for first 5 of {len(biosamples)} biosamples[/dim]")

        # Save to file if requested
        if output:
            _display_results(biosamples, output, format)

    except ValueError as e:
        error_console.print(f"[red]Invalid input:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        if verbose >= 2:
            raise
        raise typer.Exit(1)


# ============================================================================
# GFF Commands
# ============================================================================

gff_app = typer.Typer(
    name="gff",
    help="GFF file utilities for functional annotations",
    add_completion=False,
)
app.add_typer(gff_app, name="gff")


@gff_app.command(name="query")
def gff_query(
    gff_file: Path = typer.Argument(..., help="Path to GFF file"),
    ec: Optional[str] = typer.Option(None, "--ec", help="Query by EC number pattern (e.g., '2.7.%')"),
    pfam: Optional[str] = typer.Option(None, "--pfam", help="Query by PFAM domain ID (e.g., 'PF00005')"),
    cog: Optional[str] = typer.Option(None, "--cog", help="Query by COG ID (e.g., 'COG0001')"),
    ko: Optional[str] = typer.Option(None, "--ko", help="Query by KEGG Orthology ID (e.g., 'K00001')"),
    region: Optional[str] = typer.Option(None, "--region", help="Query by region (format: 'seqid:start-end')"),
    feature_type: Optional[str] = typer.Option(None, "--type", help="Filter by feature type (e.g., 'CDS', 'tRNA')"),
    sql: Optional[str] = typer.Option(None, "--sql", help="Custom SQL query"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (TSV)"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit number of results"),
    use_duckdb: bool = typer.Option(True, "--duckdb/--no-duckdb", help="Use DuckDB for queries"),
    verbose: int = verbose_option,
):
    """
    Query features from a GFF file by annotation or location.

    Examples:

    \b
        # Find all kinases (EC 2.7.x.x)
        nmdc gff query annotations.gff --ec "2.7."

    \b
        # Find ABC transporters
        nmdc gff query annotations.gff --pfam PF00005

    \b
        # Query a genomic region
        nmdc gff query annotations.gff --region "contig_1:1000-5000"

    \b
        # Custom SQL query
        nmdc gff query annotations.gff --sql "SELECT * FROM features WHERE strand = '+' LIMIT 10"

    \b
        # Save results to file
        nmdc gff query annotations.gff --ec "2.7.%" --output kinases.tsv
    """
    setup_logging(verbose)

    try:
        from nmdc_api_utilities.gff_utils import load_gff

        if not gff_file.exists():
            error_console.print(f"[red]Error:[/red] GFF file not found: {gff_file}")
            raise typer.Exit(1)

        # Count query options
        query_count = sum([ec is not None, pfam is not None, cog is not None,
                          ko is not None, region is not None, sql is not None])

        if query_count == 0:
            error_console.print("[red]Error:[/red] Must specify at least one query option (--ec, --pfam, --cog, --ko, --region, --sql)")
            raise typer.Exit(1)

        if query_count > 1 and sql is None:
            error_console.print("[yellow]Warning:[/yellow] Multiple query options specified. Using first one.")

        # Load GFF
        console.print(f"[cyan]Loading GFF file:[/cyan] {gff_file}")
        reader = load_gff(gff_file, use_duckdb=use_duckdb)

        # Execute query
        if sql:
            results = reader.query(sql)
        elif ec:
            results = reader.query_by_ec(ec)
        elif pfam:
            results = reader.query_by_pfam(pfam)
        elif cog:
            results = reader.query_by_cog(cog)
        elif ko:
            results = reader.query_by_ko(ko)
        elif region:
            # Parse region format: seqid:start-end
            # Use rsplit to handle NMDC IDs with colons (e.g., nmdc:wfmgan-11-ddkkwt71.1_000010:2253-2500)
            if ":" not in region or "-" not in region:
                error_console.print("[red]Error:[/red] Invalid region format. Use 'seqid:start-end'")
                raise typer.Exit(1)
            seqid, coords = region.rsplit(":", 1)
            start, end = coords.split("-", 1)
            results = reader.query_region(seqid, int(start), int(end), feature_type=feature_type)

        # Apply limit
        if limit:
            results = results.head(limit)

        # Output results
        if output:
            results.to_csv(output, sep="\t", index=False)
            console.print(f"[green]✓[/green] Saved {len(results)} features to {output}")
        else:
            # Display summary
            console.print(f"\n[green]Found {len(results)} features[/green]\n")

            if len(results) > 0:
                # Create table for display
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("ID", style="dim", max_width=50)
                table.add_column("Product", max_width=60)
                table.add_column("EC", style="yellow", max_width=20)
                table.add_column("PFAM", style="magenta", max_width=20)
                # Split location into 3 columns to avoid truncation
                table.add_column("Sequence ID", style="cyan", max_width=50)
                table.add_column("Start", style="green", justify="right")
                table.add_column("End", style="green", justify="right")

                # Import pandas for NA handling
                import pandas as pd

                for _, row in results.head(20).iterrows():
                    # Handle NA values properly
                    ec_val = row.get("ec_number", "")
                    ec_str = str(ec_val)[:20] if pd.notna(ec_val) and ec_val else ""

                    pfam_val = row.get("pfam", "")
                    pfam_str = str(pfam_val)[:20] if pd.notna(pfam_val) and pfam_val else ""

                    table.add_row(
                        str(row.get("ID", ""))[:50],
                        str(row.get("product", ""))[:60],
                        ec_str,
                        pfam_str,
                        str(row.get("seqid", ""))[:50],
                        str(row.get("start", "")),
                        str(row.get("end", ""))
                    )

                console.print(table)

                if len(results) > 20:
                    console.print(f"\n[dim]... showing first 20 of {len(results)} results[/dim]")
                    console.print(f"[dim]Use --output to save all results[/dim]")

        reader.close()

    except ImportError:
        error_console.print("[red]Error:[/red] GFF utilities not available. Install with: uv sync --extra gff")
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        if verbose >= 2:
            raise
        raise typer.Exit(1)


@gff_app.command(name="stats")
def gff_stats(
    gff_file: Path = typer.Argument(..., help="Path to GFF file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON)"),
    use_duckdb: bool = typer.Option(True, "--duckdb/--no-duckdb", help="Use DuckDB for loading"),
    verbose: int = verbose_option,
):
    """
    Get summary statistics for a GFF file.

    Examples:

    \b
        # Display statistics
        nmdc gff stats annotations.gff

    \b
        # Save statistics to JSON
        nmdc gff stats annotations.gff --output stats.json
    """
    setup_logging(verbose)

    try:
        from nmdc_api_utilities.gff_utils import load_gff

        if not gff_file.exists():
            error_console.print(f"[red]Error:[/red] GFF file not found: {gff_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading GFF file:[/cyan] {gff_file}")
        reader = load_gff(gff_file, use_duckdb=use_duckdb)

        stats = reader.get_summary_stats()

        if output:
            output_abs = output.resolve()
            with open(output_abs, 'w') as f:
                json.dump(stats, f, indent=2)
            console.print(f"[green]✓[/green] Saved statistics to {output_abs}")
        else:
            # Display formatted stats
            console.print(f"\n[bold cyan]GFF Summary Statistics[/bold cyan]")
            console.print(f"[cyan]File:[/cyan] {gff_file.name}\n")

            console.print(f"[bold]Total features:[/bold] {stats['total_features']:,}")
            console.print(f"[bold]Sequences:[/bold] {len(stats['sequences']):,}\n")

            # Feature types table
            table = Table(title="Feature Types", show_header=True, header_style="bold cyan")
            table.add_column("Type", style="cyan")
            table.add_column("Count", justify="right", style="yellow")
            table.add_column("Percentage", justify="right", style="dim")

            total = stats['total_features']
            for ftype, count in sorted(stats['feature_types'].items(), key=lambda x: x[1], reverse=True):
                pct = (count / total * 100) if total > 0 else 0
                table.add_row(ftype, f"{count:,}", f"{pct:.1f}%")

            console.print(table)

            # Annotation coverage
            console.print("\n[bold]Annotation Coverage:[/bold]")
            console.print(f"  EC numbers:  {stats['has_ec']:>8,} ({stats['has_ec']/total*100:>5.1f}%)")
            console.print(f"  PFAM:        {stats['has_pfam']:>8,} ({stats['has_pfam']/total*100:>5.1f}%)")
            console.print(f"  COG:         {stats['has_cog']:>8,} ({stats['has_cog']/total*100:>5.1f}%)")
            console.print(f"  KO:          {stats['has_ko']:>8,} ({stats['has_ko']/total*100:>5.1f}%)")

        reader.close()

    except ImportError:
        error_console.print("[red]Error:[/red] GFF utilities not available. Install with: uv sync --extra gff")
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        if verbose >= 2:
            raise
        raise typer.Exit(1)


@gff_app.command(name="find-bgc")
def gff_find_bgc(
    gff_file: Path = typer.Argument(..., help="Path to GFF file"),
    min_genes: int = typer.Option(5, "--min-genes", help="Minimum genes in a cluster"),
    max_distance: int = typer.Option(10000, "--max-distance", help="Maximum distance between genes (bp)"),
    require_annotations: Optional[str] = typer.Option(
        None,
        "--require-annotations",
        help="Comma-separated annotation types required (e.g., 'pfam,ec_number')"
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (JSON)"),
    use_duckdb: bool = typer.Option(True, "--duckdb/--no-duckdb", help="Use DuckDB for loading"),
    verbose: int = verbose_option,
):
    """
    Find biosynthetic gene cluster (BGC) candidates.

    Examples:

    \b
        # Find BGCs with default parameters
        nmdc gff find-bgc annotations.gff

    \b
        # Require specific annotations
        nmdc gff find-bgc annotations.gff --require-annotations "pfam,ec_number"

    \b
        # Custom parameters
        nmdc gff find-bgc annotations.gff --min-genes 4 --max-distance 5000

    \b
        # Save to file
        nmdc gff find-bgc annotations.gff --output bgcs.json
    """
    setup_logging(verbose)

    try:
        from nmdc_api_utilities.gff_utils import load_gff

        if not gff_file.exists():
            error_console.print(f"[red]Error:[/red] GFF file not found: {gff_file}")
            raise typer.Exit(1)

        required_annot = require_annotations.split(",") if require_annotations else None

        console.print(f"[cyan]Loading GFF file:[/cyan] {gff_file}")
        reader = load_gff(gff_file, use_duckdb=use_duckdb)

        console.print(f"[cyan]Finding BGC candidates...[/cyan]")
        bgcs = reader.find_bgc_candidates(
            min_genes=min_genes,
            max_distance=max_distance,
            required_annotations=required_annot
        )

        if output:
            output_abs = output.resolve()
            with open(output_abs, 'w') as f:
                json.dump(bgcs, f, indent=2)
            console.print(f"[green]✓[/green] Saved {len(bgcs)} BGC candidates to {output_abs}")
        else:
            console.print(f"\n[green]Found {len(bgcs)} BGC candidates[/green]\n")

            if len(bgcs) > 0:
                # Display table
                table = Table(title="BGC Candidates", show_header=True, header_style="bold cyan")
                table.add_column("#", style="dim", width=4)
                table.add_column("Location", style="cyan")
                table.add_column("Genes", justify="right", style="yellow")
                table.add_column("EC", justify="right", style="green")
                table.add_column("PFAM", justify="right", style="magenta")
                table.add_column("Size (bp)", justify="right", style="dim")

                for i, bgc in enumerate(bgcs[:20], 1):
                    ec_count = len([e for e in bgc['annotations']['ec_numbers'] if e])
                    pfam_count = len([p for p in bgc['annotations']['pfams'] if p])
                    size = bgc['end'] - bgc['start']

                    table.add_row(
                        str(i),
                        f"{bgc['seqid'][:30]}:{bgc['start']}-{bgc['end']}",
                        str(bgc['gene_count']),
                        str(ec_count),
                        str(pfam_count),
                        f"{size:,}"
                    )

                console.print(table)

                if len(bgcs) > 20:
                    console.print(f"\n[dim]... showing first 20 of {len(bgcs)} BGCs[/dim]")
                    console.print(f"[dim]Use --output to save all results[/dim]")

        reader.close()

    except ImportError:
        error_console.print("[red]Error:[/red] GFF utilities not available. Install with: uv sync --extra gff")
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        if verbose >= 2:
            raise
        raise typer.Exit(1)


@gff_app.command(name="export")
def gff_export(
    gff_file: Path = typer.Argument(..., help="Path to GFF file"),
    output: Path = typer.Argument(..., help="Output file path"),
    columns: Optional[str] = typer.Option(None, "--columns", help="Comma-separated column names to export"),
    use_duckdb: bool = typer.Option(True, "--duckdb/--no-duckdb", help="Use DuckDB for loading"),
    verbose: int = verbose_option,
):
    """
    Export GFF data to TSV format.

    Examples:

    \b
        # Export all columns
        nmdc gff export annotations.gff output.tsv

    \b
        # Export specific columns
        nmdc gff export annotations.gff output.tsv --columns "seqid,start,end,ec_number,pfam,product"
    """
    setup_logging(verbose)

    try:
        from nmdc_api_utilities.gff_utils import load_gff

        if not gff_file.exists():
            error_console.print(f"[red]Error:[/red] GFF file not found: {gff_file}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading GFF file:[/cyan] {gff_file}")
        reader = load_gff(gff_file, use_duckdb=use_duckdb)

        column_list = columns.split(",") if columns else None

        console.print(f"[cyan]Exporting to:[/cyan] {output}")
        reader.export_to_tsv(output, columns=column_list)

        console.print(f"[green]✓[/green] Exported {len(reader.df)} features to {output}")

        reader.close()

    except ImportError:
        error_console.print("[red]Error:[/red] GFF utilities not available. Install with: uv sync --extra gff")
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        if verbose >= 2:
            raise
        raise typer.Exit(1)


# ============================================================================
# Enrichment Commands
# ============================================================================

@app.command(name="enrich")
def enrich(
    study_dir: Path = typer.Argument(..., help="Path to study directory (from dump-study)"),
    group_by: str = typer.Option(..., "--group-by", help="Biosample property to group by (e.g., 'depth', 'ph', 'ecosystem_type')"),
    annotation_type: str = typer.Option("ec_number", "--annotation-type", help="Annotation type to analyze ('ec_number', 'pfam', 'cog', 'ko')"),
    threshold: Optional[float] = typer.Option(None, "--threshold", help="Threshold for splitting continuous variables (e.g., depth > 10)"),
    bins: Optional[int] = typer.Option(None, "--bins", help="Number of bins for continuous variables (2 for binary split)"),
    categories: Optional[str] = typer.Option(None, "--categories", help="Comma-separated categories for categorical variables"),
    method: str = typer.Option("fisher", "--method", help="Statistical test method ('fisher' or 'chi2')"),
    fdr_method: str = typer.Option("benjamini-hochberg", "--fdr-method", help="FDR correction method"),
    min_count: int = typer.Option(5, "--min-count", help="Minimum count required for testing"),
    alpha: float = typer.Option(0.05, "--alpha", help="Significance level for filtering results"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (TSV)"),
    output_format: str = typer.Option("tsv", "--format", help="Output format ('tsv', 'json', 'csv')"),
    verbose: int = verbose_option,
):
    """
    Perform enrichment analysis on functional annotations.

    Compare annotation abundances (EC numbers, PFAM, COG, KO) between groups of
    samples defined by biosample properties (depth, pH, ecosystem type, etc.).

    Examples:

    \b
        # Compare EC numbers between high and low depth samples
        nmdc enrich ./my_study --group-by depth --threshold 10.0 --annotation-type ec_number

    \b
        # Compare PFAM domains across ecosystem types
        nmdc enrich ./my_study --group-by ecosystem_type --categories "Soil,Marine" --annotation-type pfam

    \b
        # Split samples into 2 bins by pH
        nmdc enrich ./my_study --group-by ph --bins 2 --annotation-type ec_number

    \b
        # Save results to file
        nmdc enrich ./my_study --group-by depth --threshold 10.0 --output enrichment.tsv

    \b
        # Get JSON output with all details
        nmdc enrich ./my_study --group-by depth --threshold 10.0 --output enrichment.json --format json
    """
    setup_logging(verbose)

    try:
        from nmdc_api_utilities.enrichment import EnrichmentAnalyzer, load_samples_from_gff_and_biosamples

        if not study_dir.exists():
            error_console.print(f"[red]Error:[/red] Study directory not found: {study_dir}")
            raise typer.Exit(1)

        console.print(f"[cyan]Loading study data from:[/cyan] {study_dir}")

        # Find and aggregate biosample files
        # dump-study creates individual biosample.json files in each biosample directory
        biosample_files = list(study_dir.glob("nmdc_bsm-*/biosample.json"))
        if not biosample_files:
            error_console.print(f"[red]Error:[/red] No biosample.json files found in {study_dir}")
            error_console.print("[dim]Tip: Use 'nmdc dump-study' to download study data first[/dim]")
            raise typer.Exit(1)

        console.print(f"[cyan]Found {len(biosample_files)} biosample files[/cyan]")

        # Aggregate individual biosample files into a list
        biosamples = []
        for biosample_file in biosample_files:
            with open(biosample_file) as f:
                biosample = json.load(f)
                biosamples.append(biosample)

        # Find GFF files
        gff_files = {}
        for gff_path in study_dir.glob("**/data_objects/*_functional_annotation.gff"):
            # Try to extract biosample ID from path
            # Path structure: study_dir / biosample_id / data_objects / *.gff
            biosample_id = gff_path.parent.parent.name
            # Convert underscore to colon for NMDC ID format (nmdc_bsm -> nmdc:bsm)
            biosample_id = biosample_id.replace("nmdc_", "nmdc:")
            gff_files[biosample_id] = gff_path

        if not gff_files:
            error_console.print(f"[red]Error:[/red] No GFF files found in {study_dir}")
            error_console.print("[dim]Tip: Use 'nmdc dump-study --download-data' to download functional annotations[/dim]")
            raise typer.Exit(1)

        console.print(f"[cyan]Found {len(gff_files)} GFF files[/cyan]")

        # Load samples
        console.print(f"[cyan]Loading samples and annotations...[/cyan]")
        samples = load_samples_from_gff_and_biosamples(
            biosamples,  # Pass the aggregated list of biosamples
            gff_files,
            annotation_type=annotation_type
        )

        if len(samples) < 2:
            error_console.print(f"[red]Error:[/red] Need at least 2 samples, found {len(samples)}")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Loaded {len(samples)} samples")

        # Parse categories
        category_list = categories.split(",") if categories else None

        # Create analyzer
        analyzer = EnrichmentAnalyzer(
            method=method,
            fdr_method=fdr_method,
            min_count=min_count
        )

        # Run enrichment analysis
        console.print(f"[cyan]Running enrichment analysis...[/cyan]")
        console.print(f"  Group by: {group_by}")
        console.print(f"  Annotation type: {annotation_type}")
        console.print(f"  Statistical method: {method}")

        results = analyzer.analyze(
            samples,
            group_by=group_by,
            threshold=threshold,
            bins=bins,
            categories=category_list
        )

        # Filter by significance
        significant = [r for r in results if r.fdr < alpha]

        console.print(f"\n[green]Found {len(significant)} significant results (FDR < {alpha})[/green]")
        console.print(f"[dim]Total features tested: {len(results)}[/dim]\n")

        # Output results
        if output:
            # Resolve to absolute path relative to current working directory
            output_abs = output.resolve()
            analyzer.export_results(results, output_abs, format=output_format)
            console.print(f"[green]✓[/green] Saved results to {output_abs}")
        else:
            # Display top results
            if significant:
                table = Table(title=f"Top Enrichment Results (FDR < {alpha})", show_header=True, header_style="bold cyan")
                table.add_column("Feature", style="cyan", max_width=30)
                table.add_column(results[0].group1_name, justify="right", style="yellow")
                table.add_column(results[0].group2_name, justify="right", style="yellow")
                table.add_column("p-value", justify="right", style="magenta")
                table.add_column("FDR", justify="right", style="red")
                table.add_column("Fold Change", justify="right", style="green")
                table.add_column("Enriched In", style="bold")

                for r in significant[:20]:
                    table.add_row(
                        r.feature_id[:30],
                        f"{r.group1_count}/{r.group1_total}",
                        f"{r.group2_count}/{r.group2_total}",
                        f"{r.p_value:.2e}",
                        f"{r.fdr:.2e}",
                        f"{r.effect_size:.2f}x",
                        r.enriched_in.split(">")[0].strip() if ">" in r.enriched_in else r.enriched_in[:20]
                    )

                console.print(table)

                if len(significant) > 20:
                    console.print(f"\n[dim]... showing top 20 of {len(significant)} significant results[/dim]")
                    console.print(f"[dim]Use --output to save all results[/dim]")
            else:
                console.print("[yellow]No significant enrichment found[/yellow]")
                console.print("[dim]Try adjusting --alpha, --threshold, or --min-count[/dim]")

    except ImportError as e:
        if "scipy" in str(e) or "statsmodels" in str(e):
            error_console.print("[red]Error:[/red] Enrichment analysis requires additional packages.")
            error_console.print("Install with: [cyan]uv sync --extra enrich[/cyan]")
        else:
            error_console.print(f"[red]Import Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        if verbose >= 2:
            raise
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
