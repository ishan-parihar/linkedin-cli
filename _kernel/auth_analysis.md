# Authentication and Session Management Analysis

## Current Authentication Flow

### 1. Source Profile Creation
- **Login Process**: Manual login via `--login` flag using headless browser
- **Profile Storage**: Persistent browser context at `~/.linkedin-mcp/profile/`
- **Cookie Export**: Portable cookies saved to `cookies.json` 
- **State Metadata**: Source state stored with user agent and timestamps

### 2. Session Validation
- **Feed Auth Check**: Validates against `/feed/` endpoint
- **Remember-me Resolution**: Handles LinkedIn's saved-account chooser
- **Auth Barrier Detection**: URL pattern and text-based detection
- **Login Status**: Three-tier strategy (URL, selectors, content)

### 3. Cookie Management
- **Bridge Cookie Presets**: 
  - `bridge_core`: Full set (li_at, li_rm, JSESSIONID, bcookie, etc.)
  - `auth_minimal`: Minimal set (li_at, JSESSIONID, bcookie, bscookie, lidc)
- **Cookie Import/Export**: For portable authentication across runtimes
- **Domain Normalization**: Handles `.www.linkedin.com` vs `.linkedin.com`

### 4. Runtime Session Management
- **Profile Lease System**: Prevents concurrent access corruption
- **Storage State Checkpointing**: IndexedDB support for Docker scenarios
- **Derived Runtime Profiles**: Created from source for foreign runtimes
- **Session Persistence**: Automatic cleanup and renewal

### 5. Security Features
- **Private File Mode**: 0o600 permissions for sensitive files
- **Directory Hardening**: Security hardening for profile directories
- **Proxy Support**: HTTP proxy configuration with credential handling
- **Shutdown Confirmation**: Verified browser cleanup to prevent profile corruption

## Critical Dependencies on Browser Features

### Persistent Context
- Cookie storage across sessions
- localStorage persistence
- Session state retention
- IndexedDB support

### JavaScript Execution
- Auth barrier detection
- Remember-me prompt resolution
- Login status validation
- Dynamic content hydration detection

### Advanced Browser Features
- User agent spoofing
- Viewport configuration
- Proxy configuration
- Storage state export/import

## Migration Challenges

### Session Portability
- Cookie-only approaches may lose localStorage/IndexedDB data
- Storage state checkpointing requires browser-specific APIs
- Profile lease system needs browser lifecycle management

### Anti-Bot Protection
- LinkedIn may detect headless browsers
- User agent consistency required
- TLS fingerprinting concerns
- Behavior pattern detection

### Authentication Flow
- Manual login process requires interactive browser
- Cookie import/export validation needs JavaScript execution
- Session validation depends on DOM access
