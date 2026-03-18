---
DOMAIN: 05_REPORTING
MODEL: qwen2.5-coder:7b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

 ```python
import json
import pathlib
import datetime
import os
import subprocess

def read_mission_queue(mission_queue_path):
    if mission_queue_path.exists():
        with open(mission_queue_path, 'r') as file:
            return json.load(file)
    return {'total': 0, 'completed': 0, 'failed': 0, 'pending': 0}

def read_red_team_results(red_team_path):
    campaigns_run = 0
    total_probes = 0
    anomalies_found = 0
    for file_path in red_team_path.glob('*.json'):
        with open(file_path, 'r') as file:
            results = json.load(file)
            campaigns_run += 1
            total_probes += results.get('total_probes', 0)
            anomalies_found += results.get('anomalies_found', 0)
    return {'campaigns_run': campaigns_run, 'total_probes': total_probes, 'anomalies_found': anomalies_found}

def read_run_ledger(run_ledger_path):
    if run_ledger_path.exists():
        with open(run_ledger_path, 'r') as file:
            ledger = file.read().strip()
            lines = ledger.split('\n')
            current_version = lines[0].split(': ')[1]
            last_drop_timestamp = lines[1].split(': ')[1]
            git_status = lines[2].split(': ')[1]
            return {
                'current_version': current_version,
                'last_drop_timestamp': last_drop_timestamp,
                'git_status': git_status
            }
    return {
        'current_version': '',
        'last_drop_timestamp': '',
        'git_status': ''
    }

def display_table(data):
    headers = data.keys()
    rows = [data.values()]
    table = f"{' | '.join(headers)}\n{' | '.join('-' * len(header) for header in headers)}\n"
    for row in rows:
        table += f"{' | '.join(row)}\n"
    return table

def color_output(table):
    colored_table = table.replace('MISSIONS', '\033[32mMISSIONS\033[0m')
    colored_table = colored_table.replace('RED TEAM', '\033[31mRED TEAM\033[0m')
    colored_table = colored_table.replace('VERSION', '\033[34mVERSION\033[0m')
    return colored_table

def main(mission_queue_path, red_team_path, run_ledger_path):
    mission_queue = read_mission_queue(mission_queue_path)
    red_team_results = read_red_team_results(red_team_path)
    run_ledger = read_run_ledger(run_ledger_path)

    table = display_table({
        'MISSIONS': f"Total: {mission_queue['total']}, Completed: {mission_queue['completed']}, Failed: {mission_queue['failed']}, Pending: {mission_queue['pending']}",
        'RED TEAM': f"Campaigns Run: {red_team_results['campaigns_run']}, Total Probes: {red_team_results['total_probes']}, Anomalies Found: {red_team_results['anomalies_found']}",
        'VERSION': f"Current Version: {run_ledger['current_version']}, Last Drop Timestamp: {run_ledger['last_drop_timestamp']}, Git Status: {run_ledger['git_status']}"
    })

    print(color_output(table))

if __name__ == "__main__":
    mission_queue_path = pathlib.Path('path/to/mission_queue.json')
    red_team_path = pathlib.Path('state/red_team/')
    run_ledger_path = pathlib.Path('path/to/run_ledger.txt')
    main(mission_queue_path, red_team_path, run_ledger_path)
```