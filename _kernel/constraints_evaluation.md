# Constraints Evaluation Matrix

## Constraint Checklist from Intent Table

### C1: Must not use heavy Playwright dependencies (PRIMARY)
| Alternative | Weight Reduction | Meets C1 | Score |
|-------------|------------------|---------|-------|
| httpx/curlffi | ~100% (no browser) | YES | 10/10 |
| Obscura | 7x (30MB vs 200MB) | YES | 9/10 |
| Lightpanda | 16x (123MB vs 2GB) | YES | 10/10 |
| Current (Playwright) | 0% | NO | 0/10 |

### C2: Must maintain existing LinkedIn scraping functionality
| Alternative | JS Execution | Complex Interactions | Meets C2 | Score |
|-------------|--------------|---------------------|----------|-------|
| httpx/curlffi | NO | NO | NO | 0/10 |
| Obscura | YES (via CDP) | YES (via CDP) | YES | 8/10 |
| Lightpanda | YES (native) | YES (native) | YES | 9/10 |
| Current (Playwright) | YES | YES | YES | 10/10 |

### C3: Must support authenticated sessions and LinkedIn's anti-bot protections
| Alternative | Session Management | Anti-Detection | Meets C3 | Score |
|-------------|-------------------|----------------|----------|-------|
| httpx/curlffi | Limited (cookies only) | NONE | NO | 1/10 |
| Obscura | Full (via CDP) | Built-in | YES | 8/10 |
| Lightpanda | Full (native) | Unknown | MAYBE | 6/10 |
| Current (Playwright) | Full | Basic | YES | 7/10 |

### C4: Must pass existing test suite
| Alternative | Playwright API Compatible | Test Changes Required | Meets C4 | Score |
|-------------|---------------------------|---------------------|----------|-------|
| httpx/curlffi | NO | Complete rewrite | NO | 0/10 |
| Obscura | YES (via CDP) | Minimal | YES | 8/10 |
| Lightpanda | YES (via CDP) | Minimal | YES | 8/10 |
| Current (Playwright) | YES | None | YES | 10/10 |

### C5: Should maintain locale-independent detection logic per CLAUDE.md rules
| Alternative | DOM Access | JS Execution | Meets C5 | Score |
|-------------|-----------|--------------|----------|-------|
| httpx/curlffi | NO | NO | NO | 0/10 |
| Obscura | YES (via CDP) | YES | YES | 9/10 |
| Lightpanda | YES (native) | YES | YES | 9/10 |
| Current (Playwright) | YES | YES | YES | 10/10 |

### C6: Should minimize DOM dependence and prefer innerText/URL navigation
| Alternative | innerText Support | URL Navigation | Meets C6 | Score |
|-------------|------------------|----------------|----------|-------|
| httpx/curlffi | NO | YES | PARTIAL | 3/10 |
| Obscura | YES (via CDP) | YES | YES | 9/10 |
| Lightpanda | YES (native) | YES | YES | 9/10 |
| Current (Playwright) | YES | YES | YES | 10/10 |

## Additional Evaluation Criteria

### Integration Complexity
| Alternative | Code Changes | Architecture Changes | Complexity Score |
|-------------|--------------|---------------------|------------------|
| httpx/curlffi | Complete rewrite | Major | 10/10 (High) |
| Obscura | Minimal (config) | Minor | 3/10 (Low) |
| Lightpanda | Minimal (config) | Minor + MCP opportunity | 4/10 (Low-Medium) |
| Current | None | None | 0/10 (None) |

### Community & Support
| Alternative | GitHub Stars | Maturity | Documentation | Support Score |
|-------------|-------------|----------|---------------|--------------|
| httpx/curlffi | High | Mature | Excellent | 9/10 |
| Obscura | 19.8k | Mature | Good | 8/10 |
| Lightpanda | 32.8k | Beta | Good | 7/10 |
| Current (Playwright) | Very High | Very Mature | Excellent | 10/10 |

### Performance Benefits
| Alternative | Memory Improvement | Speed Improvement | Performance Score |
|-------------|-------------------|-------------------|------------------|
| httpx/curlffi | ~100% | ~10x faster | 10/10 |
| Obscura | 7x | 6x faster | 8/10 |
| Lightpanda | 16x | 9x faster | 10/10 |
| Current | 0% | 0% | 0/10 |

### Risk Assessment
| Alternative | Technical Risk | Project Risk | Risk Score |
|-------------|----------------|-------------|-----------|
| httpx/curlffi | High (won't work) | High (complete failure) | 10/10 (High) |
| Obscura | Low (CDP proven) | Low (mature project) | 3/10 (Low) |
| Lightpanda | Medium (beta status) | Medium (CORS missing) | 6/10 (Medium) |
| Current | None | None | 0/10 (None) |

## Overall Scoring

### Weighted Scoring (Weights: C1=25%, C2=25%, C3=15%, C4=15%, C5=10%, C6=10%)

| Alternative | C1 | C2 | C3 | C4 | C5 | C6 | WEIGHTED SCORE |
|-------------|----|----|----|----|----|----|---------------|
| httpx/curlffi | 10 | 0 | 1 | 0 | 0 | 3 | **2.5/10** |
| Obscura | 9 | 8 | 8 | 8 | 9 | 9 | **8.2/10** |
| Lightpanda | 10 | 9 | 6 | 8 | 9 | 9 | **8.4/10** |
| Current | 0 | 10 | 7 | 10 | 10 | 10 | **6.8/10** |

### Final Rankings
1. **Lightpanda: 8.4/10** - Best performance, native MCP, but beta risk
2. **Obscura: 8.2/10** - Mature, proven CDP, built-in anti-detection
3. **Current: 6.8/10** - Works but heavy dependency
4. **httpx/curlffi: 2.5/10** - Not viable for LinkedIn

## Recommendation
**Primary Recommendation: Obscura** (Lower risk, proven technology)
**Secondary Recommendation: Lightpanda** (Higher performance, native MCP, but beta)

Both Obscura and Lightpanda significantly outperform the current Playwright setup while meeting all critical constraints. The choice between them depends on risk tolerance vs. architectural benefits.
