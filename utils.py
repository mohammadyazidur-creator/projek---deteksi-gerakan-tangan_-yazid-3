"""
utils.py - Helper functions untuk proyek membaca gerakan tangan
"""

import cv2
import numpy as np


def draw_landmarks(frame, hand_landmarks, mp_hands, mp_drawing, mp_drawing_styles):
    """Gambar landmark tangan di frame."""
    mp_drawing.draw_landmarks(
        frame,
        hand_landmarks,
        mp_hands.HAND_CONNECTIONS,
        mp_drawing_styles.get_default_hand_landmarks_style(),
        mp_drawing_styles.get_default_hand_connections_style()
    )


def get_finger_states(hand_landmarks):
    """
    Tentukan apakah setiap jari terbuka (1) atau tertutup (0).
    Urutan: [ibu jari, telunjuk, tengah, manis, kelingking]
    """
    landmarks = hand_landmarks.landmark

    # Tip IDs untuk setiap jari
    finger_tips = [4, 8, 12, 16, 20]
    # MCP / PIP IDs (sendi di bawah tip)
    finger_pip   = [3, 6, 10, 14, 18]

    finger_states = []

    # Ibu jari — bandingkan posisi x (kiri vs kanan)
    # Jika tip lebih ke kiri dari sendi MCP → terbuka (asumsi tangan kanan)
    if landmarks[4].x < landmarks[3].x:
        finger_states.append(1)  # terbuka
    else:
        finger_states.append(0)  # tertutup

    # 4 jari lainnya — bandingkan posisi y (tip vs PIP)
    for tip_id, pip_id in zip(finger_tips[1:], finger_pip[1:]):
        if landmarks[tip_id].y < landmarks[pip_id].y:
            finger_states.append(1)  # terbuka (tip lebih tinggi = y lebih kecil)
        else:
            finger_states.append(0)  # tertutup

    return finger_states  # [ibu, telunjuk, tengah, manis, kelingking]


def draw_info_box(frame, label, confidence=None, pos=(10, 50)):
    """Tampilkan kotak informasi gestur di frame."""
    x, y = pos
    text = label
    if confidence is not None:
        text = f"{label} ({confidence:.0%})"

    # Background box
    (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)
    cv2.rectangle(frame, (x - 5, y - text_h - 10), (x + text_w + 5, y + 5), (0, 0, 0), -1)
    cv2.rectangle(frame, (x - 5, y - text_h - 10), (x + text_w + 5, y + 5), (0, 255, 100), 2)

    # Teks
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 100), 2)


def draw_finger_states(frame, finger_states, pos=(10, 100)):
    """Tampilkan status setiap jari (terbuka/tertutup)."""
    labels = ["Ibu", "Telunjuk", "Tengah", "Manis", "Kelingking"]
    x, y = pos
    for i, (name, state) in enumerate(zip(labels, finger_states)):
        color = (0, 255, 0) if state == 1 else (0, 0, 255)
        status = "BUKA" if state == 1 else "TUTUP"
        cv2.putText(frame, f"{name}: {status}", (x, y + i * 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)


def draw_fps(frame, fps):
    """Tampilkan FPS di sudut kanan atas."""
    h, w = frame.shape[:2]
    cv2.putText(frame, f"FPS: {fps:.1f}", (w - 150, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

