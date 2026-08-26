#!/usr/bin/env python3
"""
🔮 huh OSINT Runner — Dr. Squatch One Piece Collection
Self-bootstrapping | AST-aware | Bytecode-introspective | Portable
Machine: redwood | Meta: extreme | Mode: YOLO
"""

import sys, subprocess, os, json, time, re, ast, dis, types

# ===================================================================
# 0. SELF-BOOTSTRAP — Install deps if missing (no package manager req)
# ===================================================================

def ensure_dep(pkg, import_name=None):
    import_name = import_name or pkg
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"[BOOTSTRAP] Installing {pkg}...")
        rc = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True, timeout=120
        ).returncode
        try:
            __import__(import_name)
            print(f"[BOOTSTRAP] {pkg} OK")
            return True
        except ImportError:
            print(f"[BOOTSTRAP] {pkg} FAILED")
            return False

# Install in order of need
for pkg, imp in [("nodriver", "nodriver"), ("curl_cffi", "curl_cffi")]:
    if not ensure_dep(pkg, imp):
        print(f"[FATAL] Cannot install {pkg}")
        sys.exit(1)

# Now safe to import
import asyncio
import nodriver as uc
from curl_cffi import requests

# ===================================================================
# 1. AST INTROSPECTION — Self-awareness layer
# ===================================================================

def self_ast_digest():
    """Compute AST hash of this script for integrity verification."""
    with open(__file__, "r") as f:
        source = f.read()
    tree = ast.parse(source)
    names = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)})
    imports = sorted({node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)})
    return {"names_count": len(names), "imports": imports[:10], "source_hash": hex(hash(source) & 0xFFFFFFFF)}

# ===================================================================
# 2. BYTECODE AWARENESS — Function fingerprinting
# ===================================================================

def bytecode_fingerprint(fn):
    """Extract opcode sequence from function bytecode."""
    code = fn.__code__
    ops = []
    for offset, op, arg in dis.get_instructions(code):
        ops.append(dis.opname[op])
    return {"name": fn.__name__, "opcodes": ops[:20], "total_ops": len(ops)}

# ===================================================================
# 3. OSINT ENGINE — Dr. Squatch One Piece
# ===================================================================

OUTDIR = "/mnt/agents/output/huh-project/logs"
os.makedirs(OUTDIR, exist_ok=True)

