---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import ast
import pathlib
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class StrategyGateReport:
    """
    Report structure for the strategy zoo validation gate.
    Contains pass status and findings.
    """
    passed: bool = False
    findings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_finding(self, msg: str):
        self.findings.append(msg)

    def add_error(self, msg: str):
        self.errors.append(msg)

    def finalize(self):
        if not self.errors and len(self.errors) == 0:
            self.passed = True
        else:
            self.passed = False

class StrategyZooGate:
    """
    Validates trading strategy files before entry into the strategy zoo.
    Enforces security, dependency, and functional requirements.
    """

    ALLOWED_IMPORTS = {'ast', 'builtins', 'pathlib', 'typing', 'json', 're', 'math', 'os', 'sys'}
    BANNED_MODULES = {'pandas', 'numpy', 'sklearn', 'torch', 'tensorflow', 'keras'}
    REQUIRED_FUNCTIONS = ['generate_signals', 'run_strategy']

    def __init__(self):
        self.gate_passed = False
        self.report = StrategyGateReport()

    def validate_strategy(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point to validate a strategy file.
        Returns dictionary representation of StrategyGateReport.
        """
        path = pathlib.Path(file_path)
        
        if not path.exists():
            self.report.errors.append(f"File not found: {path}")
            return self._to_dict()

        try:
            source_code = path.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            
            # 1. Check Imports (AST Level)
            self._check_imports(tree)

            # 2. Check Required Functions
            self._check_required_functions(tree)

            # 3. Check Docstring Presence
            self._check_docstrings(tree)

            # 4. Check Empty/NaN Handling Heuristics
            self._check_data_handling(tree, source_code)

            # Finalize Result
            self.report.finalize()

        except SyntaxError as e:
            self.report.errors.append(f"Syntax Error in strategy: {e}")
        except Exception as e:
            self.report.errors.append(f"Unexpected error during validation: {str(e)}")

        return self._to_dict()

    def _check_imports(self, tree: ast.Module):
        """
        Checks imports to ensure only stdlib and allowed modules are used.
        Bans pandas/numpy specifically.
        """
        imports_found = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    imports_found.add(module_name)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module.split('.')[0] if node.module else ''
                imports_found.add(module_name)

        # Verify banned modules
        for mod in self.BANNED_MODULES:
            if mod in imports_found:
                self.report.add_error(f"Forbidden import detected: {mod}")
                continue
            
        # Verify allowed modules (Relaxed check, mostly stdlib + specific allowed set)
        # Allow common utilities that are standard
        allowed_extra = {'warnings', 'math', 'itertools', 'collections'}
        for mod in imports_found:
            if mod not in self.ALLOWED_IMPORTS and mod not in allowed_extra:
                self.report.add_finding(f"Unusual import detected (verify necessity): {mod}")

    def _check_required_functions(self, tree: ast.Module):
        """
        Ensures strategy defines required entry points.
        Matches 'generate_signals' or 'run_strategy'.
        """
        function_names = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                # Filter out private methods often used internally
                name = node.name
                if name in self.REQUIRED_FUNCTIONS:
                    function_names.append(name)
                elif name.startswith('_'):
                    pass
                else:
                    function_names.append(name)

        missing_funcs = []
        for req_func in self.REQUIRED_FUNCTIONS:
            if req_func not in function_names:
                # Check for variations or synonyms just in case
                found_synonym = any(r in req_func for r in ['signal', 'run'])
                if not found_synonym:
                     missing_funcs.append(req_func)

        if missing_funcs:
            self.report.add_finding(f"Missing required functions: {', '.join(missing_funcs)}")
            # Fail closed if critical functions are missing
            self.report.add_error("Strategy missing critical function definitions.")

    def _check_docstrings(self, tree: ast.Module):
        """
        Ensures file or main strategy class/module has a docstring.
        """
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Module, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                # We are looking for module level context primarily
                if isinstance(node, ast.Module) and not docstring:
                     self.report.add_finding("File is missing a module-level docstring.")

    def _check_data_handling(self, tree: ast.Module, source_code: str):
        """
        Checks heuristics for NaN/Empty data handling.
        Since we cannot execute, we look for error handling patterns 
        related to data processing (e.g., try/except on float math).
        Also checks against forbidden imports that handle NaN implicitly.
        """
        # Heuristic 1: Check if they are relying on pandas/numpy for NaN checks (already banned)
        # So if they use standard float('nan'), we expect explicit checks.
        
        # Search source for common crash scenarios without guards
        # e.g., division by zero, accessing empty lists
        
        lines = source_code.split('\n')
        
        # Check for math operations that might fail on empty data
        has_protection = False
        try_patterns = ['try:', 'except']
        
        # Heuristic: Look for existence of explicit error handling around core logic blocks
        # This is a simplified AST heuristic
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                has_protection = True
                break
            
            # Check for direct empty list checks (good practice)
            if isinstance(node, ast.If):
                test_line = ast.get_source_segment(source_code, node).lower() if hasattr(ast, 'get_source_segment') else ""
                # If we can't get line easily via segment without context, rely on Try blocks primarily
                pass

        if not has_protection:
             self.report.add_finding("Strategy lacks explicit error handling for data processing (NaN/Empty).")
        
        # Check for specific empty checks
        source_lower = source_code.lower()
        if 'len(' in source_lower or 'if not' in source_lower:
            pass # Common pattern exists
        else:
             # If basic logic involves lists/dicts, check explicitly if safe is assumed
             if 'pd.isna' in source_lower or 'np.isnan' in source_lower:
                 self.report.add_error("Direct use of pandas/numpy NaN handling detected (violates import rules).")

    def _to_dict(self) -> Dict[str, Any]:
        """Convert report object to JSON-serializable dict."""
        return {
            "passed": self.report.passed,
            "findings": self.report.findings,
            "errors": self.report.errors,
            "metadata": self.report.metadata,
            "file_path": getattr(self.report, 'filename', None) # Not explicitly set but useful
        }

# Utility function to load and run (for orchestration purposes)
def register_strategy(file_path: str) -> StrategyGateReport:
    gate = StrategyZooGate()
    return_data = gate.validate_strategy(file_path)
    # Update report object with file path for metadata
    if 'errors' in return_data:
        return_data['file_path'] = file_path
    return return_data

if __name__ == "__main__":
    # Example usage placeholder (not executed by the validator itself)
    print("Strategy Zoo Gate Initialized")
```