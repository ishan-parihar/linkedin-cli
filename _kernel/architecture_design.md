# Hybrid Architecture Design for Lightweight Browser Integration

## Architecture Overview

### Design Principles
1. **CDP Abstraction**: Use Chrome DevTools Protocol as the integration layer
2. **Configuration-Driven**: Runtime browser selection via configuration
3. **Minimal Code Changes**: Preserve existing Playwright-compatible API
4. **Fallback Capability**: Graceful degradation between browser engines
5. **Session Compatibility**: Maintain existing session management

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LinkedIn MCP Server                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Browser Abstraction Layer                     │ │
│  │  (Unified interface for all browser backends)          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                          │                                   │
│          ┌───────────────┼───────────────┐                   │
│          ▼               ▼               ▼                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Playwright │ │   Obscura    │ │  Lightpanda  │        │
│  │   (Current)  │ │   (CDP)      │ │   (CDP/MCP)   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│         │               │               │                   │
│         └───────────────┴───────────────┘                   │
│                         ▼                                   │
│              ┌──────────────────┐                          │
│              │  CDP Protocol    │                          │
│              │  (Common Layer)  │                          │
│              └──────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Strategy

### Phase 1: CDP Abstraction Layer
Create a unified browser manager that supports multiple backends:

```python
class UnifiedBrowserManager:
    """Abstract browser manager supporting multiple backends."""
    
    def __init__(self, backend: str = "playwright"):
        self.backend = backend
        self._manager = self._create_backend_manager()
    
    def _create_backend_manager(self):
        """Factory method for backend-specific managers."""
        if self.backend == "playwright":
            return PlaywrightBrowserManager()
        elif self.backend == "obscura":
            return CDPBrowserManager(cdp_url="http://localhost:9222")
        elif self.backend == "lightpanda":
            return CDPBrowserManager(cdp_url="http://localhost:9223")
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
```

### Phase 2: CDP Browser Manager
Implement CDP-based browser manager for Obscura/Lightpanda:

```python
class CDPBrowserManager:
    """CDP-based browser manager for lightweight browsers."""
    
    def __init__(self, cdp_url: str):
        self.cdp_url = cdp_url
        self._playwright = None
        self._context = None
        self._page = None
    
    async def start(self):
        """Connect to CDP endpoint instead of launching browser."""
        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.connect(self.cdp_url)
        self._page = await self._context.new_page()
```

### Phase 3: Configuration System
Add browser backend configuration:

```python
# config/schema.py
class BrowserConfig(BaseModel):
    backend: Literal["playwright", "obscura", "lightpanda"] = "playwright"
    cdp_url: str | None = None
    obscura_path: str | None = None
    lightpanda_path: str | None = None
    auto_start_cdp: bool = True
```

### Phase 4: Process Management
Add CDP server lifecycle management:

```python
class CDPServerManager:
    """Manages external CDP server processes."""
    
    def __init__(self, backend: str, config: BrowserConfig):
        self.backend = backend
        self.config = config
        self._process = None
    
    async def start(self):
        """Start the appropriate CDP server."""
        if self.backend == "obscura":
            self._process = await self._start_obscura()
        elif self.backend == "lightpanda":
            self._process = await self._start_lightpanda()
    
    async def _start_obscura(self):
        """Start Obscura in serve mode."""
        cmd = [self.config.obscura_path, "serve", "--stealth", "--port", "9222"]
        return await asyncio.create_subprocess_exec(*cmd)
```

## Session Management Migration

### Cookie Handling
- Preserve existing cookie import/export logic
- Adapt CDP cookie APIs for lightweight browsers
- Maintain portable cookie format compatibility

### Storage State
- Use CDP storage state APIs for lightweight browsers
- Maintain IndexedDB support where available
- Preserve checkpoint/restart functionality

### Profile Management
- Keep existing profile directory structure
- Adapt for lightweight browser profile formats
- Maintain profile lease system compatibility

## Fallback Strategy

### Automatic Fallback Chain
```
Primary Backend → Secondary Backend → Current Playwright
     (Obscura)      (Lightpanda)        (Fallback)
```

### Health Check System
```python
async def check_backend_health(backend: str) -> bool:
    """Verify backend availability and functionality."""
    try:
        # Quick smoke test
        manager = UnifiedBrowserManager(backend)
        await manager.start()
        await manager.close()
        return True
    except Exception:
        return False
```

### Graceful Degradation
- Configuration-based backend selection
- Runtime health checks
- Automatic fallback on failure
- Logging for troubleshooting

## Integration Points

### Minimal Code Changes Required
1. **BrowserManager**: Replace with UnifiedBrowserManager
2. **Configuration**: Add backend selection
3. **Process Management**: Add CDP server lifecycle
4. **Tests**: Update to test multiple backends

### Preserved Components
- All scraping logic (extractor.py)
- Authentication flow (auth.py)
- Session management (session_state.py)
- Tool interfaces (tools/*.py)
- MCP server logic (server.py)

## Performance Optimization

### Resource Management
- Lazy CDP server startup
- Connection pooling for CDP
- Process lifecycle optimization
- Memory monitoring and limits

### Caching Strategy
- Reuse CDP connections across tool calls
- Cache browser instances where possible
- Optimize session checkpointing
- Profile directory optimization

## Migration Path

### Stage 1: Dual-Mode Operation
- Run both Playwright and lightweight browser in parallel
- A/B test functionality
- Performance comparison
- Bug identification

### Stage 2: Feature Parity Validation
- Test all scraping sections
- Validate authentication flow
- Verify session management
- Test complex interactions

### Stage 3: Production Rollout
- Configuration-based rollout
- Gradual user migration
- Monitoring and alerting
- Quick rollback capability

## Architecture Benefits

### Immediate Benefits
- 7-16x memory reduction
- 6-9x performance improvement
- Smaller deployment footprint
- Reduced resource costs

### Long-term Benefits
- Native MCP integration (Lightpanda)
- Better anti-detection (Obscura)
- Architecture flexibility
- Future browser engine options

### Risk Mitigation
- Proven CDP integration layer
- Fallback to current implementation
- Configuration-based control
- Gradual migration path
