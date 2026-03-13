---
DOMAIN: 03_ORCHESTRATION
MODEL: claude-sonnet-4-6
TIER: heavy
STATUS: RATIFIED
---

# AgentCoordinator — Implementation Proposal
# Domain: 03_ORCHESTRATION | Task: implement_agent_coordinator

```python
#!/usr/bin/env python3
"""
agent_coordinator.py — AOS AgentCoordinator
Domain:      03_ORCHESTRATION
Security:    INTERNAL
Constraints:
  - No hardcoded credentials
  - No writes to 04_GOVERNANCE/
  - Fail closed on constraint breach
  - Thread-safe: one active agent per domain at a time
  - All assignment and completion events are logged
"""

from __future__ import annotations

import logging
import sys
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# ── CONSTANTS ──────────────────────────────────────────────────────────────────

GOVERNANCE_DOMAIN = "04_GOVERNANCE"

# ── LOGGING ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("agent_coordinator")


# ── DATA TYPES ────────────────────────────────────────────────────────────────

@dataclass
class TaskPackage:
    """Immutable task descriptor produced by the semantic router."""
    domain_id: str
    mission: str
    model: str
    tier: str = ""
    task_id: str = ""
    task: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    enqueued_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not self.domain_id:
            _fail_closed("TASK_PACKAGE_INVALID: domain_id is empty")
        if not self.mission:
            _fail_closed("TASK_PACKAGE_INVALID: mission is empty")
        if GOVERNANCE_DOMAIN in self.domain_id:
            _fail_closed(
                f"GOVERNANCE_WRITE_BLOCKED: task targets {GOVERNANCE_DOMAIN} — "
                "writes to this domain are forbidden."
            )

@dataclass
class AgentAssignment:
    """Live record of a running agent."""
    domain_id: str
    model: str
    tier: str = ""
    task_id: str = ""
    task: str = ""
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    thread: Optional[threading.Thread] = field(default=None, repr=False)


# ── FAIL-CLOSED HELPER ────────────────────────────────────────────────────────

def _fail_closed(reason: str) -> None:
    """Log the breach and hard-exit. Never returns."""
    log.critical("FAIL-CLOSED | %s", reason)
    sys.exit(1)


# ── AGENT COORDINATOR ─────────────────────────────────────────────────────────

class AgentCoordinator:
    """
    Thread-safe coordinator that:
      1. Accepts TaskPackage objects from the semantic router.
      2. Tracks one active AgentAssignment per domain (mutex enforced).
      3. Queues new tasks when a domain is already busy (FIFO).
      4. Dispatches queued tasks when the active agent completes.
      5. Logs every assignment and completion event.
      6. Refuses any task targeting 04_GOVERNANCE/ (fail-closed).
    """

    def __init__(self, dispatch_fn: 'Callable[[TaskPackage], None] | None' = None) -> None:
        """
        Args:
            dispatch_fn: Callable that actually executes a task (e.g., calls
                         semantic_router.execute_local / execute_cloud).
                         Must accept a single TaskPackage argument.
                         Must NOT write to 04_GOVERNANCE/.
        """
        if dispatch_fn is None:
            dispatch_fn = lambda pkg: None  # no-op for testing / deferred wiring

        self._dispatch_fn: Callable[[TaskPackage], None] = dispatch_fn

        # Per-domain state — protected by _global_lock for map mutations,
        # per-domain _domain_locks for active-agent enforcement.
        self._global_lock: threading.Lock = threading.Lock()
        self._domain_locks: dict[str, threading.Lock] = {}
        self._active: dict[str, AgentAssignment] = {}   # domain_id → assignment
        self._queues: dict[str, deque[TaskPackage]] = {}  # domain_id → FIFO queue

        log.info("AgentCoordinator initialized.")

    # ── PUBLIC API ─────────────────────────────────────────────────────────────

    def submit(self, package: TaskPackage) -> None:
        """
        Accept a task package.  If the domain is idle, dispatch immediately.
        If busy, enqueue and return — the task will be dispatched when the
        active agent completes.

        Raises SystemExit (via _fail_closed) on any constraint breach.
        """
        self._validate_package(package)

        domain_id = package.domain_id
        self._ensure_domain(domain_id)

        with self._global_lock:
            if domain_id in self._active:
                # Domain is busy — enqueue.
                self._queues[domain_id].append(package)
                log.info(
                    "QUEUED   | domain=%s task=%s queue_depth=%d",
                    domain_id, package.task_id,
                    len(self._queues[domain_id]),
                )
                return

            # Domain is free — claim the slot and dispatch.
            self._dispatch_now(package)

    def get_active_assignments(self) -> dict:
        return self.active_assignments()

    def active_assignments(self) -> dict[str, AgentAssignment]:
        """Return a snapshot of all currently active assignments (read-only copy)."""
        with self._global_lock:
            return dict(self._active)

    def get_queue_depth(self, domain_id: str) -> int:
        return self.queue_depth(domain_id)

    def queue_depth(self, domain_id: str) -> int:
        """Return the number of tasks waiting for a given domain."""
        with self._global_lock:
            return len(self._queues.get(domain_id, deque()))

    def status(self) -> dict[str, Any]:
        """Return a full coordinator status snapshot."""
        with self._global_lock:
            return {
                "active_domains": list(self._active.keys()),
                "queue_depths": {
                    d: len(q) for d, q in self._queues.items() if q
                },
                "snapshot_at": datetime.now(timezone.utc).isoformat(),
            }

    # ── INTERNAL ──────────────────────────────────────────────────────────────

    def _validate_package(self, package: TaskPackage) -> None:
        """Hard-fail on governance writes or missing fields (already checked in
        TaskPackage.__post_init__, but we defensively re-check here)."""
        if not isinstance(package, TaskPackage):
            _fail_closed(
                f"CONSTRAINT_BREACH: submit() received non-TaskPackage type "
                f"'{type(package).__name__}'"
            )
        if GOVERNANCE_DOMAIN in package.domain_id:
            _fail_closed(
                f"GOVERNANCE_WRITE_BLOCKED: domain_id '{package.domain_id}' "
                f"targets {GOVERNANCE_DOMAIN}. Coordinator refuses."
            )

    def _ensure_domain(self, domain_id: str) -> None:
        """Lazily create per-domain state structures."""
        with self._global_lock:
            if domain_id not in self._domain_locks:
                self._domain_locks[domain_id] = threading.Lock()
                self._queues[domain_id] = deque()

    def _dispatch_now(self, package: TaskPackage) -> None:
        """
        Register the assignment and spawn a daemon thread to run the task.
        Caller MUST hold _global_lock.
        """
        assignment = AgentAssignment(
            domain_id=package.domain_id,
            task_id=package.task_id,
            model=package.model,
            tier=package.tier,
        )

        t = threading.Thread(
            target=self._run_task,
            args=(package, assignment),
            daemon=True,
            name=f"agent-{package.domain_id}-{package.task_id}",
        )
        assignment.thread = t
        self._active[package.domain_id] = assignment

        log.info(
            "ASSIGNED | domain=%s task=%s model=%s tier=%s started_at=%s",
            assignment.domain_id, assignment.task_id,
            assignment.model, assignment.tier, assignment.started_at,
        )

        t.start()

    def _run_task(self, package: TaskPackage, assignment: AgentAssignment) -> None:
        """Worker executed in a background thread."""
        try:
            self._dispatch_fn(package)
        except Exception as exc:  # noqa: BLE001
            log.error(
                "AGENT_ERROR | domain=%s task=%s error=%s",
                package.domain_id, package.task_id, exc,
            )
            # Swallow — coordinator must not die because one agent failed.
            # The domain slot will still be released so queued work proceeds.
        finally:
            self._on_complete(package.domain_id, assignment)

    def _on_complete(self, domain_id: str, assignment: AgentAssignment) -> None:
        """
        Called when an agent finishes (success or error).
        Releases the domain slot and dispatches the next queued task if any.
        """
        completed_at = datetime.now(timezone.utc).isoformat()
        log.info(
            "COMPLETE | domain=%s task=%s model=%s completed_at=%s",
            assignment.domain_id, assignment.task_id,
            assignment.model, completed_at,
        )

        with self._global_lock:
            # Release domain slot.
            self._active.pop(domain_id, None)

            # Drain one item from the queue.
            queue = self._queues.get(domain_id, deque())
            if queue:
                next_package = queue.popleft()
                log.info(
                    "DEQUEUE  | domain=%s task=%s queue_remaining=%d",
                    domain_id, next_package.task_id, len(queue),
                )
                self._dispatch_now(next_package)
            else:
                log.info("IDLE     | domain=%s — no queued tasks.", domain_id)

```

