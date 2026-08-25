---
name: fast-browser-use
description: >
  Research-grade, Cloudflare-aware browser automation integrating 2026 arXiv
  findings on multi-layer fingerprinting, JA4 TLS detection, and LLM-agent
  attribution. Uses nodriver (CDP-native), Patchright, curl_cffi, and
  Camoufox with shape-coherent profile management.
allowed-tools: Read, Browser
---

# Fast Browser Use — Research-Grade Cloudflare Bypass (August 2026)

Built from 2026 arXiv papers, production benchmarks, and cross-layer detection research. Not baseline — this is the state-of-the-art evasion stack.

## Core Insight: Shape Coherence Beats Everything

Anti-bot systems in 2026 use **multi-layer correlation**, not single-signal validation. cite🛠web_search:15#0:~:text=Detection works more like correlation...evaluated together across requests and over time Your IP, TLS fingerprint, HTTP/2 frame ordering, browser properties, and behavior must all tell the same story. A residential proxy with a Linux TLS fingerprint and macOS navigator.platform is an instant flag. cite🛠web_search:15#0:~:text=A Linux server behind a residential proxy manufactures a fresh contradiction

## 2026 Detection Landscape (arXiv-Sourced)

### Layer 1: TLS / JA4 Fingerprinting

A February 2026 arXiv paper demonstrated that CatBoost classifiers using JA4 features achieve **98.63% accuracy** isolating bots from legitimate traffic — from handshake data alone, before any HTTP request is processed. cite🛠web_search:16#1:~:text=The CatBoost model performed better...accurate 0.9863 of the time on the test set

**Key JA4 signals:**
- `ja4_b` (cipher suite structure) — most discriminative feature
- `ext_count` (extension richness)
- `alpn_code` (protocol negotiation)
- Post-quantum key exchange presence/absence (new 2026 vector)

**What this means:** Standard Python `requests` or Go `net/http` produce JA4 fingerprints that exist nowhere in the world except scrapers. cite🛠web_search:16#9:~:text=A Python requests script claiming to be Chrome produces a fingerprint that doesn't exist anywhere in the world except in scrapers

### Layer 2: HTTP/2 Frame Sequencing

HTTP/2 `SETTINGS` frame ordering and `WINDOW_UPDATE` signals fingerprint the client library. cite🛠web_search:16#9:~:text=HTTP/2 SETTINGS frame ordering...pushes the false-positive rate well below what most scrapers can tolerate Skyvern has a uniquely identifiable stream-5 priority weight of 110. cite🛠web_search:16#2:~:text=Skyvern has a uniquely identifiable TLS/H2 fingerprint...distinct stream-5 priority weight of 110

### Layer 3: Browser Fingerprinting + Behavioral Telemetry

June 2026 arXiv research found that LLM web agents expose distinctive characteristics across all layers. cite🛠web_search:15#0:~:text=We deployed nine honeypot servers...collect three fingerprinting layers Key findings:
- BrowserUse-Stealth mode **increases** detectability by using low-reputation datacenter IPs instead of residential proxies cite🛠web_search:15#0:~:text=BrowserUse-Stealth mode avoids their residential proxy infrastructure...increases bot detection
- Stealth modes can increase detectability by introducing fingerprint inconsistencies cite🛠web_search:15#0:~:text=stealth modes and equivalent features can even increase detectability by introducing fingerprint inconsistencies
- Canvas/WebGL mismatches, font leaks, and WebRTC leaks are primary detection vectors cite🛠web_search:16#8:~:text=Canvas and WebGL Mismatches...triggers immediate verification flags

### Layer 4: Behavioral Correlation

At scale, identical execution paths (page order, delays, scroll depth, click timing) cluster into detectable signatures. cite🛠web_search:15#0:~:text=Identical execution paths across runs...grouped as one behavioral signature

## Tool Stack (August 2026 Benchmark Rankings)

651 verdicts across 31 targets, 3 independent sweeps. cite🛠web_search:15#3:~:text=651 records (217 cells x 3 runs), zero verdict drift across five hours

| Tool | OK | Blocked | Why It Wins / Fails |
|------|----|---------|---------------------|
| **nodriver** | 28 | **0** | Direct CDP, no Playwright shim, zero automation-protocol fingerprint cite🛠web_search:15#3:~:text=nodriver wins outright with zero blocked targets |
| curl_cffi | 26 | 2 | TLS impersonation only; no JS engine cite🛠web_search:15#3:~:text=Raw curl_cffi ties CloakBrowser at 26 OK |
| CloakBrowser | 26 | 2 | 49 C++ patches but same result as 21-line curl wrapper cite🛠web_search:15#3:~:text=If a 21-line wrapper ties a 130MB patched fork, that fork is paying for something the matrix doesn't measure |
| Patchright | 25 | 3 | Best Playwright replacement; use `channel=chrome` cite🛠web_search:15#3:~:text=Patchright with channel=chrome beats vanilla by one OK |
| Camoufox | 25 | 3 | Firefox TLS shape; wins on google-search, loses on dev.to cite🛠web_search:15#3:~:text=Camoufox beats Chromium forks on google-search and medium's gate but loses dev.to on a Firefox TLS quirk |
| Vanilla Playwright | 24 | 5 | Detectable CDP handshake sequence cite🛠web_search:15#3:~:text=Playwright forks fail regardless of patch quality |

