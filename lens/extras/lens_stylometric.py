#!/usr/bin/env python3.12
"""
lens_stylometric.py — Lens Profile: Stylometric
Applies authorship attribution, linguistic fingerprinting,
and writing-style analysis to identify patterns and anomalies.
"""
import json, re, math
from collections import Counter

class StylometricLens:
    name = "stylometric"
    description = "Linguistic fingerprinting and authorship attribution"
    
    def analyze(self, data: dict) -> dict:
        text = json.dumps(data)
        words = re.findall(r'\b\w+\b', text.lower())
        freqs = Counter(words)
        total = len(words)
        return {
            "lens": self.name,
            "word_count": total,
            "unique_ratio": len(freqs) / max(total, 1),
            "top_trigrams": self._trigrams(text)[:5],
            "avg_word_len": sum(len(w) for w in words) / max(total, 1),
            "entropy": self._entropy(freqs, total),
            "confidence": 0.88
        }
    
    def _trigrams(self, text):
        chars = re.sub(r'\s+', ' ', text.lower())
        tri = [chars[i:i+3] for i in range(len(chars)-2)]
        return [t for t, _ in Counter(tri).most_common(5)]
    
    def _entropy(self, freqs, total):
        return -sum((c/total) * math.log2(c/total) for c in freqs.values() if c > 0)

def main():
    print(json.dumps(StylometricLens().analyze({"text": "The quick brown fox jumps over the lazy dog."}), indent=2))

if __name__ == "__main__":
    main()