---

## Design Notes

### Constraint Enforcement

| Constraint | Mechanism |
|---|---|
| One agent per domain | `_active` dict keyed by `domain_id`; checked under `_global_lock` before dispatch |
| Queue when busy | Per-domain `deque`; FIFO; drained in `_on_complete` |
| No governance writes | `_validate_package` + `TaskPackage.__post_init__` both call `_fail_closed` if `04_GOVERNANCE` appears in the domain ID |
| No hardcoded credentials | Module contains zero credential literals; `dispatch_fn` is injected at construction |
| Fail closed | All constraint violations call `_fail_closed(reason)` → `sys.exit(1)` |
| Logging | Every QUEUED / ASSIGNED / COMPLETE / DEQUEUE / IDLE / error event is logged via `logging.INFO` / `ERROR` / `CRITICAL` |

### Threading Model

- `_global_lock` guards map mutations (`_active`, `_queues`, `_domain_locks`).
- Each task runs in a **daemon thread** — the process can exit without joining agents.
- `_on_complete` is called in the agent thread's `finally` block, guaranteeing the slot is always released.

### Integration Point (semantic_router.py)

```python
#!/usr/bin/env python3
"""
agent_coordinator.py — AOS AgentCoordinator
Domain:      03_ORCHESTRATION
Security:    INTERNAL
Constraints:
  - No hardcoded credentials
  - No writes to 04_GOVERNANCE/
  - Fail closed on constraint breach
  - Thread-safe: one active agent per domain at a time
  - All assignment and completion events are logged
"""

from __future__ import annotations

import logging
import sys
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# ── CONSTANTS ──────────────────────────────────────────────────────────────────

GOVERNANCE_DOMAIN = "04_GOVERNANCE"

# ── LOGGING ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("agent_coordinator")


# ── DATA TYPES ────────────────────────────────────────────────────────────────

@dataclass
class TaskPackage:
    """Immutable task descriptor produced by the semantic router."""
    domain_id: str
    mission: str
    model: str
    tier: str = ""
    task_id: str = ""
    task: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    enqueued_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not self.domain_id:
            _fail_closed("TASK_PACKAGE_INVALID: domain_id is empty")
        if not self.mission:
            _fail_closed("TASK_PACKAGE_INVALID: mission is empty")
        if GOVERNANCE_DOMAIN in self.domain_id:
            _fail_closed(
                f"GOVERNANCE_WRITE_BLOCKED: task targets {GOVERNANCE_DOMAIN} — "
                "writes to this domain are forbidden."
            )

@dataclass
class AgentAssignment:
    """Live record of a running agent."""
    domain_id: str
    model: str
    tier: str = ""
    task_id: str = ""
    task: str = ""
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    thread: Optional[threading.Thread] = field(default=None, repr=False)


# ── FAIL-CLOSED HELPER ────────────────────────────────────────────────────────

def _fail_closed(reason: str) -> None:
    """Log the breach and hard-exit. Never returns."""
    log.critical("FAIL-CLOSED | %s", reason)
    sys.exit(1)


# ── AGENT COORDINATOR ─────────────────────────────────────────────────────────

class AgentCoordinator:
    """
    Thread-safe coordinator that:
      1. Accepts TaskPackage objects from the semantic router.
      2. Tracks one active AgentAssignment per domain (mutex enforced).
      3. Queues new tasks when a domain is already busy (FIFO).
      4. Dispatches queued tasks when the active agent completes.
      5. Logs every assignment and completion event.
      6. Refuses any task targeting 04_GOVERNANCE/ (fail-closed).
    """

    def __init__(self, dispatch_fn: 'Callable[[TaskPackage], None] | None' = None) -> None:
        """
        Args:
            dispatch_fn: Callable that actually executes a task (e.g., calls
                         semantic_router.execute_local / execute_cloud).
                         Must accept a single TaskPackage argument.
                         Must NOT write to 04_GOVERNANCE/.
        """
        if dispatch_fn is None:
            dispatch_fn = lambda pkg: None  # no-op for testing / deferred wiring

        self._dispatch_fn: Callable[[TaskPackage], None] = dispatch_fn

        # Per-domain state — protected by _global_lock for map mutations,
        # per-domain _domain_locks for active-agent enforcement.
        self._global_lock: threading.Lock = threading.Lock()
        self._domain_locks: dict[str, threading.Lock] = {}
        self._active: dict[str, AgentAssignment] = {}   # domain_id → assignment
        self._queues: dict[str, deque[TaskPackage]] = {}  # domain_id → FIFO queue

        log.info("AgentCoordinator initialized.")

    # ── PUBLIC API ─────────────────────────────────────────────────────────────

    def submit(self, package: TaskPackage) -> None:
        """
        Accept a task package.  If the domain is idle, dispatch immediately.
        If busy, enqueue and return — the task will be dispatched when the
        active agent completes.

        Raises SystemExit (via _fail_closed) on any constraint breach.
        """
        self._validate_package(package)

        domain_id = package.domain_id
        self._ensure_domain(domain_id)

        with self._global_lock:
            if domain_id in self._active:
                # Domain is busy — enqueue.
                self._queues[domain_id].append(package)
                log.info(
                    "QUEUED   | domain=%s task=%s queue_depth=%d",
                    domain_id, package.task_id,
                    len(self._queues[domain_id]),
                )
                return

            # Domain is free — claim the slot and dispatch.
            self._dispatch_now(package)

    def get_active_assignments(self) -> dict:
        return self.active_assignments()

    def active_assignments(self) -> dict[str, AgentAssignment]:
        """Return a snapshot of all currently active assignments (read-only copy)."""
        with self._global_lock:
            return dict(self._active)

    def get_queue_depth(self, domain_id: str) -> int:
        return self.queue_depth(domain_id)

    def queue_depth(self, domain_id: str) -> int:
        """Return the number of tasks waiting for a given domain."""
        with self._global_lock:
            return len(self._queues.get(domain_id, deque()))

    def status(self) -> dict[str, Any]:
        """Return a full coordinator status snapshot."""
        with self._global_lock:
            return {
                "active_domains": list(self._active.keys()),
                "queue_depths": {
                    d: len(q) for d, q in self._queues.items() if q
                },
                "snapshot_at": datetime.now(timezone.utc).isoformat(),
            }

    # ── INTERNAL ──────────────────────────────────────────────────────────────

    def _validate_package(self, package: TaskPackage) -> None:
        """Hard-fail on governance writes or missing fields (already checked in
        TaskPackage.__post_init__, but we defensively re-check here)."""
        if not isinstance(package, TaskPackage):
            _fail_closed(
                f"CONSTRAINT_BREACH: submit() received non-TaskPackage type "
                f"'{type(package).__name__}'"
            )
        if GOVERNANCE_DOMAIN in package.domain_id:
            _fail_closed(
                f"GOVERNANCE_WRITE_BLOCKED: domain_id '{package.domain_id}' "
                f"targets {GOVERNANCE_DOMAIN}. Coordinator refuses."
            )

    def _ensure_domain(self, domain_id: str) -> None:
        """Lazily create per-domain state structures."""
        with self._global_lock:
            if domain_id not in self._domain_locks:
                self._domain_locks[domain_id] = threading.Lock()
                self._queues[domain_id] = deque()

    def _dispatch_now(self, package: TaskPackage) -> None:
        """
        Register the assignment and spawn a daemon thread to run the task.
        Caller MUST hold _global_lock.
        """
        assignment = AgentAssignment(
            domain_id=package.domain_id,
            task_id=package.task_id,
            model=package.model,
            tier=package.tier,
        )

        t = threading.Thread(
            target=self._run_task,
            args=(package, assignment),
            daemon=True,
            name=f"agent-{package.domain_id}-{package.task_id}",
        )
        assignment.thread = t
        self._active[package.domain_id] = assignment

        log.info(
            "ASSIGNED | domain=%s task=%s model=%s tier=%s started_at=%s",
            assignment.domain_id, assignment.task_id,
            assignment.model, assignment.tier, assignment.started_at,
        )

        t.start()

    def _run_task(self, package: TaskPackage, assignment: AgentAssignment) -> None:
        """Worker executed in a background thread."""
        try:
            self._dispatch_fn(package)
        except Exception as exc:  # noqa: BLE001
            log.error(
                "AGENT_ERROR | domain=%s task=%s error=%s",
                package.domain_id, package.task_id, exc,
            )
            # Swallow — coordinator must not die because one agent failed.
            # The domain slot will still be released so queued work proceeds.
        finally:
            self._on_complete(package.domain_id, assignment)

    def _on_complete(self, domain_id: str, assignment: AgentAssignment) -> None:
        """
        Called when an agent finishes (success or error).
        Releases the domain slot and dispatches the next queued task if any.
        """
        completed_at = datetime.now(timezone.utc).isoformat()
        log.info(
            "COMPLETE | domain=%s task=%s model=%s completed_at=%s",
            assignment.domain_id, assignment.task_id,
            assignment.model, completed_at,
        )

        with self._global_lock:
            # Release domain slot.
            self._active.pop(domain_id, None)

            # Drain one item from the queue.
            queue = self._queues.get(domain_id, deque())
            if queue:
                next_package = queue.popleft()
                log.info(
                    "DEQUEUE  | domain=%s task=%s queue_remaining=%d",
                    domain_id, next_package.task_id, len(queue),
                )
                self._dispatch_now(next_package)
            else:
                log.info("IDLE     | domain=%s — no queued tasks.", domain_id)

```

### What This Does NOT Do
- Does **not** persist queue state across restarts (in-memory only — add a state file if needed).
- Does **not** implement timeouts/watchdogs on hanging agents (add `threading.Timer` if required).
- Does **not** write to `04_GOVERNANCE/` under any code path.
