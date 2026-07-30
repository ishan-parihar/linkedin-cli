# Lightweight Browser Research: Obscura vs Lightpanda

## Obscura (Rust-based)

### Key Features
- **Language**: Rust
- **JavaScript Engine**: V8
- **Protocol**: Chrome DevTools Protocol (CDP)
- **Compatibility**: Drop-in replacement for Puppeteer and Playwright
- **Anti-Detection**: Built-in stealth features

### Performance Metrics
| Metric | Obscura | Headless Chrome | Improvement |
|--------|---------|-----------------|-------------|
| Memory | 30 MB | 200+ MB | ~7x less |
| Binary Size | 70 MB | 300+ MB | ~4x smaller |
| Page Load | 85 ms | ~500 ms | ~6x faster |
| Startup | Instant | ~2s | Instant |

### Integration Advantages
- **Playwright Compatibility**: Direct Playwright support via CDP
- **Puppeteer Compatibility**: Full Puppeteer API support
- **API Compatibility**: Can use existing Playwright code with minimal changes
- **Maturity**: More mature project with 19.8k GitHub stars

### LinkedIn-Specific Advantages
- Built-in anti-detection features
- Lightweight for Docker deployments
- Fast page loads for efficient scraping
- V8 JavaScript engine for complex LinkedIn interactions

## Lightpanda (Zig-based)

### Key Features
- **Language**: Zig (not a Chromium fork)
- **JavaScript Engine**: V8
- **Protocol**: Chrome DevTools Protocol (CDP)
- **Native MCP**: Built-in MCP server support
- **Agent Mode**: LLM-driven automation built-in

### Performance Metrics
| Metric | Lightpanda | Headless Chrome | Improvement |
|--------|------------|-----------------|-------------|
| Memory (100 pages) | 123MB | 2GB | ~16x less |
| Execution Time (100 pages) | 5s | 46s | ~9x faster |

### Integration Advantages
- **Native MCP Server**: Built-in MCP support (major advantage for this project)
- **CDP Support**: Compatible with Puppeteer via CDP
- **Agent Mode**: Built-in LLM automation capabilities
- **Modern Architecture**: Built from scratch for automation

### LinkedIn-Specific Advantages
- Extreme memory efficiency for large-scale scraping
- Native MCP integration could simplify architecture
- Fast execution for high-throughput operations
- Built-in proxy support

### Limitations
- **Beta Status**: Work in progress, stability concerns
- **Missing CORS**: CORS support not yet implemented (#2015)
- **Less Mature**: Newer project with potential edge cases

## Comparison Summary

### For LinkedIn MCP Server Integration

**Obscura Advantages:**
- Playwright-compatible (minimal code changes)
- More mature and stable
- Built-in anti-detection (crucial for LinkedIn)
- Proven track record with web scraping

**Lightpanda Advantages:**
- Native MCP server (architectural alignment)
- Extreme performance gains
- Built-in agent capabilities
- Smaller memory footprint

### Integration Complexity

**Obscura:**
- Low complexity - mostly configuration change
- Can likely use existing Playwright code
- Minimal refactoring required

**Lightpanda:**
- Medium complexity - may need CDP adaptation
- Native MCP could simplify some architecture
- May require more testing due to beta status

## Recommendation Priority

1. **Test Obscura first** - Higher maturity, Playwright compatibility, anti-detection
2. **Test Lightpanda second** - Native MCP is compelling, but beta status is concerning
3. **Consider hybrid approach** - Use Obscura for stability, evaluate Lightpanda for MCP-native future

Both solutions address the weight issue effectively, with 7-16x memory improvements and significant performance gains over Playwright/Chrome.
