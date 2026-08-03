"""
Comprehensive monitoring and logging for Obscura operations.

Provides detailed monitoring, metrics collection, and logging for
Obscura backend operations to ensure observability and debugging capabilities.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ObscuraMetricsCollector:
    """Collect metrics for Obscura operations."""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics

        self._operation_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics))
        self._performance_metrics: Dict[str, List] = defaultdict(list)
        self._error_metrics: Dict[str, int] = defaultdict(int)
        self._session_metrics: Dict[str, Any] = {
            "start_time": time.time(),
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
        }

        logger.info("Obscura metrics collector initialized")

    def record_operation(
        self,
        operation: str,
        duration: float,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an operation metric."""
        metric = {
            "operation": operation,
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
            "details": details or {},
        }

        self._operation_metrics[operation].append(metric)
        self._session_metrics["total_operations"] += 1

        if success:
            self._session_metrics["successful_operations"] += 1
        else:
            self._session_metrics["failed_operations"] += 1
            self._error_metrics[operation] += 1

        # Update performance metrics
        if operation not in self._performance_metrics:
            self._performance_metrics[operation] = []
        self._performance_metrics[operation].append(duration)

        # Keep performance metrics bounded
        if len(self._performance_metrics[operation]) > 1000:
            self._performance_metrics[operation] = self._performance_metrics[operation][-500:]

        logger.debug(
            "Recorded operation metric: %s (%.3fs, success=%s)", operation, duration, success
        )

    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for a specific operation."""
        metrics = list(self._operation_metrics[operation])

        if not metrics:
            return {
                "operation": operation,
                "count": 0,
                "avg_duration": 0,
                "success_rate": 0,
                "min_duration": 0,
                "max_duration": 0,
            }

        successful = [m for m in metrics if m["success"]]
        durations = [m["duration"] for m in metrics]

        return {
            "operation": operation,
            "count": len(metrics),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "success_rate": len(successful) / len(metrics) if metrics else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "error_count": len(metrics) - len(successful),
        }

    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics."""
        uptime = time.time() - self._session_metrics["start_time"]

        operation_stats = {}
        for operation in self._operation_metrics:
            operation_stats[operation] = self.get_operation_stats(operation)

        return {
            **self._session_metrics,
            "uptime_seconds": uptime,
            "operations_per_second": self._session_metrics["total_operations"] / uptime
            if uptime > 0
            else 0,
            "overall_success_rate": (
                self._session_metrics["successful_operations"]
                / self._session_metrics["total_operations"]
                if self._session_metrics["total_operations"] > 0
                else 0
            ),
            "operation_stats": operation_stats,
            "error_summary": dict(self._error_metrics),
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all operations."""
        summary = {
            "slowest_operations": [],
            "fastest_operations": [],
            "most_error_prone": [],
            "total_metrics": sum(len(metrics) for metrics in self._operation_metrics.values()),
        }

        # Find slowest and fastest operations
        operation_avg_durations = []
        for operation, metrics in self._operation_metrics.items():
            if metrics:
                durations = [m["duration"] for m in metrics]
                avg_duration = sum(durations) / len(durations)
                operation_avg_durations.append((operation, avg_duration))

        operation_avg_durations.sort(key=lambda x: x[1], reverse=True)
        summary["slowest_operations"] = operation_avg_durations[:5]
        operation_avg_durations.sort(key=lambda x: x[1])
        summary["fastest_operations"] = operation_avg_durations[:5]

        # Find most error-prone operations
        error_rates = []
        for operation, count in self._error_metrics.items():
            operation_count = len(self._operation_metrics[operation])
            if operation_count > 0:
                error_rate = count / operation_count
                error_rates.append((operation, error_rate))

        error_rates.sort(key=lambda x: x[1], reverse=True)
        summary["most_error_prone"] = error_rates[:5]

        return summary

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._operation_metrics.clear()
        self._performance_metrics.clear()
        self._error_metrics.clear()
        self._session_metrics = {
            "start_time": time.time(),
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
        }
        logger.info("Reset all metrics")


class ObscuraMonitor:
    """Monitor Obscura operations with real-time logging and alerting."""

    def __init__(self, metrics_collector: ObscuraMetricsCollector):
        self.metrics_collector = metrics_collector
        self._alert_thresholds = {
            "slow_operation": 5.0,  # seconds
            "high_error_rate": 0.1,  # 10% error rate
            "low_success_rate": 0.9,  # 90% success rate
        }
        self._alerts: List[Dict[str, Any]] = []

        logger.info("Obscura monitor initialized")

    def check_operation(self, operation: str, duration: float, success: bool) -> None:
        """Check if an operation triggers any alerts."""
        # Check for slow operation
        if duration > self._alert_thresholds["slow_operation"]:
            self._create_alert(
                "slow_operation",
                f"Operation {operation} took {duration:.3fs} (threshold: {self._alert_thresholds['slow_operation']}s)",
                {"operation": operation, "duration": duration},
            )

        # Check operation stats for error rate
        stats = self.metrics_collector.get_operation_stats(operation)
        if stats["count"] > 10:  # Only check after enough samples
            if stats["success_rate"] < self._alert_thresholds["low_success_rate"]:
                self._create_alert(
                    "low_success_rate",
                    f"Operation {operation} has low success rate: {stats['success_rate']:.1%} (threshold: {self._alert_thresholds['low_success_rate']:.1%})",
                    {"operation": operation, "success_rate": stats["success_rate"]},
                )

    def _create_alert(self, alert_type: str, message: str, details: Dict[str, Any]) -> None:
        """Create and log an alert."""
        alert = {
            "type": alert_type,
            "message": message,
            "details": details,
            "timestamp": time.time(),
        }

        self._alerts.append(alert)
        logger.warning("OBSCURA ALERT [%s]: %s", alert_type, message)

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return self._alerts[-limit:]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts."""
        alert_counts = defaultdict(int)
        for alert in self._alerts:
            alert_counts[alert["type"]] += 1

        return {
            "total_alerts": len(self._alerts),
            "alert_counts": dict(alert_counts),
            "recent_alerts": self.get_recent_alerts(10),
        }

    def update_threshold(self, threshold_name: str, value: float) -> None:
        """Update an alert threshold."""
        if threshold_name in self._alert_thresholds:
            self._alert_thresholds[threshold_name] = value
            logger.info("Updated alert threshold %s to %s", threshold_name, value)


class ObscuraStructuredLogger:
    """Structured logger for Obscura operations with JSON output."""

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = (
            log_file
            or Path.home()
            / ".linkedin-lyr"
            / "obscura_logs"
            / f"obscura_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Obscura structured logger initialized with log file: %s", self.log_file)

    def log_operation(
        self, operation: str, status: str, duration: float, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an operation in structured JSON format."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "status": status,
            "duration": duration,
            "details": details or {},
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error("Failed to write structured log: %s", e)

    def log_error(
        self, operation: str, error: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an error in structured format."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "status": "error",
            "error": error,
            "details": details or {},
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error("Failed to write structured error log: %s", e)


class ObscuraHealthChecker:
    """Health checker for Obscura backend."""

    def __init__(self):
        self._last_health_check: Optional[float] = None
        self._health_status: str = "unknown"
        self._health_details: Dict[str, Any] = {}

    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        self._last_health_check = time.time()

        health_details = {
            "timestamp": self._last_health_check,
            "binary_available": False,
            "binary_executable": False,
            "basic_functionality": False,
            "cookie_status": "unknown",
            "storage_status": "unknown",
        }

        # Check binary
        from pathlib import Path

        obscura_path = Path("/tmp/obscura")
        health_details["binary_available"] = obscura_path.exists()

        if health_details["binary_available"]:
            import os

            health_details["binary_executable"] = os.access(obscura_path, os.X_OK)

        # Check basic functionality
        if health_details["binary_executable"]:
            try:
                import subprocess

                result = subprocess.run(
                    [str(obscura_path), "--help"], capture_output=True, text=True, timeout=5
                )
                health_details["basic_functionality"] = result.returncode == 0
            except Exception as e:
                health_details["basic_functionality"] = False
                health_details["error"] = str(e)

        # Check cookie status
        try:
            from linkedin_mcp_server.core.obscura_cookie_management import get_cookie_manager

            cookie_manager = get_cookie_manager()
            cookies = await cookie_manager.load_cookies()
            health_details["cookie_status"] = "loaded" if cookies else "missing"
        except Exception as e:
            health_details["cookie_status"] = "error"
            health_details["cookie_error"] = str(e)

        # Check storage status
        storage_dir = Path.home() / ".linkedin-lyr" / "profile"
        health_details["storage_status"] = "available" if storage_dir.exists() else "missing"

        # Determine overall health
        health_status = "healthy"
        if not health_details["binary_available"]:
            health_status = "unhealthy"
        elif not health_details["binary_executable"]:
            health_status = "unhealthy"
        elif not health_details["basic_functionality"]:
            health_status = "degraded"
        elif health_details["cookie_status"] == "missing":
            health_status = "degraded"

        self._health_status = health_status
        self._health_details = health_details

        logger.info("Obscura health check: %s", health_status)

        return {
            "status": health_status,
            "details": health_details,
        }

    def get_health_status(self) -> str:
        """Get current health status."""
        return self._health_status

    def get_health_details(self) -> Dict[str, Any]:
        """Get detailed health information."""
        return self._health_details


# Global instances
_metrics_collector: ObscuraMetricsCollector | None = None
_monitor: ObscuraMonitor | None = None
_structured_logger: ObscuraStructuredLogger | None = None
_health_checker: ObscuraHealthChecker | None = None


def get_metrics_collector() -> ObscuraMetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = ObscuraMetricsCollector()

    return _metrics_collector


def get_monitor() -> ObscuraMonitor:
    """Get the global monitor instance."""
    global _monitor

    if _monitor is None:
        _monitor = ObscuraMonitor(get_metrics_collector())

    return _monitor


def get_structured_logger() -> ObscuraStructuredLogger:
    """Get the global structured logger instance."""
    global _structured_logger

    if _structured_logger is None:
        _structured_logger = ObscuraStructuredLogger()

    return _structured_logger


def get_health_checker() -> ObscuraHealthChecker:
    """Get the global health checker instance."""
    global _health_checker

    if _health_checker is None:
        _health_checker = ObscuraHealthChecker()

    return _health_checker


async def initialize_monitoring(log_file: Optional[Path] = None) -> None:
    """Initialize monitoring with specific settings."""
    global _metrics_collector, _monitor, _structured_logger, _health_checker

    _metrics_collector = ObscuraMetricsCollector()
    _monitor = ObscuraMonitor(_metrics_collector)
    _structured_logger = ObscuraStructuredLogger(log_file)
    _health_checker = ObscuraHealthChecker()

    logger.info("Initialized comprehensive monitoring system")
