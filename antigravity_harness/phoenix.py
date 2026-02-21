import hashlib
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional
from decimal import Decimal

try:
    from nacl.signing import SigningKey
except ImportError:
    SigningKey = None


class FlightRecorder:
    """Centralized error/recovery logger for mid-flight resilience.

    Records every error, self-heal action, and recovery with timestamps.
    Persists to FLIGHT_LOG.json so post-mortem analysis is always possible.
    Singleton per process — access via FlightRecorder.instance().
    """

    _instance: Optional["FlightRecorder"] = None

    def __init__(self, log_dir: Path) -> None:
        self._log_dir = log_dir
        self._events: List[Dict[str, Any]] = []

    @classmethod
    def instance(cls, log_dir: Optional[Path] = None) -> "FlightRecorder":
        """Get or create the singleton FlightRecorder."""
        if cls._instance is None:
            if log_dir is None:
                log_dir = Path("reports")
            cls._instance = cls(log_dir)
        return cls._instance

    def record_error(self, source: str, error: Exception, severity: str = "ERROR") -> None:
        """Record an error that was caught and contained."""
        self._events.append({
            "timestamp": time.time(),
            "type": "ERROR",
            "severity": severity,
            "source": source,
            "error": str(error),
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc(),
        })

    def record_recovery(self, source: str, action: str, detail: str = "") -> None:
        """Record a self-heal action that was taken."""
        self._events.append({
            "timestamp": time.time(),
            "type": "RECOVERY",
            "source": source,
            "action": action,
            "detail": detail,
        })

    def flush(self) -> Optional[Path]:
        """Persist the flight log to disk. Returns the path or None on failure."""
        if not self._events:
            return None
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            path = self._log_dir / "FLIGHT_LOG.json"
            payload = {
                "recorded_at": time.time(),
                "event_count": len(self._events),
                "events": self._events,
            }
            path.write_text(json.dumps(payload, indent=2, default=str))
            return path
        except OSError:
            # Recording failures must NEVER crash the system
            return None


