# Phased Migration Plan with Testing Gates

## Migration Overview

### Migration Goals
- Replace heavy Playwright dependency with lightweight browser (Obscura/Lightpanda)
- Maintain 100% functional compatibility
- Achieve 7-16x memory reduction
- Preserve all existing features and tests
- Enable graceful fallback to Playwright

### Migration Timeline
- **Total Duration**: 12-16 weeks
- **Phases**: 6 major phases
- **Testing Gates**: 6 major gates + continuous testing
- **Rollback Capability**: Always available

## Phase 1: Foundation and Infrastructure (Weeks 1-2)

### Objectives
- Set up development environment for lightweight browsers
- Create abstraction layer architecture
- Establish testing infrastructure
- Set up monitoring and metrics

### Tasks

#### Week 1: Environment Setup
- [ ] Install and configure Obscura
- [ ] Install and configure Lightpanda
- [ ] Set up CDP testing environment
- [ ] Create development configuration files
- [ ] Set up process management for CDP servers

#### Week 2: Architecture Foundation
- [ ] Create `UnifiedBrowserManager` interface
- [ ] Implement `CDPBrowserManager` base class
- [ ] Create configuration schema for backend selection
- [ ] Set up health check infrastructure
- [ ] Implement basic metrics collection

### Testing Gate 1: Foundation Validation
**Success Criteria**:
- [ ] Obscura starts and accepts CDP connections
- [ ] Lightpanda starts and accepts CDP connections
- [ ] Health checks complete successfully for both backends
- [ ] Basic CDP navigation works (goto, title, url)
- [ ] Metrics collection functions correctly

**Exit Criteria**: All success criteria met, no blocking issues

**Rollback Plan**: Remove lightweight browser installations, continue with Playwright

---

## Phase 2: Cookie Management Migration (Weeks 3-4)

### Objectives
- Implement unified cookie management
- Ensure cookie import/export compatibility
- Test cookie operations on all backends
- Validate LinkedIn authentication with cookies

### Tasks

#### Week 3: Cookie Abstraction
- [ ] Implement `CookieManager` class
- [ ] Add CDP cookie API methods
- [ ] Preserve existing cookie format
- [ ] Implement domain normalization
- [ ] Add cookie validation logic

#### Week 4: Cookie Testing
- [ ] Test cookie import/export with Playwright
- [ ] Test cookie import/export with Obscura
- [ ] Test cookie import/export with Lightpanda
- [ ] Validate bridge cookie presets
- [ ] Test LinkedIn authentication with cookies

### Testing Gate 2: Cookie Validation
**Success Criteria**:
- [ ] Cookie import/export works on all backends
- [ ] Bridge cookie presets function correctly
- [ ] Domain normalization preserved
- [ ] LinkedIn auth succeeds with imported cookies
- [ ] Cookie validation prevents invalid imports

**Integration Tests**:
```python
async def test_cookie_import_export_obscura():
    """Test cookie import/export with Obscura."""
    manager = UnifiedBrowserManager("obscura")
    await manager.start()
    
    # Export cookies from authenticated session
    cookies = await manager.export_cookies()
    assert len(cookies) > 0
    
    # Import cookies to fresh session
    await manager.import_cookies(cookies)
    assert await manager.is_authenticated()
    
    await manager.close()
```

**Exit Criteria**: All cookie operations work identically across backends

**Rollback Plan**: Use existing Playwright cookie management, disable abstraction layer

---

## Phase 3: Storage State Migration (Weeks 5-6)

### Objectives
- Implement storage state management
- Add feature detection for IndexedDB
- Implement graceful degradation
- Test checkpoint/restart functionality

### Tasks

#### Week 5: Storage State Implementation
- [ ] Implement `StorageStateManager` class
- [ ] Add CDP storage state APIs
- [ ] Implement IndexedDB feature detection
- [ ] Add graceful degradation logic
- [ ] Preserve existing storage state format

#### Week 6: Storage State Testing
- [ ] Test storage state export with Playwright
- [ ] Test storage state export with Obscura
- [ ] Test storage state export with Lightpanda
- [ ] Test IndexedDB fallback
- [ ] Validate checkpoint/restart flow

### Testing Gate 3: Storage State Validation
**Success Criteria**:
- [ ] Storage state export works on Playwright
- [ ] Cookie-only fallback works for lightweight browsers
- [ ] IndexedDB detection functions correctly
- [ ] Checkpoint/restart flow preserved
- [ ] Docker bridge flow functions

**Integration Tests**:
```python
async def test_storage_state_fallback():
    """Test storage state fallback without IndexedDB."""
    manager = UnifiedBrowserManager("obscura")
    await manager.start()
    
    # Export without IndexedDB
    result = await manager.export_storage_state(path, indexed_db=False)
    assert result == True
    
    # Import and validate
    await manager.import_storage_state(path)
    assert await manager.is_authenticated()
    
    await manager.close()
```

**Exit Criteria**: Storage state management works with graceful degradation

**Rollback Plan**: Use existing Playwright storage state, disable new manager

---

## Phase 4: Profile Management Adaptation (Weeks 7-8)

