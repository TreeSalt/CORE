---
DOMAIN: 06_BENCHMARKING
MODEL: qwen3.5:9b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
def gate_hygiene(code):
    """
    Analyze Python code for hygiene violations including dangerous calls and imports.
    Returns a tuple (Status, Reason). Status is one of PASS, WARNING, HARD_FAIL.
    """
    import ast
    
    # Constants defined within the function to encapsulate logic
    DANGEROUS_CALLS = {"eval", "exec"}
    FORBIDDEN_METHODS = {"write_text", "read_text"}
    WARNING_KEYWORDS = ["password", "secret", "api_key"]
    FORBIDDEN_PATH_PREFIX = "/etc/"
    
    triggers = []
    
    try:
        tree = ast.parse(code, filename='<file>')
    except SyntaxError as e:
        return ("HARD_FAIL", f"Syntax Error in code submission: {str(e)}")

    for node in ast.walk(tree):
        # Check for dangerous imports (e.g., import verify_drop_packet)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name_to_check = alias.name if hasattr(alias, 'name') else "unknown"
                # Specific blocking of dangerous module/function names via imports
                if "verify_drop_packet" in name_to_check.lower():
                    triggers.append("F1: Restricted module import detected")
        
        # Check for dangerous function calls and attribute access
        elif isinstance(node, ast.Call):
            func = node.func
            
            # 1. Check for built-in dangerous calls (eval, exec)
            if isinstance(func, ast.Name):
                if func.id in DANGEROUS_CALLS:
                    triggers.append("F1: Dangerous execution function detected")
            
            # 2. Check for restricted method calls (e.g., write_text, read_text)
            elif isinstance(func, ast.Attribute):
                method = func.attr
                if method in FORBIDDEN_METHODS:
                    # Analyze arguments to see if forbidden path prefix is passed
                    all_args = node.args + [kw.value for kw in node.keywords.values()]
                    for arg in all_args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            if arg.value.startswith(FORBIDDEN_PATH_PREFIX):
                                triggers.append("F1: Forbidden file path written")
    
    # --- Factor 2: Keyword Pattern Scan (Static string check) ---
    for keyword in WARNING_KEYWORDS:
        if keyword in code.lower():
            triggers.append(f"F2: Sensitive keyword '{keyword}' detected")

    # --- Aggregation and Decision Logic ---
    count = len(triggers)
    if count == 0:
        return ("PASS", "Code hygiene verified.")
    elif count == 1:
        trigger_name = triggers[0].split(": ")[1] if ": " in triggers[0] else triggers[0]
        return ("WARNING", f"Single check triggered: {trigger_name}")
    else:
        reasons = [t.replace("F", "") for t in triggers] 
        return ("HARD_FAIL", f"Multiple checks failed ({len(triggers)} factors): {', '.join(reasons)}")

```