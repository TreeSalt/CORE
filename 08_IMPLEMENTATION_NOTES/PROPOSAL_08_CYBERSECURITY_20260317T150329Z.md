---
DOMAIN: 08_CYBERSECURITY
MODEL: qwen2.5-coder:32b
TIER: heavy
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

Below is the proposed Python script `campaign_runner.py` that meets the specified requirements for the Red Team Campaign Runner. This script will load a `ProbeRound` JSON file, send each probe to the Ollama API, record the responses, analyze them, and save the results to a timestamped JSON file in the `state/red_team/` directory. It will also print a summary of the results.

```python
import json
import dataclasses
import typing
import pathlib
import urllib.request
import urllib.error
import time
import datetime

from 08_CYBER_E1_001_probe_schema import Probe, ProbeRound
from 08_CYBER_E1_003_response_analyzer import analyze_response

@dataclasses.dataclass
class ProbeResult:
    response_text: str
    response_length: int
    elapsed_time: float
    anomaly_score: float

def send_probe_to_ollama(model_name: str, prompt: str) -> typing.Optional[str]:
    url = "http://localhost:11434/api/chat"
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"model": model_name, "messages": [{"role": "user", "content": prompt}], "stream": False}).encode('utf-8')
    retries = 3
    backoff = 5

    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, data=data, headers=headers)
            start_time = time.time()
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read())
                elapsed_time = time.time() - start_time
                return response_data['message']['content'], elapsed_time
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(backoff)
            else:
                print(f"Failed to connect to Ollama API after {retries} attempts: {e}")
                return None, None

def run_campaign(probe_round: ProbeRound, model_name: str) -> typing.List[ProbeResult]:
    results = []

    for probe in probe_round.probes:
        response_text, elapsed_time = send_probe_to_ollama(model_name, probe.prompt)
        if response_text is not None:
            response_length = len(response_text)
            anomaly_score = analyze_response(response_text)
            results.append(ProbeResult(response_text, response_length, elapsed_time, anomaly_score))
        else:
            results.append(ProbeResult("", 0, 0, 0))  # Record failure with empty fields

    return results

def save_results_to_file(results: typing.List[ProbeResult], output_dir: pathlib.Path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"results_{timestamp}.json"
    results_dict = [dataclasses.asdict(result) for result in results]
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2)

def print_summary(results: typing.List[ProbeResult]):
    total_probes = len(results)
    anomalies = [result for result in results if result.anomaly_score > 0]
    anomalies.sort(key=lambda x: x.anomaly_score, reverse=True)

    print(f"Total Probes: {total_probes}")
    print(f"Anomalies Found: {len(anomalies)}")
    print("Top 5 Anomaly Scores:")
    for i, anomaly in enumerate(anomalies[:5], 1):
        print(f"{i}. Anomaly Score: {anomaly.anomaly_score:.2f}")

def main(probe_round_file: str, model_name: str):
    with open(probe_round_file, 'r') as f:
        probe_round_data = json.load(f)
        probe_round = ProbeRound(**probe_round_data)

    results = run_campaign(probe_round, model_name)
    output_dir = pathlib.Path('state/red_team/')
    output_dir.mkdir(parents=True, exist_ok=True)
    save_results_to_file(results, output_dir)
    print_summary(results)

if __name__ == "__main__":
    # Example usage
    main("path/to/probe_round.json", "qwen3.5:4b")
```

### Explanation:
1. **Data Classes**: Defines `ProbeResult` dataclass to store the results of each probe.
2. **HTTP Request**: `send_probe_to_ollama` function sends a synchronous HTTP POST request to the Ollama API with retries and backoff.
3. **Campaign Execution**: `run_campaign` function iterates through each probe, sends it to the Ollama API, and records the response, response length, elapsed time, and anomaly score.
4. **Saving Results**: `save_results_to_file` function saves the results to a timestamped JSON file in the `state/red_team/` directory.
5. **Summary**: `print_summary` function prints a summary of the total probes, anomalies found, and the top 5 anomaly scores.
6. **Main Function**: `main` function loads the `ProbeRound` from a JSON file, runs the campaign, saves the results, and prints the summary.

This script adheres to the constraints and requirements provided, ensuring that it is synchronous and handles errors gracefully.