### Objectives
- Adapt profile management for multiple backends
- Implement portable cookie adapter
- Preserve profile lease system
- Test profile creation and cleanup

### Tasks

#### Week 7: Profile Manager Implementation
- [ ] Implement `ProfileManager` class
- [ ] Add backend-specific profile creation
- [ ] Implement portable cookie adapter
- [ ] Preserve profile directory structure
- [ ] Adapt profile lease system

#### Week 8: Profile Management Testing
- [ ] Test profile creation with Playwright
- [ ] Test profile creation with Obscura
- [ ] Test profile creation with Lightpanda
- [ ] Test profile lease system
- [ ] Validate concurrent access prevention

### Testing Gate 4: Profile Management Validation
**Success Criteria**:
- [ ] Profile creation works on all backends
- [ ] Profile lease system intact
- [ ] Concurrent access prevention works
- [ ] Portable cookie adapter functions
- [ ] Profile cleanup succeeds

**Integration Tests**:
```python
async def test_profile_lease_system():
    """Test profile lease system with lightweight browsers."""
    manager1 = UnifiedBrowserManager("obscura")
    manager2 = UnifiedBrowserManager("obscura")
    
    # First manager should acquire lease
    await manager1.start()
    assert manager1.has_lease()
    
    # Second manager should fail to acquire lease
    with pytest.raises(ProfileLeaseError):
        await manager2.start()
    
    await manager1.close()
    await manager2.start()  # Should succeed after lease release
    await manager2.close()
```

**Exit Criteria**: Profile management works across all backends

**Rollback Plan**: Use existing Playwright profile management

---

## Phase 5: Authentication Flow Preservation (Weeks 9-10)

### Objectives
- Ensure session validation works via CDP
- Test authentication flow with all backends
- Validate remember-me resolution
- Test auth barrier detection

### Tasks

#### Week 9: Auth Flow Testing
- [ ] Test `is_logged_in()` via CDP
- [ ] Test `detect_auth_barrier()` via CDP
- [ ] Test `resolve_remember_me_prompt()` via CDP
- [ ] Test manual login flow
- [ ] Validate locale-independent detection

#### Week 10: Auth Flow Integration
- [ ] Test full authentication flow with Obscura
- [ ] Test full authentication flow with Lightpanda
- [ ] Test authentication with cookie import
- [ ] Validate session persistence
- [ ] Test authentication error handling

### Testing Gate 5: Authentication Validation
**Success Criteria**:
- [ ] All auth functions work via CDP
- [ ] Locale-independent detection preserved
- [ ] Remember-me resolution functional
- [ ] Manual login flow works
- [ ] Session persistence maintained

**Integration Tests**:
```python
async def test_auth_flow_obscura():
    """Test complete authentication flow with Obscura."""
    manager = UnifiedBrowserManager("obscura")
    await manager.start()
    
    # Test remember-me resolution
    await manager.page.goto("https://www.linkedin.com/feed/")
    resolved = await resolve_remember_me_prompt(manager.page)
    
    # Test auth detection
    logged_in = await is_logged_in(manager.page)
    assert logged_in == True
    
    await manager.close()
```

**Exit Criteria**: Authentication flow identical to Playwright

**Rollback Plan**: Use existing auth.py with Playwright

---

## Phase 6: Production Rollout (Weeks 11-12)

### Objectives
- Implement feature flags for gradual rollout
- Set up production monitoring
- Create runbooks and procedures
- Execute phased user migration

### Tasks

#### Week 11: Production Preparation
- [ ] Implement feature flags
- [ ] Set up production monitoring
- [ ] Create operational runbooks
- [ ] Train team on fallback procedures
- [ ] Prepare communication plan

#### Week 12: Gradual Rollout
- [ ] Roll out to 10% of users (Obscura)
- [ ] Monitor metrics and errors
- [ ] Roll out to 25% of users
- [ ] Monitor and validate
- [ ] Roll out to 50% of users
- [ ] Continue monitoring

### Testing Gate 6: Production Validation
**Success Criteria**:
- [ ] Error rate < 1% for migrated users
- [ ] Memory usage reduced by 7-16x
- [ ] Performance improved or maintained
- [ ] User feedback positive
- [ ] No critical issues

**Monitoring Metrics**:
```python
# Key metrics to monitor
metrics = {
    "backend_health": health_status,
    "error_rate": error_rate_percentage,
    "memory_usage": memory_mb,
    "request_latency": latency_seconds,
    "auth_success_rate": auth_success_percentage,
    "user_satisfaction": satisfaction_score,
}
```

**Exit Criteria**: Successful production rollout with positive metrics

**Rollback Plan**: Immediate rollback via feature flags if issues detected

---

## Continuous Testing Strategy

### Automated Testing Pipeline
```yaml
# .github/workflows/browser-backend-testing.yml
name: Browser Backend Testing

on: [push, pull_request]

jobs:
  test-all-backends:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        backend: [playwright, obscura, lightpanda]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: uv sync
      - name: Start ${{ matrix.backend }}
        run: ./scripts/start_${{ matrix.backend }}.sh
      - name: Run tests
        run: uv run pytest tests/ --backend=${{ matrix.backend }}
      - name: Collect metrics
        run: ./scripts/collect_metrics.sh ${{ matrix.backend }}
```

