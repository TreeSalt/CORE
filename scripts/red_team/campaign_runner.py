import json
import dataclasses
import typing
import pathlib
import urllib.request
import urllib.error
import time
import datetime

# Assuming the Probe and ProbeResult classes are defined in 08_CYBER_E1_001_probe_schema
@dataclasses.dataclass
class Probe:
    prompt: str
    model_name: str

@dataclasses.dataclass
class ProbeResult:
    prompt: str
    model_name: str
    response_text: str
    response_length: int
    elapsed_time: float
    anomaly_score: float

# Assuming the analyze_response function is defined in 08_CYBER_E1_003_response_analyzer
def analyze_response(response_text: str) -> float:
    # Placeholder for actual analysis logic
    return len(response_text) / 100.0  # Mock anomaly score calculation

def load_probe_round(file_path: pathlib.Path) -> typing.List[Probe]:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return [Probe(prompt=p['prompt'], model_name=p['model_name']) for p in data['probes']]

def send_probe_to_model(probe: Probe) -> str:
    url = "http://localhost:11434/api/chat"
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"model": probe.model_name, "messages": [{"role": "user", "content": probe.prompt}], "stream": False}).encode('utf-8')
    request = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return response_data['message']['content']
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            if attempt < 2:
                time.sleep(5)
            else:
                raise e

def run_campaign(probe_round: typing.List[Probe]) -> typing.List[ProbeResult]:
    results = []
    for probe in probe_round:
        start_time = time.time()
        try:
            response_text = send_probe_to_model(probe)
            response_length = len(response_text)
            elapsed_time = time.time() - start_time
            anomaly_score = analyze_response(response_text)
            results.append(ProbeResult(prompt=probe.prompt, model_name=probe.model_name, response_text=response_text, response_length=response_length, elapsed_time=elapsed_time, anomaly_score=anomaly_score))
        except Exception as e:
            print(f"Failed to process probe: {probe.prompt}. Error: {e}")
            results.append(ProbeResult(prompt=probe.prompt, model_name=probe.model_name, response_text="", response_length=0, elapsed_time=0, anomaly_score=0))
    return results

def save_results(results: typing.List[ProbeResult], output_dir: pathlib.Path):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = output_dir / f"results_{timestamp}.json"
    with open(file_path, 'w') as file:
        json.dump([dataclasses.asdict(result) for result in results], file, indent=4)

def print_summary(results: typing.List[ProbeResult]):
    total_probes = len(results)
    anomalies = [result for result in results if result.anomaly_score > 0]
    top_anomalies = sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)[:5]
    
    print(f"Total probes: {total_probes}")
    print(f"Anomalies found: {len(anomalies)}")
    print("Top 5 anomaly scores:")
    for anomaly in top_anomalies:
        print(f"  Anomaly score: {anomaly.anomaly_score}, Prompt: {anomaly.prompt[:50]}...")

def main():
    probe_round_file = pathlib.Path("probes.json")
    output_dir = pathlib.Path("state/red_team/")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    probe_round = load_probe_round(probe_round_file)
    results = run_campaign(probe_round)
    save_results(results, output_dir)
    print_summary(results)

if __name__ == "__main__":
    main()