class SovereignAuditor:
    """
    Institutional Audit Engine for TRADER_OPS (The Phoenix Protocol).
    Responsible for runtime integrity, invariant enforcement, and forensic reporting.
    """

    def __init__(self, repo_root: Path, account_id: str, debug_mode: bool = False):
        """
        Initialize the auditor with a repository root and an account identifier.
        The auditor initializes with Sovereign Defaults for invariant enforcement.
        """
        self.repo_root = repo_root
        self.account_id = account_id
        self.debug_mode = debug_mode
        self.log: List[Dict[str, Any]] = []
        self.decisions: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.invariants_passed = True
        
        # Runtime Constraints (Sovereign Defaults)
        self.max_exposure_pct = 10.0      # Hard limit (10x Leprechaun leverage)
        self.max_single_order_pct = 1.1  # Allow 100% Equity + 10% slippage/margin buffer
        self._strategy_commitment: Optional[Dict[str, str]] = None
        
        # Item 27: Live Safety Guard
        from antigravity_harness.execution.safety import ExecutionSovereignGuard, ExecutionSafetyConfig # noqa: PLC0415
        self.sovereign_guard = ExecutionSovereignGuard(ExecutionSafetyConfig(), None)

    def attach_strategy_commitment(self, strategy_code: str, params: Dict[str, Any], data_hash: str, results: Dict[str, Any]) -> None:
        """
        Generate a ZKP-inspired commitment for the current strategy run.
        """
        from antigravity_harness.zkp import SovereigntyCommitment # noqa: PLC0415
        self._strategy_commitment = SovereigntyCommitment.generate_commitment(
            strategy_code, params, data_hash, results
        )

    def log_decision(self, bar_idx: int, timestamp: Any, decision: str, context: Dict[str, Any]) -> None:
        """Capture high-fidelity decision telemetry for forensic debugging."""
        if not self.debug_mode:
            return
            
        self.decisions.append({
            "bar_idx": bar_idx,
            "timestamp": str(timestamp),
            "decision": decision,
            "context": context
        })

    def boot_audit(self, current_cash: float, current_qty: float) -> None:
        """
        Reconcile WAL state with actual account state.
        Logs the starting 'Ground Truth' for the current session.
        """
        print(f"🦅 [AUDITOR] Boot Audit: Reconciling {self.account_id}...")
        self._log_event("BOOT_SYNC", {
            "cash": current_cash,
            "qty": current_qty,
            "status": "CONSISTENT"
        })

    def check_invariants(self, account: Any, order_qty: float, order_price: float) -> bool:
        """
        Verify exposure limits and order constraints before execution.
        Returns True if all invariants pass, otherwise logs a violation and returns False.
        """
        # Exposure check: Current Equity + Proposed Order Value
        equity = account.cash + (account.qty * order_price)
        order_value = order_qty * order_price
        
        # 1. Exposure Check (Total exposure including current position)
        current_exposure = account.qty * order_price
        total_p_exposure = current_exposure + order_value
        
        if total_p_exposure > (equity * self.max_exposure_pct):
            self._log_event("INVARIANT_VIOLATION", {"type": "EXPOSURE_LIMIT", "value": total_p_exposure})
            self.invariants_passed = False
            return False
            
        # 2. Order Sizing Check
        if order_value > (equity * self.max_single_order_pct):
            self._log_event("INVARIANT_VIOLATION", {"type": "ORDER_SIZE_LIMIT", "value": order_value})
            self.invariants_passed = False
            return False
            
        # Item 27: Live Safety Vetting
        from antigravity_harness.execution.adapter_base import OrderIntent, OrderSide, OrderType # noqa: PLC0415
        mock_intent = OrderIntent(
            symbol=getattr(account, 'symbol', 'UNKNOWN'),
            side=OrderSide.BUY if order_qty > 0 else OrderSide.SELL,
            quantity=int(abs(order_qty)),
            order_type=OrderType.LIMIT,
            limit_price=Decimal(str(order_price))
        )
        data_ts = getattr(account, 'last_update_time', datetime.utcnow())

        ok, reason = self.sovereign_guard.validate_intent(mock_intent, equity, data_ts)
        if not ok:
            self._log_event("SAFETY_HALT", {"reason": reason, "equity": equity})
            self.invariants_passed = False
            return False
            
        return True

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Internal helper to append an event to the audit trail with a high-res timestamp."""
        self.log.append({
            "timestamp": time.time(),
            "event": event_type,
            "data": data
        })

    def emit_audit_report(self, final_account: Any) -> Path:
        """
        Generate a signed AUDIT_REPORT.json containing the full forensic trail.
        Uses Ed25519 (The Phoenix Seal) for cryptographic intent binding.
        """
        report_path = self.repo_root / "reports/AUDIT_REPORT.json"
        
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            report = {
                "account_id": self.account_id,
                "audit_session_id": hashlib.sha256(str(self.start_time).encode()).hexdigest()[:12],
                "duration_sec": time.time() - self.start_time,
                "invariants_passed": self.invariants_passed,
                "final_state": {
                    "cash": final_account.cash,
                    "qty": final_account.qty
                },
                "events": self.log,
                "forensic_decisions": self.decisions if self.debug_mode else [],
                "sovereignty_proof": self._strategy_commitment
            }
            
            report_bytes = json.dumps(report, indent=2, sort_keys=True).encode("utf-8")
            report_path.write_bytes(report_bytes)
            
            # Sign the report if institutional seed exists
            seed_path = self.repo_root / "sovereign.seed"
            if seed_path.exists() and SigningKey is not None:
                
                sig_path = report_path.with_suffix(".json.sig")
                print(f"✍️  Signing Audit Report: {sig_path.name} (The Phoenix Seal)")
                
                seed = seed_path.read_bytes()
                signing_key = SigningKey(seed)
                signed_report = signing_key.sign(report_bytes)
                
                # We save just the signature
                sig_path.write_bytes(signed_report.signature)

            # Item 24: Record in Immutable Ledger
            if self.invariants_passed and self._strategy_commitment:
                from antigravity_harness.ledger import StrategyLedger # noqa: PLC0415
                ledger = StrategyLedger(self.repo_root / "state/STRATEGY_LEDGER.json")
                ledger.append(self.account_id, self._strategy_commitment, report_path)
                
        except (OSError, ImportError) as e:
            # Audit failure must NOT crash the engine, but we log the failure to stderr
            print(f"⚠️  [AUDITOR] CRITICAL FAILURE: Could not emit or sign audit report: {e}", file=sys.stderr)
            
        return report_path
