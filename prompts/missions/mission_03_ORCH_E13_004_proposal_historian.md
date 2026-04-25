# MISSION: Proposal Historian — Archival of Pre-Richmond Proposals
DOMAIN: 03_ORCHESTRATION
TASK: 03_ORCH_E13_004_proposal_historian
TYPE: IMPLEMENTATION
VERSION: 1.0

## CONTEXT
The repository currently holds 1,347 files in `08_IMPLEMENTATION_NOTES/`,
representing 65% of all files in the repo. Of these, approximately 503
proposals are from epochs E1 through E10 (pre-Richmond, before the
mantis_core rename). These historical proposals are no longer needed in
the active working tree but should be preserved as a record of the
factory's evolution.

This mission builds a historian tool that bundles old proposals into
compressed tarballs grouped by epoch, generates a searchable index, and
moves the bundles to an archive directory. The active working tree
keeps only proposals from E11 onwards.

The default cutoff date is 2026-03-21 (Richmond Genesis), but the cutoff
is configurable via CLI argument.

## EXACT IMPORTS:
```python
import os
import re
import json
import tarfile
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
```

## INTERFACE CONTRACT
The deliverable is `scripts/proposal_historian.py` containing both an
importable API and a CLI entry point.

### Dataclass: ProposalRecord
Frozen dataclass with these fields:
```
filename: str               # original filename
domain: str                 # extracted from filename pattern
timestamp: str              # extracted from filename pattern
size_bytes: int
inferred_epoch: Optional[int]   # parsed from content if possible
status: Optional[str]       # extracted from STATUS line in proposal
```

### Dataclass: ArchiveBundle
Frozen dataclass with these fields:
```
bundle_name: str            # e.g., "epoch_05_proposals.tar.gz"
proposal_count: int
total_size_bytes: int
created_at: str             # ISO UTC
proposals: List[ProposalRecord]
```

### Function: scan_proposals(notes_dir: Path) -> List[ProposalRecord]
Walks `notes_dir` non-recursively (only files, not subdirectories).
For each file matching the pattern `PROPOSAL_<DOMAIN>_<TIMESTAMP>.md`:
1. Parses the domain and timestamp from the filename
2. Reads the first 50 lines of the file to extract STATUS and inferred epoch
3. Constructs a ProposalRecord
Returns the list of records, sorted by timestamp ascending.

### Function: filter_by_cutoff(records: List[ProposalRecord], cutoff_iso: str) -> List[ProposalRecord]
Returns records whose timestamp is strictly older than the cutoff. The
cutoff is compared lexicographically (since timestamps are zero-padded
ISO format, lexicographic == chronological).

### Function: group_by_epoch(records: List[ProposalRecord]) -> Dict[str, List[ProposalRecord]]
Groups records into buckets keyed by inferred_epoch. Records with no
inferred_epoch go into a special "unknown_epoch" bucket. Returns a dict
with stable insertion order.

### Function: create_bundle(records: List[ProposalRecord], bundle_path: Path, source_dir: Path) -> ArchiveBundle
Creates a gzipped tarball at bundle_path containing all the files
referenced by the records (resolved relative to source_dir). Computes
total size and constructs an ArchiveBundle return value. Uses gzip
compression level 6 (default balance).

### Function: write_index(bundles: List[ArchiveBundle], index_path: Path) -> None
Serializes a list of ArchiveBundle objects to a JSON file at index_path.
The index allows querying which bundle contains a given proposal without
unpacking. Uses indent=2 for human readability.

### Function: archive_old_proposals(notes_dir: Path, archive_dir: Path, cutoff_iso: str, dry_run: bool = True) -> Dict
The orchestration function. Performs the full pipeline:
1. Scans notes_dir for proposals
2. Filters by cutoff
3. Groups by epoch
4. Creates archive_dir if it does not exist
5. For each epoch group, creates a bundle in archive_dir
6. Writes the index file at archive_dir/INDEX.json
7. If dry_run is False, deletes the original proposal files after
   successful bundling
8. Returns a summary dict with total counts and bytes saved

dry_run defaults to True for safety. Live deletion requires explicit
opt-in via dry_run=False.

### CLI Entry Point
When invoked with `python3 scripts/proposal_historian.py [scan|archive] [--cutoff DATE]`:
- `scan` performs read-only analysis and prints a JSON report
- `archive` performs the bundling but defaults to dry-run
- `archive --execute` performs the actual archival including deletion
- `--cutoff` accepts ISO date format, defaults to "20260321T000000Z"
- `--notes-dir` defaults to "08_IMPLEMENTATION_NOTES"
- `--archive-dir` defaults to "archive/historical_proposals"

Exit codes: 0 on success, 1 on error.

## DELIVERABLE
File: scripts/proposal_historian.py

## BEHAVIORAL REQUIREMENTS
- Idempotent: re-running scan does not modify any files
- Atomic: bundle creation must complete before any source files are deleted
- Defensive: if any bundle creation fails, no source files are deleted
- Verifiable: bundle integrity must be checked (gzip CRC) before deletion
- Timestamps must be timezone-aware UTC, ISO format
- Default behavior must be safe (dry-run)
- Logging via the standard logging module
- Index format: JSON, indented, deterministic key order

## TEST REQUIREMENTS
The corresponding test mission will verify:
1. scan_proposals correctly parses filename patterns
2. filter_by_cutoff respects the cutoff boundary (strict less-than)
3. group_by_epoch handles records with no epoch (unknown_epoch bucket)
4. create_bundle produces a valid gzipped tarball with all files
5. archive_old_proposals in dry-run mode does not delete any files
6. archive_old_proposals with execute=True deletes files only after
   bundle creation succeeds
7. write_index produces valid parseable JSON
8. CLI scan command exits 0 and prints JSON
9. CLI archive command without --execute does not modify the filesystem
10. Bundle gzip integrity check passes after creation

## CONSTRAINTS
- Pure stdlib (no external dependencies)
- Atomic operations only — partial archival must be impossible
- Default behavior must be read-only / dry-run
- Output valid Python only
