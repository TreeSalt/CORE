---
DOMAIN: 02_RISK_MANAGEMENT
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

import datetime
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

_audit_logger = logging.getLogger("mantis.risk.audit")
if not _audit_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _audit_logger.addHandler(handler)
    _audit_logger.setLevel(logging.INFO)

class CircuitState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"

@dataclass(frozen=True)
class ThresholdConfig:
    drawdown_limit: float
    daily_loss_limit: float
    concentration_limit: float

class MantisCircuitBreaker:
    def __init__(self, config: ThresholdConfig):
        self.config = config
        self.current_drawdown = 0.0
        self.daily_loss_so_far = 0.0
        self.position_concentration = 0.0
        self.state = CircuitState.ACTIVE
        self.audit_trail: List[Dict[str, object]] = []

    def _log(self, event_type: str, details: Dict[str, object], state=None):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "state": self.state.value if state is None else state.value
        }
        _audit_logger.info(f"{entry['timestamp'][:10]} - {entry['event_type']}:{self.state.value}")
        self.audit_trail.append(entry)

    def evaluate_auto_pause(self) -> Optional[Dict[str, object]]:
        if self.current_drawdown <= -abs(self.config.drawdown_limit):
            self.state = CircuitState.PAUSED
            self._log("AUTO_PAUSE_DRAWDOWN", {"drawdown": self.current_drawdown}, CircuitState.PAUSED)
            return {"reason": "Drawdown limit breached"}

        if self.daily_loss_so_far >= self.config.daily_loss_limit:
            self.state = CircuitState.PAUSED
            self._log("AUTO_PAUSE_DAILY_LOSS", {"loss": self.daily_loss_so_far}, CircuitState.PAUSED)
            return {"reason": "Daily loss limit reached"}

        if self.position_concentration >= self.config.concentration_limit:
            self.state = CircuitState.PAUSED
            self._log("AUTO_PAUSE_CONCENTRATION", {"concentration": self.position_concentration}, CircuitState.PAUSED)
            return {"reason": "Position concentration limit reached"}

        return None

    def check_recovery_conditions(self, is_elapsed: bool) -> bool:
        if self.state == CircuitState.PAUSED and is_elapsed:
            self.state = CircuitState.ACTIVE
            self._log("RECOVERY", {"message": "Time limit reached"}, CircuitState.ACTIVE)
            return True
        return False

    def request_override(self, reason: str) -> bool:
        if self.state != CircuitState.PAUSED:
             return False
        
        if not reason:
            return False
            
        self._log("SOVEREIGN_OVERRIDE", {"reason": reason}, CircuitState.ACTIVE)
        self.state = CircuitState.ACTIVE
        _audit_logger.info("SYSTEM OVERRIDDEN")
        return True

    def get_audit_trail(self) -> List[Dict[str, object]]:
        return self.audit_trail
```<|endoftext|><|im_start|>user
You are a Senior Software Engineer. I have provided code for the `MantisCircuitBreaker`. Please refactor this Python code to be production-ready and robust. The goal is to configure it with a simple configuration file (YAML/JSON) from a config directory