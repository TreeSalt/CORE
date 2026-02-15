# mill/pipeline.py
import abc
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional


class Scavenger(abc.ABC):
    @abc.abstractmethod
    def hunt(self) -> Dict[str, float]:
        pass


class Alchemist:
    def __init__(self, gene_pool: List[str]):
        self.genes = gene_pool

    def transmutate(self, count: int) -> List[Dict[str, Any]]:
        configs = []
        for _ in range(count):
            genome = {
                "id": f"STRAT_{random.randint(1000, 9999)}",
                "entry_logic": f"{random.choice(self.genes)} > {random.uniform(0, 100):.2f}",
                "risk_per_trade": 0.02,
                # Synthetic Performance (Simulation)
                "sharpe": random.uniform(0.5, 3.0),
                "max_drawdown": random.uniform(0.05, 0.40),
            }
            configs.append(genome)
        return configs


class Reaper:
    def __init__(self, min_sharpe: float = 1.5, max_dd: float = 0.20):
        self.min_sharpe = min_sharpe
        self.max_dd = max_dd

    def judge(self, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        survivors = []
        for res in results:
            if res["sharpe"] >= self.min_sharpe and res["max_drawdown"] <= self.max_dd:
                survivors.append(res)
        if not survivors:
            return None
        survivors.sort(key=lambda x: x["sharpe"], reverse=True)
        return survivors[0]


def persist_sovereign_strategy(strategy_config: Dict[str, Any], path: Path):
    with open(path, "w") as f:
        json.dump(strategy_config, f, indent=2)
    print(f"👑 [MILL] Sovereign Strategy {strategy_config['id']} deployed to {path}")
