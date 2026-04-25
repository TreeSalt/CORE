# MISSION: proposal_historian_v2
TYPE: IMPLEMENTATION
MISSION_ID: 03_ORCH_E16_004_proposal_historian_v2

## CONTEXT
P23 was deployed cleanly via Phase G surgical extraction. This is a
hardened v2 with reinforced brief.

## DELIVERABLE
File: scripts/proposal_historian.py

## INTERFACE CONTRACT
- Dataclass: ProposalRecord (frozen)
- Dataclass: ArchiveBundle (frozen)
- Function: scan_proposals(notes_dir: Path) -> list[ProposalRecord]
- Function: parse_iso_timestamp(timestamp_str: str) -> datetime
- Function: filter_by_cutoff(records, cutoff_iso) -> list[ProposalRecord]
- Function: group_by_epoch(records) -> dict[int, list[ProposalRecord]]
- Function: create_bundle(epoch, records, notes_dir, temp_dir) -> ArchiveBundle
- Function: write_index(bundles, output_path) -> None
- CLI entry point

## CONSTRAINTS
Pure stdlib + tarfile.
