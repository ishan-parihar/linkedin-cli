# Fallback Strategy for Failed Alternatives

## Fallback Architecture

### Multi-Layer Fallback System
```
┌─────────────────────────────────────────────────────────────┐
│                    Primary Backend                           │
│                  (Obscura / Lightpanda)                       │
└─────────────────────────────────────────────────────────────┘
                          │
                    Health Check
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         Healthy                Unhealthy
              │                       │
              ▼                       ▼
        Continue              Fallback to Playwright
              │                       │
              ▼                       ▼
        Success?               Health Check
              │                       │
       ┌──────┴──────┐          ┌──────┴──────┐
       ▼             ▼          ▼             ▼
    Yes            No       Healthy      Unhealthy
       │             │          │             │
       ▼             ▼          ▼             ▼
   Continue     Try Alternate  Continue    Critical Error
                   Backend                   (Alert)
```

## Health Check System

### Component Health Checks
```python
class BackendHealthChecker:
    """Health monitoring for browser backends."""
    
    async def check_backend_health(self, backend: str) -> HealthStatus:
        """Comprehensive health check for backend."""
        checks = [
            self._check_process_running(),
            self._check_cdp_connection(),
            self._check_basic_functionality(),
            self._check_linkedin_compatibility(),
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        return self._evaluate_health(results)
    
    async def _check_process_running(self) -> bool:
        """Check if backend process is running."""
        if self.backend == "playwright":
            return True  # Managed internally
        else:
            return await self._check_external_process()
    
    async def _check_cdp_connection(self) -> bool:
        """Check CDP endpoint connectivity."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.cdp_url, timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False
    
    async def _check_basic_functionality(self) -> bool:
        """Test basic browser functionality."""
        try:
            manager = UnifiedBrowserManager(self.backend)
            await manager.start()
            await manager.page.goto("about:blank")
            await manager.close()
            return True
        except Exception:
            return False
    
    async def _check_linkedin_compatibility(self) -> bool:
        """Test LinkedIn-specific functionality."""
        try:
            manager = UnifiedBrowserManager(self.backend)
            await manager.start()
            await manager.page.goto("https://www.linkedin.com")
            # Check for LinkedIn-specific elements
            content = await manager.page.title()
            await manager.close()
            return "LinkedIn" in content or "linkedin" in content.lower()
        except Exception:
            return False
```

### Health Status Classification
```python
@dataclass
class HealthStatus:
    """Health status classification."""
    backend: str
    status: Literal["healthy", "degraded", "unhealthy", "critical"]
    process_running: bool
    cdp_connected: bool
    basic_functionality: bool
    linkedin_compatible: bool
    last_check: datetime
    error_details: list[str] = field(default_factory=list)
    
    @property
    def can_serve(self) -> bool:
        """Whether backend can serve requests."""
        return self.status in ("healthy", "degraded")
    
    @property
    def needs_fallback(self) -> bool:
        """Whether fallback should be triggered."""
        return self.status in ("unhealthy", "critical")
```

## Automatic Fallback Mechanism

### Fallback Trigger Conditions
```python
class FallbackTrigger:
    """Conditions that trigger automatic fallback."""
    
    @staticmethod
    def should_trigger_fallback(health: HealthStatus, 
                               consecutive_failures: int,
                               error_rate: float) -> bool:
        """Determine if fallback should be triggered."""
        
        # Immediate fallback for critical issues
        if health.status == "critical":
            return True
        
        # Fallback after consecutive failures
        if consecutive_failures >= 3:
            return True
        
        # Fallback on high error rate
        if error_rate > 0.5:  # 50% failure rate
            return True
        
        # Fallback for unhealthy status
        if health.status == "unhealthy":
            return True
        
        return False
```

### Fallback Orchestrator
```python
class FallbackOrchestrator:
    """Manages fallback between browser backends."""
    
    def __init__(self, config: FallbackConfig):
        self.config = config
        self.current_backend = config.primary_backend
        self.fallback_backend = config.fallback_backend
        self.health_checker = BackendHealthChecker()
        self.failure_count = defaultdict(int)
        self.circuit_breaker = CircuitBreaker()
    
    async def get_healthy_backend(self) -> str:
        """Get a healthy backend, triggering fallback if needed."""
        health = await self.health_checker.check_backend_health(self.current_backend)
        
        if FallbackTrigger.should_trigger_fallback(
            health, 
            self.failure_count[self.current_backend],
            self._get_error_rate(self.current_backend)
        ):
            logger.warning(f"Fallback triggered for {self.current_backend}")
            return await self._execute_fallback()
        
        return self.current_backend
    
    async def _execute_fallback(self) -> str:
        """Execute fallback to secondary backend."""
        # Check if fallback is healthy
        fallback_health = await self.health_checker.check_backend_health(self.fallback_backend)
        
        if fallback_health.can_serve:
            logger.info(f"Falling back to {self.fallback_backend}")
            self.current_backend = self.fallback_backend
            return self.fallback_backend
        
        # If fallback also unhealthy, use Playwright as last resort
        logger.warning("Fallback backend also unhealthy, using Playwright")
        return "playwright"
```

