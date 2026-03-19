# Mission: core deploy — Extract Code from Ratified Proposals

## Domain
03_ORCHESTRATION

## Model Tier
Sprint (9b)

## Description
Build a deployment script that extracts Python code from ratified proposal markdown files
and writes them to their intended output paths.

CONTEXT: The factory generates proposals as markdown files with embedded code blocks.
After ratification, the Sovereign must manually extract the code. This script automates that.

REQUIREMENTS:
1. Scan 08_IMPLEMENTATION_NOTES/PROPOSAL_*.md for files with STATUS: RATIFIED
2. Extract Python code blocks (between triple backticks) from each proposal
3. Read the OUTPUT: line from the original mission file to determine target path
4. Write extracted code to the target path
5. Print summary: files deployed, paths written
6. Skip proposals already deployed (check if target file exists and matches)

ALLOWED IMPORTS: re, pathlib, json, sys, argparse
NO EXTERNAL DEPENDENCIES.
OUTPUT: scripts/deploy_proposals.py
TEST: Create a mock proposal with STATUS: RATIFIED and a code block. Run deploy. Assert output file created.