### Performance Benchmarking
```python
class PerformanceBenchmark:
    """Performance benchmarking for backends."""
    
    async def benchmark_backend(self, backend: str) -> BenchmarkResults:
        """Run comprehensive performance benchmark."""
        
        # Memory benchmark
        memory_start = self._get_memory_usage()
        manager = UnifiedBrowserManager(backend)
        await manager.start()
        memory_after_start = self._get_memory_usage()
        
        # Page load benchmark
        start_time = time.time()
        await manager.page.goto("https://www.linkedin.com/feed/")
        load_time = time.time() - start_time
        
        # Scraping benchmark
        start_time = time.time()
        text = await manager.page.evaluate("document.body.innerText")
        scrape_time = time.time() - start_time
        
        await manager.close()
        memory_after_close = self._get_memory_usage()
        
        return BenchmarkResults(
            backend=backend,
            memory_used=memory_after_start - memory_start,
            load_time=load_time,
            scrape_time=scrape_time,
            memory_leaked=memory_after_close - memory_start,
        )
```

## Risk Mitigation

### Phase-Specific Risks

#### Phase 1 Risks
- **Risk**: Lightweight browser installation fails
- **Mitigation**: Pre-package binaries, provide fallback installation scripts
- **Contingency**: Skip problematic backend, continue with others

#### Phase 2 Risks
- **Risk**: Cookie API incompatibility
- **Mitigation**: Comprehensive API testing, graceful degradation
- **Contingency**: Use Playwright cookie management for affected backend

#### Phase 3 Risks
- **Risk**: IndexedDB support missing
- **Mitigation**: Feature detection, cookie-only fallback
- **Contingency**: Disable IndexedDB-dependent features

#### Phase 4 Risks
- **Risk**: Profile format incompatibility
- **Mitigation**: Portable cookie adapter, profile format abstraction
- **Contingency**: Use Playwright profile format as universal adapter

#### Phase 5 Risks
- **Risk**: Auth detection fails via CDP
- **Mitigation**: Extensive auth flow testing, preserve existing logic
- **Contingency**: Use Playwright for authentication only

#### Phase 6 Risks
- **Risk**: Production issues detected
- **Mitigation**: Gradual rollout, feature flags, monitoring
- **Contingency**: Immediate rollback via feature flags

## Communication Plan

### Stakeholder Communication
- **Weekly progress updates** to project stakeholders
- **Phase completion notifications** with success criteria
- **Risk alerts** for any blocking issues
- **Rollback notifications** if executed

### User Communication
- **Pre-migration notification** of upcoming improvements
- **Migration notification** when user is migrated
- **Performance improvement summary** post-migration
- **Support contact** for any issues

## Success Metrics

### Technical Metrics
- ✅ All existing tests pass with new backends
- ✅ Memory usage reduced by 7-16x
- ✅ Performance maintained or improved
- ✅ Error rate < 1% in production
- ✅ Fallback mechanisms functional

### Business Metrics
- ✅ User satisfaction maintained or improved
- ✅ Support ticket volume unchanged or reduced
- ✅ System reliability maintained
- ✅ Cost reduction achieved (resource usage)

### Operational Metrics
- ✅ Deployment success rate 100%
- ✅ Rollback time < 5 minutes
- ✅ Monitoring coverage 100%
- ✅ Team training complete

## Timeline Summary

| Phase | Duration | Key Deliverables | Testing Gate |
|-------|----------|------------------|--------------|
| 1: Foundation | 2 weeks | Environment setup, architecture | Gate 1: Foundation Validation |
| 2: Cookie Management | 2 weeks | Cookie abstraction | Gate 2: Cookie Validation |
| 3: Storage State | 2 weeks | Storage state manager | Gate 3: Storage State Validation |
| 4: Profile Management | 2 weeks | Profile manager | Gate 4: Profile Management Validation |
| 5: Authentication | 2 weeks | Auth flow preservation | Gate 5: Authentication Validation |
| 6: Production Rollout | 2 weeks | Production deployment | Gate 6: Production Validation |

**Total Duration**: 12 weeks with optional 4-week buffer for testing and refinement

## Resource Requirements

### Development Resources
- 2 senior developers (full-time)
- 1 QA engineer (part-time, phases 2-6)
- 1 DevOps engineer (part-time, phases 1, 6)

### Infrastructure Resources
- Development environment with all browser backends
- Staging environment for integration testing
- Production environment with gradual rollout capability
- Monitoring and alerting infrastructure

### Testing Resources
- LinkedIn test accounts (3-5 accounts)
- Testing environments for each backend
- Performance benchmarking tools
- Load testing infrastructure

## Conclusion

This phased migration plan provides a structured approach to replacing Playwright with lightweight browsers while maintaining functionality and minimizing risk. Each phase has clear objectives, testing gates, and rollback procedures to ensure successful migration with minimal disruption to users.
