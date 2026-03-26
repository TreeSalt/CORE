---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: IMPLEMENTATION
STATUS: PENDING_REVIEW
---

```python
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CoreStatusV3')


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceStatusInfo:
    service_name: str
    status: ServiceStatus
    last_heartbeat: Optional[datetime] = None
    error_message: Optional[str] = None
    uptime_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatusReport:
    report_id: str
    timestamp: datetime
    services_status: Dict[str, ServiceStatusInfo]
    overall_health: ServiceStatus
    message: Optional[str] = None


class CoreStatusManagerV3:
    """Core status management and orchestration v3."""
    
    def __init__(self, default_interval_seconds: float = 60.0):
        self.default_interval = default_interval_seconds
        self.service_statuses: Dict[str, ServiceStatusInfo] = {}
        self.status_history: List[StatusReport] = []
        self._uptime_start: Optional[datetime] = None
        self._running = True
    
    def start(self) -> None:
        """Start the status manager."""
        self._uptime_start = datetime.now()
        logger.info("CoreStatusManagerV3 started")
    
    def stop(self) -> None:
        """Stop the status manager."""
        self._running = False
        self._uptime_start = None
        logger.info("CoreStatusManagerV3 stopped")
    
    def get_uptime_seconds(self) -> float:
        """Get current uptime in seconds."""
        if self._uptime_start:
            return (datetime.now() - self._uptime_start).total_seconds()
        return 0.0
    
    def register_service(
        self, 
        name: str, 
        status: ServiceStatus = ServiceStatus.HEALTHY,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceStatusInfo:
        """Register a service with initial status."""
        now = datetime.now()
        
        self.service_statuses[name] = ServiceStatusInfo(
            service_name=name,
            status=status,
            last_heartbeat=now,
            uptime_seconds=self.get_uptime_seconds() if self._uptime_start else 0.0,
            metadata=metadata or {}
        )
        
        logger.info(f"Registered service: {name} - status: {status.value}")
        return self.service_statuses[name]
    
    def update_service_status(
        self,
        service_name: str,
        status: ServiceStatus,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ServiceStatusInfo]:
        """Update a service's status."""
        if service_name not in self.service_statuses:
            logger.warning(f"Service not found: {service_name}")
            return None
        
        info = self.service_statuses[service_name]
        now = datetime.now()
        
        # Calculate uptime
        if info.last_heartbeat and self._uptime_start:
            elapsed_since_last = (now - info.last_heartbeat).total_seconds()
            info.uptime_seconds = info.uptime_seconds + elapsed_since_last
        
        info.status = status
        info.last_heartbeat = now
        info.error_message = error_message
        
        if metadata:
            info.metadata.update(metadata)
        
        # Log degraded/healthy changes
        prev_status = ServiceStatus(info.metadata.get('last_status', 'N/A')) if info.metadata else None
        if str(prev_status) != status.value:
            logger.info(f"Updated service {service_name}: {prev_status.value} -> {status.value}")
        
        return info
    
    def set_service_unhealthy(
        self,
        service_name: str,
        error_message: Optional[str] = None
    ) -> Optional[ServiceStatusInfo]:
        """Mark a service as unhealthy."""
        return self.update_service_status(
            service_name=service_name,
            status=ServiceStatus.UNHEALTHY,
            error_message=error_message
        )
    
    def set_service_degraded(
        self,
        service_name: str,
        error_message: Optional[str] = None
    ) -> Optional[ServiceStatusInfo]:
        """Mark a service as degraded."""
        return self.update_service_status(
            service_name=service_name,
            status=ServiceStatus.DEGRADED,
            error_message=error_message
        )
    
    def set_service_healthy(self, service_name: str) -> Optional[ServiceStatusInfo]:
        """Mark a service as healthy."""
        return self.update_service_status(
            service_name=service_name,
            status=ServiceStatus.HEALTHY
        )
    
    def get_status_report(self, include_history: bool = False) -> StatusReport:
        """Generate a current status report."""
        if not self._uptime_start:
            self.start()
        
        now = datetime.now()
        services_status = dict(self.service_statuses)
        
        # Determine overall health
        statuses = [info.status for info in self.service_statuses.values()]
        
        if all(s == ServiceStatus.HEALTHY for s in statuses):
            overall_health = ServiceStatus.HEALTHY
            message = "All services healthy"
        elif not any(s in [ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY] for s in statuses):
            overall_health = ServiceStatus.HEALTHY
            message = "All services operational"
        else:
            unhealthy_count = sum(1 for s in statuses if s == ServiceStatus.UNHEALTHY)
            if unhealthy_count > 0:
                overall_health = ServiceStatus.UNHEALTHY
                message = f"{unhealthy_count} service(s) unhealthy"
            else:
                overall_health = ServiceStatus.DEGRADED
                message = "Some services degraded"
        
        report = StatusReport(
            report_id=f"rpt-{now.strftime('%Y%m%d-%H%M%S')}-{len(self.status_history)}",
            timestamp=now,
            services_status=services_status,
            overall_health=overall_health,
            message=message
        )
        
        self.status_history.append(report)
        
        logger.info(f"Status report generated: {overall_health.value}")
        
        return report
    
    def get_all_statuses(self) -> Dict[str, ServiceStatusInfo]:
        """Get all current service statuses."""
        return dict(self.service_statuses)
    
    def get_service_by_name(self, name: str) -> Optional[ServiceStatusInfo]:
        """Get a specific service status by name."""
        return self.service_statuses.get(name)
    
    def check_heartbeat(self, service_name: str, interval_seconds: float = None) -> bool:
        """Check if a service heartbeat is within acceptable interval."""
        if service_name not in self.service_statuses:
            return False
        
        info = self.service_statuses[service_name]
        now = datetime.now()
        
        if info.last_heartbeat:
            elapsed = (now - info.last_heartbeat).total_seconds()
            actual_interval = interval_seconds or self.default_interval
            
            # Mark unhealthy if heartbeat missed 2 intervals
            if elapsed > actual_interval * 2:
                self.set_service_unhealthy(service_name, 
                    f"Heartbeat missed for {elapsed:.1f} seconds (threshold: {actual_interval}s)")
                return False
            
            # Mark degraded if heartbeat delayed beyond threshold
            if elapsed > actual_interval:
                self.set_service_degraded(service_name,
                    f"Heartbeat delayed by {elapsed:.1f} seconds")
            
            return True
        
        return True
    
    def reset_heartbeat(self, service_name: str) -> bool:
        """Reset a service's heartbeat timestamp."""
        if service_name not in self.service_statuses:
            return False
        
        self.service_statuses[service_name].last_heartbeat = datetime.now()
        logger.info(f"Heartbeat reset for service: {service_name}")
        return True
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of the system health."""
        report = self.get_status_report()
        
        healthy_count = sum(1 for s in self.service_statuses.values() 
                           if s.status == ServiceStatus.HEALTHY)
        degraded_count = sum(1 for s in self.service_statuses.values() 
                             if s.status == ServiceStatus.DEGRADED)
        unhealthy_count = sum(1 for s in self.service_statuses.values() 
                              if s.status == ServiceStatus.UNHEALTHY)
        
        return {
            "timestamp": report.timestamp.isoformat(),
            "overall_health": report.overall_health.value,
            "message": report.message,
            "service_count": len(self.service_statuses),
            "healthy_services": healthy_count,
            "degraded_services": degraded_count,
            "unhealthy_services": unhealthy_count,
            "uptime_seconds": self.get_uptime_seconds(),
            "reports_generated": len(self.status_history)
        }
    
    def export_status_json(self) -> str:
        """Export current status to JSON string."""
        summary = self.get_health_summary()
        
        # Add detailed service info
        services_detail = {}
        for name, info in self.service_statuses.items():
            service_detail = {
                "name": info.service_name,
                "status": info.status.value,
                "last_heartbeat": info.last_heartbeat.isoformat() if info.last_heartbeat else None,
                "error_message": info.error_message,
                "uptime_seconds": round(info.uptime_seconds, 2)
            }
            if info.metadata:
                service_detail["metadata"] = info.metadata
            
            services_detail[name] = service_detail
        
        export_data = {
            "summary": summary,
            "services": services_detail,
            "history_count": len(self.status_history)
        }
        
        return json.dumps(export_data, indent=2, default=str)


# Singleton instance for easy access
_status_manager_instance: Optional[CoreStatusManagerV3] = None


def get_status_manager() -> CoreStatusManagerV3:
    """Get or create the singleton status manager instance."""
    global _status_manager_instance
    if _status_manager_instance is None:
        _status_manager_instance = CoreStatusManagerV3()
        _status_manager_instance.start()
    return _status_manager_instance


def register_core_service(name: str, metadata: Optional[Dict] = None) -> ServiceStatusInfo:
    """Convenience function to register a core service."""
    manager = get_status_manager()
    return manager.register_service(name=name, metadata=metadata)


def update_core_service(
    name: str,
    status: ServiceStatus,
    error_message: Optional[str] = None
) -> Optional[ServiceStatusInfo]:
    """Convenience function to update a core service status."""
    manager = get_status_manager()
    return manager.update_service_status(name, status, error_message)


def get_core_status_report(include_history: bool = False) -> StatusReport:
    """Convenience function to get current status report."""
    manager = get_status_manager()
    return manager.get_status_report(include_history=include_history)


if __name__ == "__main__":
    # Demo usage
    print("CoreStatusManagerV3 initialized")
    
    mgr = CoreStatusManagerV3(default_interval_seconds=60.0)
    mgr.start()
    
    # Register some services
    mgr.register_service("database", ServiceStatus.HEALTHY, {"type": "postgres"})
    mgr.register_service("cache", ServiceStatus.HEALTHY, {"type": "redis"})
    mgr.register_service("api_gateway", ServiceStatus.DEGRADED, {"reason": "high_latency"})
    
    # Generate initial report
    print("\n--- Initial Status Report ---")
    print(mgr.get_status_report().__dict__)
    
    # Simulate time passing and heartbeat checks
    time.sleep(0.1)
    
    # Check heartbeats
    for name in mgr.service_statuses:
        mgr.check_heartbeat(name, interval_seconds=60)
    
    # Get updated report
    print("\n--- Updated Status Report ---")
    print(mgr.get_status_report())
    
    # Export to JSON
    print("\n--- JSON Export ---")
    print(mgr.export_status_json())
    
    # Cleanup
    mgr.stop()
```