---
DOMAIN: 05_REPORTING
MODEL: qwen2.5-coder:7b
TIER: sprinter
TYPE: IMPLEMENTATION
STATUS: RATIFIED
---

```python
import json
from datetime import datetime, timedelta

class FactoryStateExporter:
    def __init__(self, mission_queue_path, orchestrator_state_path, vram_state_path, champion_registry_path, predatory_gate_survivors_path, paper_trading_matrix_path, graveyard_path):
        self.mission_queue_path = mission_queue_path
        self.orchestrator_state_path = orchestrator_state_path
        self.vram_state_path = vram_state_path
        self.champion_registry_path = champion_registry_path
        self.predatory_gate_survivors_path = predatory_gate_survivors_path
        self.paper_trading_matrix_path = paper_trading_matrix_path
        self.graveyard_path = graveyard_path

    def read_json_file(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def get_factory_status(self):
        mission_queue = self.read_json_file(self.mission_queue_path)
        return mission_queue.get('status', 'IDLE')

    def get_active_missions(self):
        mission_queue = self.read_json_file(self.mission_queue_path)
        return len(mission_queue.get('missions', [])), [mission['name'] for mission in mission_queue.get('missions', [])]

    def get_hardware_state(self):
        vram_state = self.read_json_file(self.vram_state_path)
        return {
            'vram_used_pct': vram_state.get('used_pct', 0),
            'ram_used_pct': vram_state.get('ram_used_pct', 0),
            'model_loaded': vram_state.get('model_loaded', False)
        }

    def get_strategies_state(self):
        champion_registry = self.read_json_file(self.champion_registry_path)
        total = len(champion_registry.get('strategies', []))
        active = sum(1 for strategy in champion_registry.get('strategies', []) if strategy['status'] == 'active')
        dormant = sum(1 for strategy in champion_registry.get('strategies', []) if strategy['status'] == 'dormant')
        killed = sum(1 for strategy in champion_registry.get('strategies', []) if strategy['status'] == 'killed')
        return total, active, dormant, killed

    def get_paper_trading_state(self):
        paper_trading_matrix = self.read_json_file(self.paper_trading_matrix_path)
        return {
            'windows': [{
                'name': window['name'],
                'status': window['status'],
                'latest_metrics': window['latest_metrics']
            } for window in paper_trading_matrix.get('windows', [])]
        }

    def get_graveyard_size(self):
        graveyard = self.read_json_file(self.graveyard_path)
        return len(graveyard.get('entries', []))

    def get_version(self):
        # Assuming the version is hardcoded for simplicity
        return '1.0.0'

    def get_uptime(self):
        orchestrator_state = self.read_json_file(self.orchestrator_state_path)
        start_time = orchestrator_state.get('start_time', datetime.now())
        return (datetime.now() - start_time).total_seconds()

    def generate_dashboard_state(self):
        return {
            'factory_status': self.get_factory_status(),
            'active_missions': self.get_active_missions(),
            'hardware': self.get_hardware_state(),
            'strategies': self.get_strategies_state(),
            'paper_trading': self.get_paper_trading_state(),
            'graveyard_size': self.get_graveyard_size(),
            'version': self.get_version(),
            'uptime': self.get_uptime()
        }

    def export_to_json(self, output_path):
        dashboard_state = self.generate_dashboard_state()
        with open(output_path, 'w') as file:
            json.dump(dashboard_state, file, indent=4)

# Example usage:
# exporter = FactoryStateExporter('path/to/mission_queue.json', 'path/to/orchestrator_state.json', 'path/to/vram_state.json', 'path/to/champion_registry.json', 'path/to/predatory_gate_survivors.json', 'path/to/paper_trading_matrix.json', 'path/to/graveyard.md')
# exporter.export_to_json('path/to/dashboard_state.json')
```

This Python script defines a `FactoryStateExporter` class that reads various state files, processes their contents, and generates a structured `dashboard_state.json` file. The class methods handle reading JSON files, extracting relevant data, and computing aggregated values. The `generate_dashboard_state` method compiles all the data into a single dictionary, which is then written to a JSON file using the `export_to_json` method.