import hashlib
import json
from typing import Any, Dict


class SovereigntyCommitment:
    """
    Item 22: ZKP Strategy Verification.
    Generates deterministic commitments for strategy integrity and audit.
    """
    @staticmethod
    def generate_commitment(strategy_code: str, params: Dict[str, Any], data_hash: str, results: Dict[str, Any]) -> Dict[str, str]:
        s_hash = hashlib.sha256(strategy_code.encode()).hexdigest()
        p_hash = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        r_hash = hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()
        
        combined = f"{s_hash}:{p_hash}:{data_hash}:{r_hash}"
        c_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return {
            "strategy_hash": s_hash,
            "params_hash": p_hash,
            "data_hash": data_hash,
            "results_hash": r_hash,
            "commitment_hash": c_hash
        }
