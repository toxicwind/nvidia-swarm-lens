---
name: fast-browser-use
description: >
  Accelerate web research with fast browser automation, DOM extraction, 
  screenshots, session management, and data collection from dynamic websites 
  and infinite-scroll pages. High-performance browser automation for heavy 
  scraping, multi-tab management, and precise DOM extraction.
allowed-tools: Read, Browser
---

# Fast Browser Use

High-performance browser automation skill for AI agents.

## When to use

- Web research requiring fast DOM extraction
- Screenshots and visual verification
- Session management across multiple pages
- Data collection from dynamic/infinite-scroll pages
- Multi-tab orchestration
- Persistent state (cookies/localStorage) reuse

## Core workflow

1. **Open** — Navigate to target URL
2. **Snapshot** — Capture DOM state / accessibility tree
3. **Interact** — Click, fill, scroll based on refs
4. **Extract** — Pull structured data from page
5. **Persist** — Save session state for reuse

## Commands

| Command | Description |
|---------|-------------|
| `browser open <url>` | Navigate to URL |
| `browser snapshot` | Capture interactive elements |
| `browser click <ref>` | Click element by ref |
| `browser fill <ref> <text>` | Type into field |
| `browser scroll` | Scroll page / infinite scroll |
| `browser screenshot` | Capture page image |
| `browser extract <selector>` | Extract data by selector |
| `browser session save <name>` | Save session state |
| `browser session load <name>` | Restore session state |

## Multi-tab management

```
browser tab new <url>     # Open new tab
browser tab list          # List all tabs
browser tab switch <id>   # Switch to tab
browser tab close <id>    # Close tab
```

## Configuration

- `HEADLESS=true/false` — Run headless or visible
- `STEALTH=true/false` — Enable anti-detection
- `PROXY=<url>` — Route through proxy
- `TIMEOUT=<ms>` — Default timeout

## Integration with huh project

This skill is registered under skill://fast-browser-use and integrates
with the huh project's Mintlify MCP and swarm orchestration.
