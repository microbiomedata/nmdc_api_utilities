---
name: enrichment-analysis
description: Skills for performing functional enrichment analysis on GFF functional annotation and metabolomics files
---

# Command

`nmdc enrich --help`



## Full details

Usage: `nmdc enrich [OPTIONS] STUDY_DIR`

Perform enrichment analysis on functional annotations.

Compare annotation abundances (EC numbers, PFAM, COG, KO) between groups of samples defined by biosample properties (depth, pH, ecosystem type, etc.).

Assumes `nmdc dump-study` has been executed first.

Examples:

     # Compare EC numbers between high and low depth samples
     nmdc enrich ./my_study --group-by depth --threshold 10.0 --annotation-type ec_number

     # Compare PFAM domains across ecosystem types
     nmdc enrich ./my_study --group-by ecosystem_type --categories "Soil,Marine" --annotation-type pfam

     # Split samples into 2 bins by pH
     nmdc enrich ./my_study --group-by ph --bins 2 --annotation-type ec_number

     # Save results to file
     nmdc enrich ./my_study --group-by depth --threshold 10.0 --output enrichment.tsv

     # Get JSON output with all details
     nmdc enrich ./my_study --group-by depth --threshold 10.0 --output enrichment.json --format json

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    study_dir      PATH  Path to study directory (from dump-study) [required]                                                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --group-by                 TEXT     Biosample property to group by (e.g., 'depth', 'ph', 'ecosystem_type') [required]                                                                                           │
│    --annotation-type          TEXT     Annotation type to analyze ('ec_number', 'pfam', 'cog', 'ko') [default: ec_number]                                                                                          │
│    --threshold                FLOAT    Threshold for splitting continuous variables (e.g., depth > 10)                                                                                                             │
│    --bins                     INTEGER  Number of bins for continuous variables (2 for binary split)                                                                                                                │
│    --categories               TEXT     Comma-separated categories for categorical variables                                                                                                                        │
│    --method                   TEXT     Statistical test method ('fisher' or 'chi2') [default: fisher]                                                                                                              │
│    --fdr-method               TEXT     FDR correction method [default: benjamini-hochberg]                                                                                                                         │
│    --min-count                INTEGER  Minimum count required for testing [default: 5]                                                                                                                             │
│    --alpha                    FLOAT    Significance level for filtering results [default: 0.05]                                                                                                                    │
│    --output           -o      PATH     Output file (TSV)                                                                                                                                                           │
│    --format                   TEXT     Output format ('tsv', 'json', 'csv') [default: tsv]                                                                                                                         │
│    --verbose          -v      INTEGER  Increase verbosity: -v (INFO: show API URLs and timing), -vv (DEBUG: show full requests/responses), -vvv (DEBUG: show all library details) [default: 0]                     │
│    --help                              Show this message and exit.                                                                                                                                                 │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
