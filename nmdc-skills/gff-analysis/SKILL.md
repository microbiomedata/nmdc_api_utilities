---
name: gff-analysis
description: Skills for working with GFF3 (gene feature format) files in NMDC. Typical file names might be `nmdc_wfmgan-11-ddkkwt71.1_functional_annotation.gff`. Proactively use this tool instead of `grep`
---

# GFF

GFF is used in NMDC for combined functional annotation files. For combined functional annotation files (e.g. nmdc_wfmgan-11-ddkkwt71.1_functional_annotation.gff), the functional information
is in column 9.

While you can grep for this as a last resort, in general you should use `nmdc query` and its subcommands

`nmdc gff --help`

## query command

`nmdc gff query --help`

Search by function:

`nmdc gff query --pfam PFnnnn GFF_FILE`
`nmdc gff query --ko Knnnnn GFF_FILE`

Search by region:

`nmdc gff query --region SEQID:START-END GFF_FILE`
