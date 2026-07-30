# Session Management Migration Strategy

## Current Session Management Analysis

### Existing Components
1. **Persistent Browser Context** (core/browser.py)
   - Cookie storage and retrieval
   - localStorage persistence
   - Session state retention
   - Profile directory management

2. **Cookie Management** (core/browser.py)
   - Cookie import/export in JSON format
   - Domain normalization (.www.linkedin.com → .linkedin.com)
   - Bridge cookie presets (bridge_core, auth_minimal)
   - Cookie validation

3. **Storage State Checkpointing** (drivers/browser.py)
   - IndexedDB support for Docker scenarios
   - Storage state export/import
   - Derived runtime profiles
   - Checkpoint-restart validation

4. **Profile Lease System** (drivers/browser.py)
   - Concurrent access prevention
   - Profile directory locking
   - Lease reference counting
   - Clean shutdown verification

## Migration Challenges

### 1. Cookie API Compatibility
**Challenge**: Different browsers have different cookie APIs
- Playwright: `context.cookies()` / `context.add_cookies()`
- CDP: `Network.setCookies` / `Network.getCookies`
- Format differences in cookie attributes

**Solution**: Create cookie API abstraction layer
```python
class CookieManager:
    """Abstract cookie management across browser backends."""
    
    async def get_cookies(self) -> list[dict]:
        """Get cookies with backend-specific API."""
        if self.backend == "playwright":
            return await self._context.cookies()
        else:  # CDP
            return await self._cdp_get_cookies()
    
    async def set_cookies(self, cookies: list[dict]) -> None:
        """Set cookies with backend-specific API."""
        if self.backend == "playwright":
            await self._context.add_cookies(cookies)
        else:  # CDP
            await self._cdp_set_cookies(cookies)
```

### 2. Storage State Compatibility
**Challenge**: IndexedDB support varies across browsers
- Playwright: Full IndexedDB support
- Obscura: Unknown IndexedDB support
- Lightpanda: Limited Web API support (CORS missing)

**Solution**: Graceful degradation strategy
```python
class StorageStateManager:
    """Storage state management with feature detection."""
    
    async def export_storage_state(self, path: Path, indexed_db: bool = True) -> bool:
        """Export storage state with feature detection."""
        if not indexed_db or not self._supports_indexed_db():
            return await self._export_without_indexed_db(path)
        return await self._export_with_indexed_db(path)
    
    def _supports_indexed_db(self) -> bool:
        """Check IndexedDB support for current backend."""
        return self.backend == "playwright"  # Only Playwright confirmed
```

### 3. Profile Directory Compatibility
**Challenge**: Different profile formats
- Playwright: Chromium profile format
- Obscura: Custom profile format
- Lightpanda: Custom profile format

**Solution**: Portable cookie format as universal adapter
```python
class ProfileManager:
    """Profile management with portable format."""
    
    async def create_profile(self, source_state: SourceState) -> Path:
        """Create profile from portable state."""
        if self.backend == "playwright":
            return await self._create_playwright_profile(source_state)
        else:
            # For lightweight browsers, use cookie import instead
            return await self._create_cookie_based_profile(source_state)
```

### 4. Session Validation Compatibility
**Challenge**: Auth barrier detection varies
- Playwright: Full DOM access
- CDP: Same DOM access via CDP
- Feature parity expected

**Solution**: Preserve existing validation logic
```python
# Existing auth.py functions work via CDP
# No changes required for:
# - is_logged_in()
# - detect_auth_barrier()
# - resolve_remember_me_prompt()
```

## Migration Strategy

### Phase 1: Cookie Abstraction (Week 1)
**Goal**: Create unified cookie management

**Tasks**:
1. Implement `CookieManager` class
2. Add CDP cookie API methods
3. Preserve existing cookie format
4. Test cookie import/export

**Validation**:
- Cookie import/export works on all backends
- Bridge cookie presets function correctly
- Domain normalization preserved

### Phase 2: Storage State Migration (Week 2)
**Goal**: Migrate storage state handling

**Tasks**:
1. Implement `StorageStateManager` class
2. Add feature detection for IndexedDB
3. Implement graceful degradation
4. Test checkpoint/restart functionality

**Validation**:
- Storage state export works on Playwright
- Cookie-only fallback works for lightweight browsers
- Docker bridge flow functions

