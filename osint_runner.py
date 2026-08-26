#!/usr/bin/env python3
"""
OSINT Runner — Dr. Squatch One Piece Collection
Uses nodriver (confirmed in subprocess Python) + stdlib only
Saves to /mnt/agents/output/huh-project/logs/
"""

import asyncio
import json
import time
import os
import re

# nodriver is available in subprocess Python
import nodriver as uc

OUTDIR = "/mnt/agents/output/huh-project/logs"
os.makedirs(OUTDIR, exist_ok=True)

async def main():
    print("[OSINT] Starting headless Chrome via nodriver...")
    browser = await uc.start(headless=True, browser_args=[
        '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
        '--disable-web-security', '--window-size=1920,1080',
        '--disable-features=IsolateOrigins,site-per-process',
    ])
    print("[OK] Browser started")

    # === PHASE 1: One Piece Collection Page ===
    print("\n[PHASE 1] Rendering /collections/one-piece...")
    page = await browser.get("https://drsquatch.com/collections/one-piece")
    await page.sleep(6)

    content = await page.get_content()
    print(f"[OK] Content: {len(content):,} bytes")

    # Extract all product links
    links = await page.query_selector_all('a[href*="/products/"]')
    print(f"[OK] Found {len(links)} product link elements")

    products = []
    seen = set()
    for link in links[:50]:
        try:
            href = await link.get_attribute('href') or ''
            text = (await link.get_text() or '').strip()
            if text and len(text) > 2:
                key = href + '|' + text
                if key not in seen:
                    seen.add(key)
                    products.append({'text': text[:100], 'href': href})
        except Exception as e:
            pass

    print(f"[OK] {len(products)} unique products:")
    for p in products[:20]:
        print(f"  -> {p['text'][:55]:55s} | {p['href'][:50]}")

    # Extract body text
    body_text = await page.evaluate("document.body.innerText")
    lines = [l.strip() for l in body_text.split('\n') if l.strip() and len(l.strip()) > 3]

    # Search for keywords
    doc_lines = [l for l in lines if 'doc' in l.lower() and len(l) < 200]
    note_lines = [l for l in lines if 'note' in l.lower() and len(l) < 200]
    op_lines = [l for l in lines if 'one piece' in l.lower() and len(l) < 200]
    soap_lines = [l for l in lines if 'soap' in l.lower() and len(l) < 200]

    print(f"\n[OK] 'Doc' mentions: {len(doc_lines)}")
    for l in doc_lines[:8]: print(f"  -> {l[:100]}")
    print(f"[OK] 'Note' mentions: {len(note_lines)}")
    for l in note_lines[:8]: print(f"  -> {l[:100]}")
    print(f"[OK] 'One Piece' mentions: {len(op_lines)}")
    for l in op_lines[:8]: print(f"  -> {l[:100]}")
    print(f"[OK] 'Soap' mentions: {len(soap_lines)}")
    for l in soap_lines[:8]: print(f"  -> {l[:100]}")

    # Check for exact match
    has_docs_notes = "doc\'s notes" in body_text.lower() or "docs notes" in body_text.lower()
    print(f"\n[OK] 'Doc\'s Notes' exact match: {has_docs_notes}")

    # Screenshot
    screenshot_path = os.path.join(OUTDIR, "drsquatch-onepiece-collection.png")
    await page.save_screenshot(screenshot_path)
    print(f"[OK] Screenshot: {screenshot_path}")

    # === PHASE 2: Scroll for lazy-loaded content ===
    print("\n[PHASE 2] Scrolling for lazy-loaded products...")
    await page.scroll_down(1200)
    await page.sleep(4)

    content2 = await page.get_content()
    print(f"[OK] Post-scroll content: {len(content2):,} bytes")

    # Re-extract after scroll
    links2 = await page.query_selector_all('a[href*="/products/"]')
    products2 = []
    seen2 = set()
    for link in links2[:50]:
        try:
            href = await link.get_attribute('href') or ''
            text = (await link.get_text() or '').strip()
            if text and len(text) > 2:
                key = href + '|' + text
                if key not in seen2:
                    seen2.add(key)
                    products2.append({'text': text[:100], 'href': href})
        except:
            pass

    new_products = [p for p in products2 if p['href'] + '|' + p['text'] not in seen]
    print(f"[OK] {len(new_products)} new products after scroll")
    for p in new_products[:10]:
        print(f"  -> {p['text'][:55]:55s} | {p['href'][:50]}")

    all_products = products + new_products

    # === PHASE 3: Try to find specific product pages ===
    print("\n[PHASE 3] Testing known product handles...")
    handles_to_try = [
        "docs-notes", "doc-s-notes", "doctor-notes", "doc-notes",
        "one-piece-soap", "one-piece-bar-soap", "luffy-soap",
        "straw-hat-soap", "devil-fruit-soap", "going-merry-soap",
    ]

    found_products = []
    for handle in handles_to_try:
        test_url = f"https://drsquatch.com/products/{handle}"
        try:
            test_page = await browser.get(test_url)
            await test_page.sleep(3)
            title = await test_page.evaluate("document.title")
            if "404" not in title.lower() and "not found" not in title.lower():
                print(f"  [HIT] {handle}: {title[:60]}")
                found_products.append({
                    'handle': handle,
                    'title': title,
                    'url': test_url
                })
                # Screenshot this product
                ss_path = os.path.join(OUTDIR, f"product-{handle}.png")
                await test_page.save_screenshot(ss_path)
            else:
                print(f"  [MISS] {handle}: 404")
        except Exception as e:
            print(f"  [ERR] {handle}: {e}")

    # === PHASE 4: Shopify JSON API ===
    print("\n[PHASE 4] Shopify JSON API fallback...")
    import urllib.request

    api_products = []
    for page_num in range(1, 6):
        api_url = f"https://drsquatch.com/products.json?limit=250&page={page_num}"
        try:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
                prods = data.get('products', [])
                if not prods:
                    break
                api_products.extend(prods)
                print(f"  [OK] Page {page_num}: +{len(prods)} products (total: {len(api_products)})")
        except Exception as e:
            print(f"  [ERR] Page {page_num}: {e}")
            break

    # Search API products for One Piece / Doc
    keywords = ['one piece', 'one-piece', 'luffy', 'zoro', 'nami', 'sanji', 
                'doc', 'notes', 'anime', 'collab', 'collaboration', 'limited']
    matches = []
    for p in api_products:
        combined = f"{(p.get('title') or '').lower()} {(p.get('handle') or '').lower()} {(p.get('product_type') or '').lower()} {' '.join(p.get('tags') or []).lower()}"
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            variants = p.get('variants', [])
            price = variants[0].get('price', 'N/A') if variants else 'N/A'
            matches.append({
                'title': p.get('title'),
                'handle': p.get('handle'),
                'type': p.get('product_type'),
                'price': price,
                'tags': p.get('tags', []),
                'score': score,
                'created_at': p.get('created_at'),
                'updated_at': p.get('updated_at'),
            })

    matches.sort(key=lambda x: (-x['score'], x.get('updated_at', '')), reverse=False)
    print(f"\n[OK] API matches: {len(matches)}")
    for m in matches[:15]:
        print(f"  -> {m['title'][:50]:50s} | ${m['price']:>6s} | {m['handle'][:30]:30s} | score:{m['score']}")

    browser.stop()

    # === SAVE EVERYTHING ===
    result = {
        "method": "nodriver_subprocess",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collection_url": "https://drsquatch.com/collections/one-piece",
        "products_rendered": all_products,
        "products_count": len(all_products),
        "doc_mentions": doc_lines[:15],
        "note_mentions": note_lines[:15],
        "op_mentions": op_lines[:15],
        "soap_mentions": soap_lines[:15],
        "has_docs_notes_exact": has_docs_notes,
        "found_product_pages": found_products,
        "api_total_products": len(api_products),
        "api_matches": matches[:30],
        "screenshots": [
            "drsquatch-onepiece-collection.png",
        ] + [f"product-{p['handle']}.png" for p in found_products],
    }

    out_path = os.path.join(OUTDIR, "osint-complete.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[OK] Complete OSINT saved to: {out_path}")
    print(f"[OK] Screenshots in: {OUTDIR}")

if __name__ == "__main__":
    asyncio.run(main())
