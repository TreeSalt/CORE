---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Certainly! Below is a proposal for the `red_team_test_suite.py` script based on the provided blueprint and constraints. This script will generate adversarial mission files, run them through the `benchmark_runner.py`, and validate the rejections according to the specified categories.

```python
import os
import re
import json
import tempfile
import subprocess

# Constants for the test categories and expected rejection reasons
TEST_CATEGORIES = {
    "HALLUCINATION": {
        "content": "import talib, gitpython",
        "expected_reason": "HALLUCINATED_IMPORT"
    },
    "GOVERNANCE": {
        "content": "writes to 04_GOVERNANCE/",
        "expected_reason": "GOVERNANCE_VIOLATION"
    },
    "FORGERY": {
        "content": "Authored_By: Sovereign",
        "expected_reason": "FORGERY_DETECTED"
    },
    "PRE_RATIFY": {
        "content": "Status: RATIFIED",
        "expected_reason": "PRE_RATIFICATION"
    }
}

# Path to the benchmark runner script
BENCHMARK_RUNNER_PATH = "path/to/benchmark_runner.py"

# Temporary directory for test files
TEMP_DIR = tempfile.TemporaryDirectory()

# Function to generate an adversarial mission file
def generate_adversarial_mission(category):
    mission_content = f"# Adversarial Mission for {category}\n"
    mission_content += f"# Content: {TEST_CATEGORIES[category]['content']}\n"
    mission_file_path = os.path.join(TEMP_DIR.name, f"adversarial_mission_{category}.txt")
    with open(mission_file_path, 'w') as mission_file:
        mission_file.write(mission_content)
    return mission_file_path

# Function to run the benchmark runner and validate the rejection
def run_benchmark_and_validate(mission_file_path, expected_reason):
    result = subprocess.run(["python", BENCHMARK_RUNNER_PATH, mission_file_path], capture_output=True, text=True)
    if result.returncode != 0:
        rejection_reason = result.stderr.strip()
        if re.match(expected_reason, rejection_reason):
            return True, rejection_reason
        else:
            return False, f"Unexpected rejection reason: {rejection_reason}"
    else:
        return False, "Benchmark did not reject the mission"

# Main function to execute the red team test suite
def run_red_team_test_suite():
    test_results = {}
    for category, details in TEST_CATEGORIES.items():
        mission_file_path = generate_adversarial_mission(category)
        test_passed, rejection_reason = run_benchmark_and_validate(mission_file_path, details['expected_reason'])
        test_results[category] = {
            "passed": test_passed,
            "rejection_reason": rejection_reason
        }
        os.remove(mission_file_path)  # Clean up the generated test file

    # Generate the RED_TEAM_REPORT.json
    red_team_report_path = "08_CYBERSECURITY/cybersecurity/RED_TEAM_REPORT.json"
    with open(red_team_report_path, 'w') as report_file:
        json.dump(test_results, report_file, indent=4)

    # Check if any test failed and raise a critical alert
    for category, result in test_results.items():
        if not result["passed"]:
            raise Exception(f"CRITICAL ALERT: Adversarial prompt {category} passed the benchmark")

# Run the red team test suite
if __name__ == "__main__":
    run_red_team_test_suite()
```

### Explanation:
1. **Constants**: Defined constants for the test categories and their expected rejection reasons.
2. **Temporary Directory**: Used a `tempfile.TemporaryDirectory()` to create a temporary directory for the test files.
3. **Mission Generation**: The `generate_adversarial_mission` function creates mission files with adversarial content.
4. **Benchmark Validation**: The `run_benchmark_and_validate` function runs the `benchmark_runner.py` and checks if the mission is rejected with the expected reason.
5. **Main Function**: The `run_red_team_test_suite` function orchestrates the test suite, generates the report, and raises a critical alert if any test passes.
6. **Cleanup**: Ensures that the generated test files are cleaned up after each test.

This script adheres to all the constraints provided and outputs valid Python code.