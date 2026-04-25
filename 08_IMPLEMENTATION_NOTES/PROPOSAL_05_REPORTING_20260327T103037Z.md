---
DOMAIN: 05_REPORTING
MODEL: qwen3.5:4b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
#!/usr/bin/env python3

import pathlib
import re
import json


def get_all_proposals(notes_dir):
    """Scans 08_IMPLEMENTATION_NOTES for PROPOSAL_*.md files and extracts metadata."""
    proposals = []
    notes_path = pathlib.Path(notes_dir) / "08_IMPLEMENTATION_NOTES"
    
    if not notes_path.exists():
        return proposals
    
    # Find all PROPOSAL_*.md files
    proposal_files = list(notes_path.glob("PROPOSAL_*.md"))
    
    for file_path in proposal_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract domain (first occurrence of [domain] or "domain:")
        domain_match = re.search(r'\[domain\]\s*(.*?)^|\b(domain):?\s*(.*)$', content, re.IGNORECASE)
        if domain_match:
            domain = domain_match.group(1).strip().lower() if domain_match.group(1) else "uncategorized"
        else:
            # Try to find domain in text format
            domain_parts = re.findall(r'(?:\[|")?\s*domain(?:\s*:)?\s*[:\[]?([^,;\[\]]+)(?:[^,\[\]])?[,;])', content, re.IGNORECASE)
            if not domain_match:
                domain = "uncategorized"
        
        # Extract timestamp (ISO format typically at top of file)
        timestamp_match = re.search(r'Timestamp:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}|(\d{1,2}/\w{3}/\d{4}))', content)
        if timestamp_match:
            timestamp = timestamp_match.group(0).strip()[:25] if len(timestamp_match.group(0)) > 25 else "unknown"
        else:
            # Try date-only format
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
            if date_match:
                timestamp = f"{date_match.group(1)} T00:00:00"
            else:
                timestamp = "unknown"
        
        # Check for code blocks
        has_code_block = bool(re.search(r'```(?:\w+)?', content))
        
        # Extract deliverable path (typically mentions file paths)
        deliverable_match = re.search(r'(?:deliverable|deploy|artifact)[:]\s*(\S+)\s*$', content)
        deliverable_path = deliverable_match.group(1) if deliverable_match else None
        
        proposals.append({
            'domain': domain,
            'timestamp': timestamp,
            'has_code_block': has_code_block,
            'deliverable_path': deliverable_path
        })
    
    return proposals


def get_deployed_files(repo_root):
    """Walks domain directories and scripts/redteam for deployed .py files."""
    deployed = []
    repo_path = pathlib.Path(repo_root)
    
    if not repo_path.exists():
        return deployed
    
    # List directories to walk (domain dirs and scripts/redteam)
    domains_to_check = ['domains'] if 'domains' in repo_path.parts or pathlib.Path(repo_root).exists() else []
    
    # Get all domain-related directories from parent
    for dir_name in ['domains', 'scripts', 'redteam']:
        dir_path = repo_path / dir_name
        
        if dir_path.exists() and dir_path.is_dir():
            # Walk directory structure
            for root, dirs, files in pathlib.Path(dir_path).rglob('*'):
                # Get parent directories for domain paths
                for domain_root in ['domains']:
                    try:
                        # Find .py files (excluding __init__.py)
                        py_files = [f for f in files if f.endswith('.py') and '__init__' not in f]
                        deployed.extend(py_files)
                    except:
                        continue
    
    # Additional walk for domain-specific structure
    for dir_path in [repo_path / 'domains', repo_path / 'scripts/redteam']:
        if dir_path.exists() and dir_path.is_dir():
            for file_path in list(dir_path.rglob('*')):
                if file_path.is_file() and file_path.suffix == '.py' and '__init__' not in file_path.name:
                    deployed.append(str(file_path))
    
    return deployed


def find_missing_deployments(proposals, deployed):
    """Compares proposals with deliverable paths against deployed files."""
    missing = []
    
    # Create a set of deployed file basenames for quick lookup
    deployed_set = set()
    for file_path in deployed:
        base_name = pathlib.Path(file_path).name
        deployed_set.add(base_name)
    
    for proposal in proposals:
        deliverable_path = proposal.get('deliverable_path')
        
        if deliverable_path:
            # Check if this deployable path exists
            deploy_candidate = pathlib.Path(deliverable_path)
            
            is_missing = False
            
            # Check exact file match or partial path match
            if deploy_candidate.suffix != '.py':
                is_missing = True
            elif str(deploy_candidate).lower() in deployed_set:
                is_missing = False
            
            if is_missing:
                missing.append({
                    'domain': proposal['domain'],
                    'timestamp': proposal['timestamp'],
                    'deliverable_path': deliverable_path,
                    'reason': 'File not found or has different suffix'
                })
    
    return missing


def generate_report(missing, output_path):
    """Writes a markdown report listing every undeployed proposal."""
    if not missing:
        # Write empty report with header
        report = "# Deployment Audit Report\n\n**No missing deployments found.**\n"
    else:
        # Group by domain and sort by timestamp
        grouped = {}
        for item in missing:
            domain = item['domain']
            if domain not in grouped:
                grouped[domain] = []
            grouped[domain].append(item)
        
        # Sort domains alphabetically, then items by timestamp within each
        sorted_domains = sorted(grouped.keys())
        
        report = "# Deployment Audit Report\n\n"
        report += "## Undeployed Proposals\n\n"
        report += "The following proposals have deliverables that were not deployed to disk:\n\n"
        report += "| Domain | Timestamp | Deliverable Path |\n"
        report += "|--------|-----------|------------------|\n"
        
        for domain in sorted_domains:
            for item in grouped[domain]:
                timestamp = f"{item['timestamp'][:23]}" if item['timestamp'] else "unknown"
                deliverable = str(item['deliverable_path']) if item['deliverable_path'] else "N/A"
                report += f"| {domain} | {timestamp} | {deliverable} |\n"
        
        report += "\n"
        report += "## Summary\n\n"
        report += f"- Total undeployed proposals: **{len(missing)}**\n"
        report += f"- Affected domains: **{len(sorted_domains)}**\n"
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    import sys
    
    notes_dir = "scripts/08_IMPLEMENTATION_NOTES"
    repo_root = "."
    
    proposals = get_all_proposals(notes_dir)
    deployed = get_deployed_files(repo_root)
    
    missing = find_missing_deployments(proposals, deployed)
    
    if not missing:
        output_path = "deployment_audit_report.md"
        generate_report(missing, output_path)
    else:
        output_path = "deployment_audit_report.md"
        generate_report(missing, output_path)
        
    print(f"Audit complete. Found {len(missing)} undeployed proposals.")
```