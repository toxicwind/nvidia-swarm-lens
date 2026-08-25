---
name: fast-browser-use
description: >
  High-performance, Cloudflare-aware browser automation for AI agents.
  Bypasses bot detection via CDP-native Chrome control (nodriver),
  patched Playwright (Patchright), or TLS impersonation (curl_cffi).
  Handles Turnstile, JavaScript challenges, fingerprinting, and session persistence.
allowed-tools: Read, Browser
---

# Fast Browser Use — Cloudflare-Aware Edition

Stealth browser automation stack for 2026. Not baseline — this is the bypass layer.

## Stack Ranking (2026 Benchmarks)

| Tool | Best For | Cloudflare Pass | Speed | Maintenance |
|------|----------|-----------------|-------|-------------|
| **nodriver** | New Python projects | Zero blocked | Fast, async | Active |
| **Patchright** | Existing Playwright | +1 over vanilla | Fast | Active |
| **CloakBrowser** | Max stealth | 0.9 reCAPTCHA | Medium | Active |
| **curl_cffi** | No-JS targets | 26/31 sites | Blazing | Stable |
| **SeleniumBase UC** | CAPTCHA-heavy | Best for challenges | Medium | Active |

## Primary: nodriver (Recommended)

Direct Chrome DevTools Protocol — no WebDriver, no Playwright shim. The only tool with zero blocked cells across 31 Cloudflare targets.

```python
import asyncio
import nodriver as uc

async def scrape():
    browser = await uc.start()
    page = await browser.get('https://target-site.com')
    await asyncio.sleep(5)
    content = await page.get_content()
    await page.save_screenshot("proof.png")
    browser.stop()

asyncio.run(scrape())
```

Install: pip install nodriver

## Fallback: Patchright (Playwright Drop-in)

Swaps in for Playwright. Use channel=chrome to run system Chrome 148.

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

Install: pip install patchright && patchright install chrome

## Lightweight: curl_cffi (No Browser)

For tier 1-2 sites where JS execution isn't needed.

```python
from curl_cffi import requests
r = requests.get("https://target-site.com", impersonate="chrome")
print(r.text)
```

Install: pip install curl_cffi

## Cloudflare Bypass Checklist

1. IP Layer: Residential or mobile proxies
2. TLS Layer: Match JA3 fingerprint to User-Agent
3. Browser Layer: Remove navigator.webdriver, patch CDP leaks
4. Behavior Layer: Random delays (2-5s), mouse moves
5. Session Layer: Reuse cookies/localStorage

## huh Project Integration

skill://fast-browser-use
├── cloudflare-bypass (nodriver primary)
├── session-persistence
├── screenshot-evidence
└── proxy-rotation

Trigger: Load fast-browser-use with cloudflare bypass