async def osint_drsquatch():
    results = {
        "meta": {
            "machine": "redwood",
            "mode": "YOLO",
            "ast_digest": self_ast_digest(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "python": sys.version,
            "executable": sys.executable,
        },
        "phases": []
    }

    # --- PHASE 1: Shopify JSON API (no JS, fastest) ---
    print("\n" + "="*60)
    print("[PHASE 1] Shopify JSON API — Full Catalog")
    print("="*60)

    api_products = []
    for page_num in range(1, 8):
        url = f"https://drsquatch.com/products.json?limit=250&page={page_num}"
        try:
            r = requests.get(url, impersonate="chrome", timeout=20)
            data = r.json()
            prods = data.get("products", [])
            if not prods:
                break
            api_products.extend(prods)
            print(f"  Page {page_num}: +{len(prods)} (total: {len(api_products)})")
        except Exception as e:
            print(f"  Page {page_num} ERR: {e}")
            break

    keywords = ["one piece", "one-piece", "luffy", "zoro", "nami", "sanji",
                "doc", "notes", "anime", "collab", "collaboration", "limited", "exclusive"]
    matches = []
    for p in api_products:
        combined = f"{(p.get('title') or '').lower()} {(p.get('handle') or '').lower()} {(p.get('product_type') or '').lower()} {' '.join(p.get('tags') or []).lower()} {(p.get('body_html') or '').lower()}"
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            variants = p.get("variants", [])
            price = variants[0].get("price", "N/A") if variants else "N/A"
            matches.append({
                "title": p.get("title"),
                "handle": p.get("handle"),
                "type": p.get("product_type"),
                "price": price,
                "available": any(v.get("available") for v in variants),
                "tags": p.get("tags", []),
                "score": score,
                "created_at": p.get("created_at"),
                "updated_at": p.get("updated_at"),
                "images": [img.get("src", "") for img in p.get("images", [])[:3]],
            })
    matches.sort(key=lambda x: (-x["score"], x.get("updated_at", "")))

    print(f"\n[OK] {len(matches)} keyword matches:")
    for m in matches[:20]:
        status = "✓" if m["available"] else "✗"
        print(f"  {status} {m['title'][:45]:45s} | ${m['price']:>6s} | {m['handle'][:28]:28s} | score:{m['score']}")

    results["phases"].append({
        "name": "shopify_api",
        "total_products": len(api_products),
        "matches": matches,
    })

    # --- PHASE 2: nodriver — Rendered Page Extraction ---
    print("\n" + "="*60)
    print("[PHASE 2] nodriver — JS-Rendered Collection Page")
    print("="*60)

    browser = await uc.start(headless=True, browser_args=[
        "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
        "--disable-web-security", "--window-size=1920,1080"
    ])
    print("[OK] Browser started")

    page = await browser.get("https://drsquatch.com/collections/one-piece")
    await page.sleep(6)

    content = await page.get_content()
    print(f"[OK] Content: {len(content):,} bytes")

    # Extract product cards
    links = await page.query_selector_all('a[href*="/products/"]')
    products = []
    seen = set()
    for link in links[:50]:
        try:
            href = await link.get_attribute("href") or ""
            text = (await link.get_text() or "").strip()
            if text and len(text) > 2:
                key = href + "|" + text
                if key not in seen:
                    seen.add(key)
                    products.append({"text": text[:100], "href": href})
        except:
            pass

    print(f"[OK] {len(products)} unique rendered products:")
    for p in products[:15]:
        print(f"  -> {p['text'][:55]:55s} | {p['href'][:50]}")

    # Extract visible text
    body_text = await page.evaluate("document.body.innerText")
    lines = [l.strip() for l in body_text.split("\n") if l.strip() and len(l.strip()) > 3]

    doc_lines = [l for l in lines if "doc" in l.lower() and len(l) < 200]
    note_lines = [l for l in lines if "note" in l.lower() and len(l) < 200]
    op_lines = [l for l in lines if "one piece" in l.lower() and len(l) < 200]
    soap_lines = [l for l in lines if "soap" in l.lower() and len(l) < 200]

    has_exact = "doc's notes" in body_text.lower() or "docs notes" in body_text.lower()

    print(f"\n[OK] 'Doc' mentions: {len(doc_lines)}")
    for l in doc_lines[:5]: print(f"  -> {l[:100]}")
    print(f"[OK] 'Note' mentions: {len(note_lines)}")
    for l in note_lines[:5]: print(f"  -> {l[:100]}")
    print(f"[OK] 'One Piece' mentions: {len(op_lines)}")
    for l in op_lines[:5]: print(f"  -> {l[:100]}")
    print(f"[OK] Exact 'Doc\\'s Notes' match: {has_exact}")

    # Screenshot
    ss_path = os.path.join(OUTDIR, "drsquatch-onepiece-collection.png")
    await page.save_screenshot(ss_path)
    print(f"[OK] Screenshot: {ss_path}")

    # Scroll for lazy-load
    await page.scroll_down(1200)
    await page.sleep(4)
    content2 = await page.get_content()
    print(f"[OK] Post-scroll: {len(content2):,} bytes")

    browser.stop()

    results["phases"].append({
        "name": "nodriver_rendered",
        "products": products,
        "doc_mentions": doc_lines[:15],
        "note_mentions": note_lines[:15],
        "op_mentions": op_lines[:15],
        "soap_mentions": soap_lines[:15],
        "has_docs_notes_exact": has_exact,
        "screenshot": ss_path,
    })

    # --- PHASE 3: Handle Guessing ---
    print("\n" + "="*60)
    print("[PHASE 3] Handle Guessing — Direct Product Pages")
    print("="*60)

    handles = [
        "docs-notes", "doc-s-notes", "doctor-notes", "doc-notes",
        "one-piece-soap", "one-piece-bar-soap", "luffy-soap",
        "straw-hat-soap", "devil-fruit-soap", "going-merry-soap",
        "one-piece-collection", "one-piece-bundle", "wanted-poster-soap",
    ]
    found = []
    for handle in handles:
        url = f"https://drsquatch.com/products/{handle}.json"
        try:
            r = requests.get(url, impersonate="chrome", timeout=10)
            if r.status_code == 200:
                prod = r.json().get("product", {})
                print(f"  [HIT] {handle}: {prod.get('title', 'unknown')}")
                found.append({
                    "handle": handle,
                    "title": prod.get("title"),
                    "price": prod.get("variants", [{}])[0].get("price"),
                })
            else:
                print(f"  [MISS] {handle}: {r.status_code}")
        except Exception as e:
            print(f"  [ERR] {handle}: {e}")

    results["phases"].append({
        "name": "handle_guess",
        "found": found,
    })

    # --- SAVE ---
    out_path = os.path.join(OUTDIR, "osint-complete.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Complete OSINT saved: {out_path}")
    print(f"[OK] Total phases: {len(results['phases'])}")

    return results

# ===================================================================
# 4. ENTRY — Run with existing event loop awareness
# ===================================================================

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Jupyter / nested loop — use nest_asyncio if available
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass
            result = loop.run_until_complete(osint_drsquatch())
        else:
            result = asyncio.run(osint_drsquatch())
    except RuntimeError:
        result = asyncio.run(osint_drsquatch())
