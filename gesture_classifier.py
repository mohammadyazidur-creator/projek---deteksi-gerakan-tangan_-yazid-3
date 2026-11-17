"""
gesture_classifier.py - Klasifikasi gestur tangan berdasarkan status jari
"""

import numpy as np


# ─────────────────────────────────────────────
# Definisi gestur: (nama, emoji, pola jari)
# Pola: [ibu jari, telunjuk, tengah, manis, kelingking]
#       1 = terbuka, 0 = tertutup, None = bebas (don't care)
# ─────────────────────────────────────────────
GESTURE_RULES = [
    {
        "name": "Open Hand",
        "emoji": "✋",
        "pattern": [1, 1, 1, 1, 1],
        "description": "Semua jari terbuka"
    },
    {
        "name": "Closed Fist",
        "emoji": "✊",
        "pattern": [0, 0, 0, 0, 0],
        "description": "Semua jari tertutup"
    },
    {
        "name": "Thumbs Up",
        "emoji": "👍",
        "pattern": [1, 0, 0, 0, 0],
        "description": "Hanya ibu jari terbuka"
    },
    {
        "name": "Peace / Victory",
        "emoji": "✌",
        "pattern": [0, 1, 1, 0, 0],
        "description": "Telunjuk & tengah terbuka"
    },
    {
        "name": "Rock",
        "emoji": "🤘",
        "pattern": [0, 1, 0, 0, 1],
        "description": "Telunjuk & kelingking terbuka"
    },
    {
        "name": "OK",
        "emoji": "👌",
        "pattern": [1, 0, 1, 1, 1],
        "description": "Ibu jari + tengah + manis + kelingking terbuka"
    },
    {
        "name": "Pointing",
        "emoji": "☞",
        "pattern": [0, 1, 0, 0, 0],
        "description": "Hanya telunjuk terbuka"
    },
    {
        "name": "Call Me",
        "emoji": "🤙",
        "pattern": [1, 0, 0, 0, 1],
        "description": "Ibu jari & kelingking terbuka"
    },
    {
        "name": "Three",
        "emoji": "🤟",
        "pattern": [0, 1, 1, 1, 0],
        "description": "Telunjuk, tengah & manis terbuka"
    },
    {
        "name": "Four",
        "emoji": "🖖",
        "pattern": [0, 1, 1, 1, 1],
        "description": "Empat jari terbuka (kecuali ibu jari)"
    },
]


def classify_gesture(finger_states: list) -> dict:
    """
    Klasifikasikan gestur berdasarkan status jari.
    
    Args:
        finger_states: list[int] — [ibu, telunjuk, tengah, manis, kelingking]
                       1 = terbuka, 0 = tertutup
    
    Returns:
        dict berisi: name, emoji, description, confidence, matched_fingers
    """
    best_match = None
    best_score = -1

    for gesture in GESTURE_RULES:
        pattern = gesture["pattern"]
        matches = sum(
            1 for s, p in zip(finger_states, pattern) if p is None or s == p
        )
        total = len([p for p in pattern if p is not None])
        score = matches / max(total, 1)

        if score > best_score:
            best_score = score
            best_match = gesture

    if best_score < 0.8:
        return {
            "name": "Unknown",
            "emoji": "❓",
            "description": "Gestur tidak dikenali",
            "confidence": best_score,
            "matched_fingers": 0
        }

    return {
        "name": best_match["name"],
        "emoji": best_match["emoji"],
        "description": best_match["description"],
        "confidence": best_score,
        "matched_fingers": int(best_score * len(best_match["pattern"]))
    }


def count_fingers(finger_states: list) -> int:
    """Hitung jumlah jari yang terbuka."""
    return sum(finger_states)

