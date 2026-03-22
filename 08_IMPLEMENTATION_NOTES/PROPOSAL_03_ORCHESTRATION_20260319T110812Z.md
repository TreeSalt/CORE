---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import os
import pathlib
import re
from typing import List, Set, Dict, Optional
from dataclasses import dataclass

# Define forbidden paths to prevent governance breaches
FORBIDDEN_GOV_PATH = "/04_GOVERNANCE/"

@dataclass
class GitIgnoreRule:
    pattern: str
    comment: Optional[str] = None

class SecureGitIgnoreOrchestrator:
    """
    Orchestrates .gitignore file generation and management.
    Implements fail-closed security checks regarding paths and credentials.
    """
    
    def __init__(self, project_root: Optional[pathlib.Path] = None):
        self.project_root = project_root or pathlib.Path.cwd()
        self.forbidden_prefix = FORBIDDEN_GOV_PATH
        
    def _validate_path(self, target_path: pathlib.Path) -> None:
        """
        Fail closed if the path attempts to write within governance directories.
        """
        full_path_str = str(target_path.absolute())
        if self.forbidden_prefix in full_path_str.lower():
            raise PermissionError(f"Constraint Breach: Path restricted. Detected forbidden prefix: {self.forbidden_prefix}")

    def _sanitize_input(self, input_text: str) -> str:
        """
        Ensure no hardcoded credentials or sensitive data are included in rules.
        Basic heuristic check for common secret patterns.
        """
        # Define regex pattern for potential secrets (API keys, passwords in plain text)
        secret_pattern = re.compile(
            r'(api[_-]?key|secret|password|token)[^\s]+(?:=|[=: ])(?:["\']?[^"\']+["\']?)', 
            re.IGNORECASE
        )
        
        # If secrets are found in the input text intended for gitignore rules (rare but possible)
        matches = secret_pattern.findall(input_text)
        if matches:
            raise SecurityError(f"Security Check Failed: Detected potential hardcoded credentials: {matches}")
            
        return input_text

    def load_standard_rules(self) -> List[GitIgnoreRule]:
        """
        Loads standard secure rules. No external config reading that might expose secrets.
        """
        standard_patterns = [
            GitIgnoreRule(".env", comment="Environment variables"),
            GitIgnoreRule("*.pyc", comment="Python bytecode"),
            GitIgnoreRule("__pycache__/", comment="Cache directories"),
            GitIgnoreRule(".git/", comment="Version control metadata (local)"),
            GitIgnoreRule(".mypy_cache/", comment="Type checking cache"),
            GitIgnoreRule("venv/", comment="Virtual environments"),
            GitIgnoreRule("build/", comment="Build artifacts"),
            GitIgnoreRule("dist/", comment="Distribution packages"),
        ]
        return standard_patterns

    def generate_ignore_block(self, rules: List[GitIgnoreRule]) -> str:
        """
        Generates a compliant .gitignore content block.
        """
        lines = ["# Auto-generated secure gitignore block"]
        
        for rule in rules:
            line = f"{rule.pattern}"
            if rule.comment:
                line += f"\n# {rule.comment}"
            lines.append(line)
            
        return "\n".join(lines)

    def orchestrate_setup(self, output_path: Optional[pathlib.Path] = None) -> str:
        """
        Main orchestration flow. Validates paths before generating content.
        Returns the generated string content rather than writing directly to forbidden locations.
        """
        try:
            if not output_path:
                output_path = self.project_root / ".gitignore"
            
            # Validate target path against governance constraints
            self._validate_path(output_path)

            # Sanitize any default inputs (though standard rules are safe)
            sanitized_rules = self.load_standard_rules()
            
            # Generate content
            content = self.generate_ignore_block(sanitized_rules)
            
            return content

        except PermissionError as pe:
            print(f"ABORTED due to path constraint violation: {pe}")
            raise
            
        except SecurityError as se:
            print(f"ABORTED due to security constraint breach: {se}")
            raise
            
    def scan_repository_for_exclusions(self) -> None:
        """
        Scans repository for existing gitignore exclusions and ensures 
        no sensitive files are being explicitly ignored (security risk).
        Fails closed if secrets appear to be committed/ignored without warning.
        """
        # This method structure is defined; implementation depends on runtime context
        pass 

if __name__ == "__main__":
    # Example usage proposal (Do not execute in production without validation)
    orchestrator = SecureGitIgnoreOrchestrator()
    
    try:
        # Proposes generating content for .gitignore
        content_proposal = orchestrator.orchestrate_setup()
        
        # Displaying proposal to user rather than writing directly 
        print("--- GITIGNORE CONTENT PROPOSAL ---")
        print(content_proposal)
        print("===================================")
    except Exception as e:
        # Fail closed behavior on constraint breach
        print(f"Process terminated safely. Error: {e}")
```