## Primary: nodriver (Zero Blocked Cells)

The only tool with zero blocked targets across 31 production sites. Drives system Chrome over raw WebSocket CDP — no Playwright accessibility layer, no `Runtime.enable` / `Target.setAutoAttach` startup sequence that anti-bot gates fingerprint. cite🛠web_search:15#3:~:text=nodriver connects to system Chrome's DevTools port over a plain WebSocket, without Playwright's accessibility layer

```python
import asyncio
import nodriver as uc

async def bypass():
    browser = await uc.start()
    page = await browser.get('https://canadianinsider.com')  # blocks everything else
    await page.sleep(5)
    content = await page.get_content()
    await page.save_screenshot("proof.png")
    browser.stop()

asyncio.run(bypass())
```

**Tradeoff:** AGPL-3.0 license. asyncio object model requires adapter layer in Playwright codebases.

## Fallback: Patchright + channel=chrome

Drop-in Playwright replacement. The `channel=chrome` flag runs system Chrome 148 — fingerprint protection at a layer no runtime patch can replicate. cite🛠web_search:15#3:~:text=channel=chrome tells it to drive the system's installed Google Chrome binary instead of a bundled Chromium

```python
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = context.new_page()
    page.goto("https://target-site.com")
```

## Firefox Alternative: Camoufox

Custom Firefox build with C-level spoofing. Firefox TLS shape is whitelisted on many Chrome-blocking gates. 0% headless score on CreepJS. cite🛠web_search:15#1:~:text=Using Camoufox, we're finally able to achieve 0% headless and stealth scores

```python
from camoufox.sync_api import Camoufox

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    page.goto("https://abrahamjuliot.github.io/creepjs/")
```

## HTTP-Only: curl_cffi

For tier 1-2 sites without JS. Patches libcurl to emit Chrome JA3/JA4 fingerprint. 26/31 targets with a 21-line wrapper. cite🛠web_search:15#3:~:text=curl_cffi is pip install curl_cffi + requests.get(url, impersonate=chrome)

```python
from curl_cffi import requests

r = requests.get("https://target-site.com", impersonate="chrome")
print(r.text)
```

## Shape-Coherent Profile Management

**The #1 mistake:** Heavy randomization increases detection risk. Inconsistent profiles reset on every run, never building storage/cache/behavioral history. cite🛠web_search:15#0:~:text=Profiles that reset on every run never build storage, cache, or behavioral history

**Correct approach:** Stateful personas with fixed traits across sessions.

```python
PERSONA = {
    "os": "macOS",                    # Match IP geolocation
    "browser": "Chrome 148",
    "viewport": (1920, 1080),
    "device_pixel_ratio": 2.0,        # Retina for macOS
    "timezone": "America/Toronto",    # Match proxy location
    "locale": "en-CA",
    "fonts": ["Helvetica Neue", "Arial", "Times"],
    "hardware_concurrency": 8,
    "device_memory": 8,               # GB
    "webrtc": "disabled",             # Prevent IP leaks
}
```

**Consistency rules:**
- macOS persona → macOS TLS fingerprint → North American residential IP
- Windows persona → Windows TLS fingerprint → matching timezone
- Never mix: Linux server + residential proxy + macOS navigator.platform

## Behavioral Telemetry (Scale Detection)

At low volume, behavior doesn't matter. At scale, identical patterns cluster.

```python
import random

def human_delay(action_type="click"):
    # Log-normal distribution (humans are right-skewed)
    base = {"click": 0.8, "scroll": 1.5, "type": 0.05}[action_type]
    return random.lognormvariate(mu=0, sigma=0.5) * base

def human_scroll():
    # Variable scroll depth with pauses
    for _ in range(random.randint(3, 8)):
        page.mouse.wheel(0, random.randint(300, 700))
        await asyncio.sleep(random.uniform(0.5, 2.0))
```

## Escalation Path (Browserless Model)

Don't start with the heaviest tool. Escalate only when needed. cite🛠web_search:15#0:~:text=Start with the lightest tooling that works...Only add complexity when correlation and challenges actually appear

| Stage | Tool | When |
|-------|------|------|
| 1 | curl_cffi | Static HTML, no JS |
| 2 | nodriver | JS-rendered, Cloudflare-gated |
| 3 | Patchright + stealth route | Existing Playwright codebase |
| 4 | Camoufox | Chrome-shaped gates, Firefox whitelisted |
| 5 | BrowserQL / BaaS | CAPTCHA + session continuity required |

## huh Project Integration

```
skill://fast-browser-use
├── research/           # 2026 arXiv paper summaries
├── benchmarks/         # 651-verdict matrix
├── profiles/           # Shape-coherent personas
├── nodriver/           # Primary bypass
├── patchright/         # Playwright fallback
├── camoufox/           # Firefox alternative
├── curl_cffi/          # HTTP-only floor
└── telemetry/          # Behavioral A/B testing
```

Trigger: `Load fast-browser-use with cloudflare bypass`