### Phase 3: Profile Directory Adaptation (Week 3)
**Goal**: Adapt profile management

**Tasks**:
1. Implement `ProfileManager` class
2. Add backend-specific profile creation
3. Preserve portable cookie format
4. Test profile lease system

**Validation**:
- Profile creation works on all backends
- Profile lease system intact
- Concurrent access prevention works

### Phase 4: Session Validation Preservation (Week 4)
**Goal**: Ensure session validation works

**Tasks**:
1. Test existing auth functions via CDP
2. Verify remember-me resolution
3. Test auth barrier detection
4. Validate login status checks

**Validation**:
- All auth functions work via CDP
- Locale-independent detection preserved
- Remember-me resolution functional

## Compatibility Matrix

| Feature | Playwright | Obscura (CDP) | Lightpanda (CDP) | Migration Strategy |
|---------|-----------|---------------|------------------|-------------------|
| Cookie Import/Export | ✅ Native | ✅ CDP API | ✅ CDP API | Abstraction layer |
| localStorage | ✅ Native | ✅ CDP API | ✅ CDP API | CDP integration |
| IndexedDB | ✅ Native | ❓ Unknown | ❌ Incomplete | Graceful degradation |
| Session State | ✅ Native | ✅ CDP API | ✅ CDP API | CDP integration |
| Profile Format | ✅ Chromium | ❓ Custom | ❓ Custom | Cookie-based adapter |
| Auth Detection | ✅ Full DOM | ✅ CDP DOM | ✅ CDP DOM | No changes needed |

## Rollback Strategy

### Feature Flags
```python
# config/schema.py
class MigrationConfig(BaseModel):
    use_unified_session_manager: bool = False
    force_playwright_cookies: bool = False
    disable_indexed_db_fallback: bool = False
```

### Fallback Triggers
- Cookie manager failure → Playwright native
- Storage state failure → Cookie-only mode
- Profile creation failure → Portable cookie import
- Auth detection failure → Use existing auth.py

### Validation Gates
Each phase requires:
- Unit tests for new abstraction layer
- Integration tests with real LinkedIn
- Performance benchmarks
- Memory usage validation

## Testing Strategy

### Unit Testing
```python
# tests/test_cookie_manager.py
async def test_cookie_manager_playwright():
    manager = CookieManager(backend="playwright")
    # Test cookie operations

async def test_cookie_manager_cdp():
    manager = CookieManager(backend="obscura")
    # Test CDP cookie operations
```

### Integration Testing
```python
# tests/test_session_migration.py
async def test_session_obscura_linkedin():
    # Test full LinkedIn session with Obscura

async def test_session_lightpanda_linkedin():
    # Test full LinkedIn session with Lightpanda
```

### Performance Testing
- Memory usage comparison
- Session creation time
- Cookie import/export speed
- Storage state export time

## Risk Mitigation

### Technical Risks
1. **CDP API Limitations**: Mitigate with comprehensive testing
2. **IndexedDB Support**: Plan for graceful degradation
3. **Profile Format Differences**: Use portable cookie adapter
4. **Session Validation**: Preserve existing proven logic

### Operational Risks
1. **Migration Complexity**: Phase-by-phase approach
2. **User Impact**: Feature flags for gradual rollout
3. **Performance Regression**: Benchmark at each phase
4. **Data Loss**: Preserve existing profiles during migration

## Success Criteria

### Functional Requirements
- ✅ All session management features work on all backends
- ✅ Cookie import/export maintains compatibility
- ✅ Auth flow preserved across backends
- ✅ Profile lease system intact

### Performance Requirements
- ✅ Memory usage reduced by 7-16x
- ✅ Session creation time ≤ current
- ✅ No performance regression in scraping

### Reliability Requirements
- ✅ Zero data loss during migration
- ✅ Graceful fallback on failures
- ✅ Existing tests continue to pass
- ✅ New tests for migration components

## Timeline Estimate
- **Phase 1**: 1 week (Cookie abstraction)
- **Phase 2**: 1 week (Storage state migration)
- **Phase 3**: 1 week (Profile directory adaptation)
- **Phase 4**: 1 week (Session validation)
- **Testing & Validation**: 2 weeks
- **Total**: 6 weeks

## Resource Requirements
- 1 senior developer (full-time)
- Access to LinkedIn test accounts
- Testing environment with multiple browser backends
- Performance monitoring tools
- Comprehensive test coverage