## Circuit Breaker Pattern

### Circuit Breaker Implementation
```python
class CircuitBreaker:
    """Circuit breaker for failing backends."""
    
    def __init__(self, failure_threshold: int = 5, 
                 timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = defaultdict(int)
        self.last_failure_time = defaultdict(float)
        self.state = defaultdict(lambda: "closed")
    
    async def record_failure(self, backend: str):
        """Record a failure for the backend."""
        self.failures[backend] += 1
        self.last_failure_time[backend] = time.time()
        
        if self.failures[backend] >= self.failure_threshold:
            self.state[backend] = "open"
            logger.warning(f"Circuit breaker opened for {backend}")
    
    async def record_success(self, backend: str):
        """Record a success for the backend."""
        self.failures[backend] = 0
        self.state[backend] = "closed"
    
    async def can_attempt(self, backend: str) -> bool:
        """Check if we can attempt using this backend."""
        if self.state[backend] == "closed":
            return True
        
        if self.state[backend] == "open":
            # Check if timeout has passed
            if time.time() - self.last_failure_time[backend] > self.timeout:
                self.state[backend] = "half_open"
                return True
        
        return False
```

## Graceful Degradation

### Feature Degradation Levels
```python
class DegradationLevel(Enum):
    """Levels of graceful degradation."""
    FULL_FEATURED = "full_featured"
    REDUCED_FUNCTIONALITY = "reduced"
    MINIMAL_FUNCTIONALITY = "minimal"
    EMERGENCY_MODE = "emergency"

class DegradationManager:
    """Manages graceful degradation of features."""
    
    def __init__(self, backend: str):
        self.backend = backend
        self.current_level = DegradationLevel.FULL_FEATURED
    
    async def determine_degradation_level(self, health: HealthStatus) -> DegradationLevel:
        """Determine appropriate degradation level."""
        
        if health.status == "healthy":
            return DegradationLevel.FULL_FEATURED
        
        elif health.status == "degraded":
            if not health.linkedin_compatible:
                return DegradationLevel.REDUCED_FUNCTIONALITY
            return DegradationLevel.FULL_FEATURED
        
        elif health.status == "unhealthy":
            return DegradationLevel.MINIMAL_FUNCTIONALITY
        
        else:  # critical
            return DegradationLevel.EMERGENCY_MODE
    
    async def apply_degradation(self, level: DegradationLevel):
        """Apply degradation to current operations."""
        if level == DegradationLevel.REDUCED_FUNCTIONALITY:
            # Disable complex interactions
            self._disable_complex_features()
        
        elif level == DegradationLevel.MINIMAL_FUNCTIONALITY:
            # Only basic scraping
            self._enable_minimal_mode()
        
        elif level == DegradationLevel.EMERGENCY_MODE:
            # Emergency mode - cookie-only operations
            self._enable_emergency_mode()
```

## Monitoring and Alerting

### Metrics Collection
```python
class BackendMetrics:
    """Metrics collection for backend monitoring."""
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.success_count = defaultdict(int)
        self.failure_count = defaultdict(int)
        self.latency_samples = defaultdict(list)
        self.memory_usage = defaultdict(list)
    
    def record_request(self, backend: str, success: bool, latency: float, memory: float):
        """Record a request metric."""
        self.request_count[backend] += 1
        if success:
            self.success_count[backend] += 1
        else:
            self.failure_count[backend] += 1
        
        self.latency_samples[backend].append(latency)
        self.memory_usage[backend].append(memory)
    
    def get_error_rate(self, backend: str) -> float:
        """Calculate error rate for backend."""
        total = self.request_count[backend]
        if total == 0:
            return 0.0
        return self.failure_count[backend] / total
    
    def get_average_latency(self, backend: str) -> float:
        """Calculate average latency for backend."""
        samples = self.latency_samples[backend]
        if not samples:
            return 0.0
        return sum(samples) / len(samples)
```

