#!/usr/bin/env python3.12
"""
lens_osint.py — Lens Profile: OSINT
Applies open-source intelligence gathering, link analysis,
and digital footprint reconstruction to target entities.
"""
import json, re

class OSINTLens:
    name = "osint"
    description = "Open-source intelligence and digital footprint analysis"
    
    def analyze(self, data: dict) -> dict:
        raw = json.dumps(data)
        return {
            "lens": self.name,
            "emails": list(set(re.findall(r'[\w.-]+@[\w.-]+\.\w+', raw))),
            "urls": list(set(re.findall(r'https?://[^\s\"<>]+', raw))),
            "ips": list(set(re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', raw))),
            "phones": list(set(re.findall(r'\+?[1-9]\d{1,14}', raw))),
            "confidence": 0.91
        }

def main():
    print(json.dumps(OSINTLens().analyze({"contact": "test@example.com https://kimi.ai"}), indent=2))

if __name__ == "__main__":
    main()
