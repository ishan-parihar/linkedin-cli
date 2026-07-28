"""
Performance metrics and alerting for Obscura operations.

Provides comprehensive performance tracking and alerting to ensure
Obscura backend performance meets expectations and enables proactive issue detection.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from collections import deque
import statistics

from linkedin_mcp_server.core.obscura_monitoring import get_metrics_collector

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Track performance metrics for Obscura operations."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        
        self._latency_samples: deque = deque(maxlen=window_size)
        self._throughput_samples: deque = deque(maxlen=window_size)
        self._error_samples: deque = deque(maxlen=window_size)
        
        self._baselines: Dict[str, float] = {}
        self._performance_alerts: List[Dict[str, Any]] = []
        
        logger.info("Performance tracker initialized with window size: %d", window_size)
    
    def record_latency(self, operation: str, latency: float) -> None:
        """Record latency for an operation."""
        self._latency_samples.append({
            "operation": operation,
            "latency": latency,
            "timestamp": time.time(),
        })
        
        # Update baseline if not set
        if operation not in self._baselines:
            self._baselines[operation] = latency
            logger.info("Set baseline latency for %s: %.3fs", operation, latency)
    
    def record_throughput(self, operations_per_second: float) -> None:
        """Record throughput metric."""
        self._throughput_samples.append({
            "throughput": operations_per_second,
            "timestamp": time.time(),
        })
    
    def record_error(self, operation: str, error_type: str) -> None:
        """Record an error occurrence."""
        self._error_samples.append({
            "operation": operation,
            "error_type": error_type,
            "timestamp": time.time(),
        })
    
    def get_latency_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get latency statistics."""
        samples = [
            s for s in self._latency_samples
            if operation is None or s["operation"] == operation
        ]
        
        if not samples:
            return {
                "operation": operation or "all",
                "count": 0,
                "avg_latency": 0,
                "p50_latency": 0,
                "p95_latency": 0,
                "p99_latency": 0,
                "min_latency": 0,
                "max_latency": 0,
            }
        
        latencies = [s["latency"] for s in samples]
        
        return {
            "operation": operation or "all",
            "count": len(samples),
            "avg_latency": statistics.mean(latencies),
            "p50_latency": statistics.median(latencies),
            "p95_latency": self._percentile(latencies, 95),
            "p99_latency": self._percentile(latencies, 99),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
        }
    
    def get_throughput_stats(self) -> Dict[str, Any]:
        """Get throughput statistics."""
        if not self._throughput_samples:
            return {
                "count": 0,
                "avg_throughput": 0,
                "max_throughput": 0,
                "min_throughput": 0,
            }
        
        throughputs = [s["throughput"] for s in self._throughput_samples]
        
        return {
            "count": len(throughputs),
            "avg_throughput": statistics.mean(throughputs),
            "max_throughput": max(throughputs),
            "min_throughput": min(throughputs),
        }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        if not self._error_samples:
            return {
                "total_errors": 0,
                "error_rate": 0,
                "error_types": {},
            }
        
        total_operations = len(self._latency_samples)
        error_count = len(self._error_samples)
        
        error_types = {}
        for sample in self._error_samples:
            error_type = sample["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": error_count,
            "error_rate": error_count / total_operations if total_operations > 0 else 0,
            "error_types": error_types,
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def check_performance_regression(self, threshold: float = 0.2) -> List[str]:
        """Check for performance regression against baselines."""
        regressions = []
        
        for operation, baseline in self._baselines.items():
            stats = self.get_latency_stats(operation)
            current_avg = stats["avg_latency"]
            
            if current_avg > baseline * (1 + threshold):
                regression = f"{operation} latency degraded by {((current_avg - baseline) / baseline) * 100:.1f}% (baseline: {baseline:.3fs, current: {current_avg:.3fs})"
                regressions.append(regression)
                logger.warning("Performance regression detected: %s", regression)
        
        return regressions
    
    def create_performance_alert(self, alert_type: str, message: str, details: Dict[str, Any]) -> None:
        """Create a performance alert."""
        alert = {
            "type": alert_type,
            "message": message,
            "details": details,
            "timestamp": time.time(),
        }
        
        self._performance_alerts.append(alert)
        logger.warning("PERFORMANCE ALERT [%s]: %s", alert_type, message)
    
    def get_performance_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent performance alerts."""
        return self._performance_alerts[-limit:]


class AlertManager:
    """Manage performance and operational alerts."""
    
    def __init__(self):
        self._alert_rules: Dict[str, Dict[str, Any]] = {
            "high_latency": {
                "threshold": 5.0,
                "description": "Operation latency exceeds threshold",
                "severity": "warning",
            },
            "low_throughput": {
                "threshold": 0.1,
                "description": "Throughput falls below threshold",
                "severity": "warning",
            },
            "high_error_rate": {
                "threshold": 0.1,
                "description": "Error rate exceeds threshold",
                "severity": "critical",
            },
            "memory_spike": {
                "threshold": 100,  # MB
                "description": "Memory usage exceeds threshold",
                "severity": "warning",
            },
        }
        
        self._active_alerts: Dict[str, Dict[str, Any]] = {}
        self._alert_history: List[Dict[str, Any]] = []
        
        logger.info("Alert manager initialized with %d rules", len(self._alert_rules))
    
    def check_alert_conditions(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any alert conditions are met."""
        triggered_alerts = []
        
        # Check high latency
        if "avg_latency" in metrics and metrics["avg_latency"] > self._alert_rules["high_latency"]["threshold"]:
            triggered_alerts.append({
                "rule": "high_latency",
                "value": metrics["avg_latency"],
                "threshold": self._alert_rules["high_latency"]["threshold"],
                "severity": self._alert_rules["high_latency"]["severity"],
            })
        
        # Check low throughput
        if "throughput" in metrics and metrics["throughput"] < self._alert_rules["low_throughput"]["threshold"]:
            triggered_alerts.append({
                "rule": "low_throughput",
                "value": metrics["throughput"],
                "threshold": self._alert_rules["low_throughput"]["threshold"],
                "severity": self._alert_rules["low_throughput"]["severity"],
            })
        
        # Check high error rate
        if "error_rate" in metrics and metrics["error_rate"] > self._alert_rules["high_error_rate"]["threshold"]:
            triggered_alerts.append({
                "rule": "high_error_rate",
                "value": metrics["error_rate"],
                "threshold": self._alert_rules["high_error_rate"]["threshold"],
                "severity": self._alert_rules["high_error_rate"]["severity"],
            })
        
        # Process triggered alerts
        for alert in triggered_alerts:
            self._process_alert(alert)
        
        return triggered_alerts
    
    def _process_alert(self, alert: Dict[str, Any]) -> None:
        """Process a triggered alert."""
        rule_name = alert["rule"]
        rule_config = self._alert_rules[rule_name]
        
        # Add to active alerts if not already present
        if rule_name not in self._active_alerts:
            self._active_alerts[rule_name] = {
                **alert,
                "triggered_at": time.time(),
                "description": rule_config["description"],
            }
            logger.warning(
                "Alert triggered: %s (value: %s, threshold: %s, severity: %s)",
                rule_name, alert["value"], alert["threshold"], alert["severity"]
            )
        
        # Add to history
        self._alert_history.append({
            **alert,
            "resolved_at": None,
            "description": rule_config["description"],
        })
    
    def resolve_alert(self, rule_name: str) -> None:
        """Resolve an active alert."""
        if rule_name in self._active_alerts:
            alert = self._active_alerts[rule_name]
            alert["resolved_at"] = time.time()
            
            # Add to history
            self._alert_history.append(alert)
            
            # Remove from active
            del self._active_alerts[rule_name]
            
            logger.info("Alert resolved: %s", rule_name)
    
    def get_active_alerts(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active alerts."""
        return self._active_alerts.copy()
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self._alert_history[-limit:]


# Global instances
_performance_tracker: PerformanceTracker | None = None
_alert_manager: AlertManager | None = None


def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker instance."""
    global _performance_tracker
    
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    
    return _performance_tracker


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    
    if _alert_manager is None:
        _alert_manager = AlertManager()
    
    return _alert_manager


async def initialize_performance_tracking(window_size: int = 100) -> None:
    """Initialize performance tracking with specific settings."""
    global _performance_tracker, _alert_manager
    
    _performance_tracker = PerformanceTracker(window_size=window_size)
    _alert_manager = AlertManager()
    
    logger.info("Initialized performance tracking with window size: %d", window_size)