### Alerting System
```python
class AlertManager:
    """Alerting for backend issues."""
    
    async def check_alerts(self, health: HealthStatus, metrics: BackendMetrics):
        """Check if any alerts should be triggered."""
        
        alerts = []
        
        # Critical health alert
        if health.status == "critical":
            alerts.append(self._create_critical_alert(health))
        
        # High error rate alert
        error_rate = metrics.get_error_rate(health.backend)
        if error_rate > 0.3:  # 30% error rate
            alerts.append(self._create_error_rate_alert(health.backend, error_rate))
        
        # High latency alert
        latency = metrics.get_average_latency(health.backend)
        if latency > 10.0:  # 10 seconds
            alerts.append(self._create_latency_alert(health.backend, latency))
        
        # Memory usage alert
        memory = metrics.get_average_memory(health.backend)
        if memory > 500:  # 500MB
            alerts.append(self._create_memory_alert(health.backend, memory))
        
        for alert in alerts:
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: Alert):
        """Send alert via configured channels."""
        logger.error(f"ALERT: {alert.message}")
        # Add integrations: Slack, email, PagerDuty, etc.
```

## Rollback Procedures

### Manual Rollback
```python
class RollbackManager:
    """Manual rollback procedures."""
    
    async def rollback_to_playwright(self):
        """Immediate rollback to Playwright."""
        logger.warning("Executing manual rollback to Playwright")
        
        # Update configuration
        config = get_config()
        config.browser.backend = "playwright"
        
        # Stop lightweight browser processes
        await self._stop_lightweight_browsers()
        
        # Validate Playwright availability
        if await self._validate_playwright():
            logger.info("Rollback to Playwright successful")
            return True
        else:
            logger.error("Rollback to Playwright failed")
            return False
    
    async def _validate_playwright(self) -> bool:
        """Validate Playwright is functional."""
        try:
            manager = UnifiedBrowserManager("playwright")
            await manager.start()
            await manager.close()
            return True
        except Exception as e:
            logger.error(f"Playwright validation failed: {e}")
            return False
```

### Configuration Rollback
```python
class ConfigRollback:
    """Configuration-based rollback."""
    
    async def rollback_config(self, backup_config: dict):
        """Rollback configuration to previous state."""
        logger.info("Rolling back configuration")
        
        # Restore configuration
        config = get_config()
        config.browser.backend = backup_config["browser"]["backend"]
        config.browser.cdp_url = backup_config["browser"].get("cdp_url")
        
        # Save configuration
        save_config(config)
        
        logger.info("Configuration rollback complete")
```

## Testing Fallback Mechanisms

### Fallback Testing
```python
class FallbackTestSuite:
    """Test suite for fallback mechanisms."""
    
    async def test_health_check_triggers(self):
        """Test health check triggers fallback."""
        # Simulate unhealthy backend
        # Verify fallback triggers
        pass
    
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        # Simulate repeated failures
        # Verify circuit breaker opens
        pass
    
    async def test_graceful_degradation(self):
        """Test graceful degradation levels."""
        # Test each degradation level
        # Verify appropriate functionality
        pass
    
    async def test_manual_rollback(self):
        """Test manual rollback procedures."""
        # Test rollback to Playwright
        # Verify successful rollback
        pass
```

## Documentation and Runbooks

### Operational Runbook
```markdown
# Backend Fallback Runbook

## When Backend Fails

1. Check health status: `GET /health`
2. Review metrics: `GET /metrics`
3. Check logs for error patterns
4. Execute manual rollback if needed

## Manual Rollback Procedure

1. Update configuration: `browser.backend = "playwright"`
2. Restart MCP server
3. Validate functionality
4. Monitor health checks

## Escalation Procedures

- Level 1: Automatic fallback (0-5 min)
- Level 2: Manual intervention (5-15 min)
- Level 3: Critical incident (15+ min)
```

## Success Criteria

### Reliability Requirements
- ✅ Fallback triggers within 5 seconds of backend failure
- ✅ Health checks complete within 2 seconds
- ✅ Circuit breaker prevents cascade failures
- ✅ Manual rollback completes within 30 seconds

### Performance Requirements
- ✅ Fallback adds <100ms latency
- ✅ Health checks consume <1% CPU
- ✅ Monitoring overhead <5% memory
- ✅ No performance degradation in normal operation

### Operational Requirements
- ✅ Clear alerting for all failure modes
- ✅ Comprehensive runbooks available
- ✅ Team trained on fallback procedures
- ✅ Post-incident review process established
