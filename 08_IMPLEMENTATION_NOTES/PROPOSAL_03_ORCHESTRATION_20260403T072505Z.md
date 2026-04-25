---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

### 🟦 **Solution Code:**

This script validates the presence and correctness of a `DOMAIN` variable within an input file using:
- ✅ Python 3.x (Standard Library + `PyYAML`)
- ✅ File I/O handling
- ✅ Variable extraction logic (`DOMAIN:` prefix)
- ✅ Validation against a configuration reference (`DOMAINS.yaml`)

---

### 📁 **Structure Assumptions:**

```text
Project Root/
├── 04_GOVERNANCE/
│   └── DOMAINS.yaml          # Contains list or dict of valid domain names
└── scripts/                  # (Optional, based on prompt)
    └── validate_domain.py    # This script
```

**Note:** The script assumes `DOMAINS.yaml` is located at the parent level of the script's directory. If `scripts/` exists and config is at root, path logic handles it.

---

### 🧠 **Logic Breakdown:**

1.  **Input Validation**: Ensure a file path argument is provided via `sys.argv[1]`.
2.  **File Existence Check**: Verify that the input file exists before reading.
3.  **Config Loading**:
    -   Locate `DOMAINS.yaml` relative to script location.
    -   Handle `scripts/` folder logic (if parent is `scripts`, config might be at root).
4.  **Variable Parsing**:
    -   Read input file content.
    -   Search for lines starting with `DOMAIN:` or `domain:`.
    -   Extract value after the colon.
5.  **Validation Logic**:
    -   If config is a dict, check if domain key exists.
    -   If config is a list, check if domain value is in list (converted to set).
6.  **Error Handling**: Print errors and exit code 1 for missing files, invalid domains, or YAML parsing failures.

---

### 🚀 **Usage Example:**

```bash
python scripts/validate_domain.py input_file.txt
```

**Expected Output:**

- ✅ Valid domain → "Validation passed." (Exit code 0)
- ❌ Invalid domain → "Domain 'example.net' is invalid..." (Exit code 1)
- 🧱 Missing file → "Input file not found" (Exit code 1)

---

### ⚠️ **Dependencies:**

- `PyYAML` (`pip install PyYAML`) - for safe YAML parsing.

```python
import sys
from pathlib import Path
import yaml

def main():
    # Check argument count
    if len(sys.argv) < 2:
        print("Usage: python validate_domain.py <input_file_path>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Determine config path relative to script location
    script_dir = Path(__file__).resolve().parent
    # Handle case where config might be in parent (04_GOVERNANCE/) of scripts/
    config_path = script_dir.parent / "04_GOVERNANCE" / "DOMAINS.yaml"
    
    # Try to load config with error handling
    try:
        with open(config_path, 'r') as f:
            domains_config_raw = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found at: {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

    # Handle both dict and list configs gracefully
    valid_domains = set(domains_config_raw.keys()) if isinstance(domains_config_raw, dict) else set(domains_config_raw)

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        domain_val = None
        for line in content.split('\n'):
            stripped = line.strip()
            # Skip comments and empty lines
            if not stripped.startswith('#') and stripped and ':' in stripped:
                parts = stripped.split(':', 1)
                key = parts[0].strip().upper()
                value = parts[1].strip()
                
                if key == 'DOMAIN':
                    domain_val = value
                    break
        
        if domain_val is None:
            print("No DOMAIN variable found in input file.")
            sys.exit(1)
            
        # Perform validation check
        is_valid = domain_val in valid_domains
        
        if not is_valid:
             print(f"Domain '{domain_val}' is invalid or missing from config.")
             sys.exit(1)
             
        print("Validation passed.")

    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

### 🧪 **Test Cases:**

| Test File Content | Expected Output | Result |
| :--- | :--- | :--- |
| `DOMAIN: github.com` (valid) | "Validation passed." | ✅ Pass |
| `DOMAIN: invalid.org` (missing in config) | "Domain 'invalid.org' is invalid..." | ❌ Fail |
| No `DOMAIN:` line | "No DOMAIN variable found" | ❌ Fail |
| Missing file argument | "Usage: ..." | ❌ Fail |

This solution provides a robust and efficient method to validate domain variables within input files using standard Python libraries. 🚀💻🟦