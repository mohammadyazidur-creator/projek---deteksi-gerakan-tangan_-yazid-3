"""
utils.py - Helper functions untuk proyek membaca gerakan tangan
"""

import cv2
import numpy as np


def draw_landmarks(frame, hand_landmarks, mp_hands=None, mp_drawing=None, mp_drawing_styles=None):
    """Gambar landmark tangan di frame untuk API MediaPipe lama maupun baru."""
    if mp_hands is not None and mp_drawing is not None and mp_drawing_styles is not None and hasattr(mp_hands, "HAND_CONNECTIONS"):
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style()
        )
        return

    connections = None
    if mp_hands is not None and hasattr(mp_hands, "HAND_CONNECTIONS"):
        connections = mp_hands.HAND_CONNECTIONS
    else:
        try:
            from mediapipe.tasks.python import vision
            connections = vision.HandLandmarksConnections.HAND_CONNECTIONS
        except Exception:
            connections = []

    h, w = frame.shape[:2]
    if connections:
        for connection in connections:
            start = hand_landmarks[connection.start]
            end = hand_landmarks[connection.end]
            cv2.line(frame, (int(start.x * w), int(start.y * h)), (int(end.x * w), int(end.y * h)), (0, 255, 0), 2)

    for landmark in hand_landmarks:
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)


def _is_thumb_open(landmarks):
    points = np.array([
        [landmark.x, landmark.y, getattr(landmark, "z", 0.0)]
        for landmark in landmarks
    ])
    mcp, ip, tip = points[2], points[3], points[4]
    first_segment = mcp - ip
    second_segment = tip - ip
    segment_lengths = np.linalg.norm(first_segment) * np.linalg.norm(second_segment)
    if segment_lengths == 0:
        return False

    angle_cosine = np.dot(first_segment, second_segment) / segment_lengths
    angle = np.degrees(np.arccos(np.clip(angle_cosine, -1.0, 1.0)))
    palm_width = np.linalg.norm(points[5] - points[17])
    extension_from_index = (
        np.linalg.norm(tip - points[5]) - np.linalg.norm(ip - points[5])
    )
    return angle > 150 and extension_from_index > palm_width * 0.1


def get_finger_states(hand_landmarks):
    """
    Tentukan apakah setiap jari terbuka (1) atau tertutup (0).
    Urutan: [ibu jari, telunjuk, tengah, manis, kelingking]
    """
    landmarks = getattr(hand_landmarks, "landmark", hand_landmarks)

    # Tip IDs untuk setiap jari
    finger_tips = [4, 8, 12, 16, 20]
    # MCP / PIP IDs (sendi di bawah tip)
    finger_pip   = [3, 6, 10, 14, 18]

    finger_states = []

    finger_states.append(int(_is_thumb_open(landmarks)))

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

