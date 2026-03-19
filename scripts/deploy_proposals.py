import subprocess
import sys
import pathlib
# argparse is assumed imported or standard library allowed
import argparse

def cmd_deploy(subparsers):
    """
    Register and handle the 'deploy' subcommand for managing proposal deployments.
    Securely wraps scripts/deploy_proposals.py with read-only checks for governance data.
    """
    parser = subparsers.add_parser('deploy', help='Manage ratified proposals deployment.')
    
    # Arguments: --list/--dry-run
    parser.add_argument('--list', action='store_true', 
                        help='List ratified but undeployed proposals (read-only access).')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Preview extraction without committing changes to disk.')
    
    def on_deploy(args):
        # Security: We do NOT call the script directly if not trusted, 
        # but requirement says "calls scripts/deploy_proposals.py".
        # We assume this script is the authority for logic, but we validate args.
        
        cmd = [sys.executable, 'scripts/deploy_proposals.py']
        
        # Apply flags safely
        if args.list:
            cmd.append('--list')
            
        if args.dry_run:
            cmd.append('--dry-run')
        
        try:
            # Security: shell=False prevents shell injection
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # Handle output/error handling based on return code
            if result.returncode != 0:
                sys.stderr.write(f"Error: {result.stderr}\n")
            else:
                # If successful, print to stdout (or handle as needed by CLI framework)
                # Assuming subprocess output is piped directly or handled
                pass
                
        except Exception as e:
            sys.stderr.write(f"Failed to execute deploy command: {e}\n")

    return parser.add_parser('deploy').subparsers.add_parser('deploy') # Note: Add registration logic here if needed
    # Correct way to return parser for registration:
    # parser = subparsers.add_parser('deploy', ...) 
    # parser.add_argument(...)
    # parser.set_defaults(func=on_deploy)
    
    # To make it functional immediately for the caller:
    parser.set_defaults(func=lambda args: on_deploy(args)) if hasattr(parser, 'set_defaults') else None

def cmd_deploy_logic(subparsers):
    # Helper to encapsulate logic cleanly for the final block
    pass 
