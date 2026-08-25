#!/usr/bin/env python3
import os, sys, subprocess, json

SKILL_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG = {
    "binaries": {
        "nodriver": {"type": "pip", "package": "nodriver", "test": "nodriver"},
        "patchright": {"type": "pip", "package": "patchright", "test": "patchright", "post": "python -m patchright install chrome"},
        "camoufox": {"type": "pip", "package": "camoufox", "test": "camoufox", "post": "python -m camoufox fetch"},
        "curl_cffi": {"type": "pip", "package": "curl_cffi", "test": "curl_cffi"},
    }
}

def check(m): 
    try: __import__(m); return True
    except: return False

def install(pkg, post=None):
    ok = subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True).returncode == 0
    if ok and post: subprocess.run(post, shell=True)
    return ok

def load_all():
    for name, spec in CONFIG["binaries"].items():
        if check(spec["test"]): print(f"[OK] {name} already installed"); continue
        if install(spec["package"], spec.get("post")) and check(spec["test"]):
            print(f"[OK] {name} installed")
        else:
            print(f"[FAIL] {name}")

if __name__ == "__main__":
    if len(sys.argv) < 2: print("Usage: python loader.py load|test"); sys.exit(0)
    if sys.argv[1] == "load": load_all()
    elif sys.argv[1] == "test":
        print("Testing curl_cffi...")
        try:
            from curl_cffi import requests
            r = requests.get("https://httpbin.org/ip", impersonate="chrome")
            print(f"[OK] {r.json()}")
        except Exception as e:
            print(f"[FAIL] {e}")
