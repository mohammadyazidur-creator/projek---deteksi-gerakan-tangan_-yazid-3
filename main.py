"""Deteksi gerakan tangan menggunakan kamera HP yang dikirim melalui USB."""
import asyncio
import os
import time
from datetime import datetime

import aiohttp
import cv2
import mediapipe as mp
import numpy as np

from utils import draw_landmarks, get_finger_states, draw_finger_states, draw_fps
from gesture_classifier import classify_gesture, count_fingers

SERVER_WS = "http://127.0.0.1:8000/ws/pc"
DETECTION_CONF = 0.7
TRACKING_CONF = 0.6
MAX_HANDS = 2
SHOW_FINGER_STATES = True
SCREENSHOT_DIR = "screenshots"
COLOR_PRIMARY = (0, 255, 100)
COLOR_LEFT = (255, 150, 0)
COLOR_RIGHT = (0, 150, 255)


def setup_mediapipe():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=MAX_HANDS,
        min_detection_confidence=DETECTION_CONF,
        min_tracking_confidence=TRACKING_CONF,
    )
    return hands, mp_hands, mp_drawing, mp_styles


def draw_header(frame):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 45), (20, 20, 20), -1)
    cv2.putText(frame, "Deteksi Gerakan Tangan - Kamera HP USB", (10, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_PRIMARY, 2)
    cv2.line(frame, (0, 45), (w, 45), COLOR_PRIMARY, 1)


def draw_hand_info(frame, hand_label, gesture, finger_states, index, show_fingers):
    h, w = frame.shape[:2]
    x = 10 if index == 0 else w // 2 + 10
    color = COLOR_LEFT if hand_label == "Left" else COLOR_RIGHT
    label = "Kiri" if hand_label == "Left" else "Kanan"
    y = 65
    cv2.putText(frame, f"Tangan {label}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"Gestur: {gesture['name']}", (x, y + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    opened = count_fingers(finger_states)
    cv2.putText(frame, f"Jari terbuka: {opened} ({gesture['confidence']:.0%})",
                (x, y + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    if show_fingers:
        draw_finger_states(frame, finger_states, pos=(x, y + 90))


def process_frame(frame, hands, mp_hands, mp_drawing, mp_styles, show_fingers):
    # Video dari HP sudah dicerminkan di halaman web; tidak di-flip lagi di sini.
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    gestures = []
    if results.multi_hand_landmarks and results.multi_handedness:
        for i, (landmarks, handedness) in enumerate(
            zip(results.multi_hand_landmarks, results.multi_handedness)
        ):
            label = handedness.classification[0].label
            draw_landmarks(frame, landmarks, mp_hands, mp_drawing, mp_styles)
            states = get_finger_states(landmarks)
            gesture = classify_gesture(states)
            gestures.append((label, gesture, states))
            draw_hand_info(frame, label, gesture, states, i, show_fingers)
    return frame, gestures


async def run_detection():
    global SHOW_FINGER_STATES
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    hands, mp_hands, mp_drawing, mp_styles = setup_mediapipe()
    last_frame = None
    prev_time = time.time()
    fps_smooth = 0.0

    print("[INFO] Menghubungkan ke server kamera HP:", SERVER_WS)
    print("[INFO] Pastikan server_hp.py sudah berjalan.")
    try:
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.ws_connect(SERVER_WS, heartbeat=20) as ws:
                print("[BERHASIL] Python terhubung. Buka kamera dari HP.")
                while True:
                    try:
                        msg = await ws.receive(timeout=1.0)
                    except asyncio.TimeoutError:
                        msg = None

                    if msg is not None:
                        if msg.type == aiohttp.WSMsgType.BINARY:
                            frame = cv2.imdecode(np.frombuffer(msg.data, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                now = time.time()
                                fps = 1.0 / max(now - prev_time, 1e-9)
                                fps_smooth = fps_smooth * 0.9 + fps * 0.1
                                prev_time = now
                                frame, gestures = process_frame(
                                    frame, hands, mp_hands, mp_drawing, mp_styles,
                                    SHOW_FINGER_STATES
                                )
                                draw_header(frame)
                                draw_fps(frame, fps_smooth)
                                if not gestures:
                                    h, w = frame.shape[:2]
                                    cv2.putText(frame, "Arahkan tangan ke kamera HP...",
                                                (max(10, w // 2 - 220), h // 2),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)
                                cv2.putText(frame, "[Q] Keluar  [F] Status jari  [S] Screenshot",
                                            (10, frame.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX,
                                            0.48, (180, 180, 180), 1)
                                last_frame = frame.copy()
                                cv2.imshow("Deteksi Gerakan Tangan - Kamera HP", frame)
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            print("[WARNING] Koneksi server terputus.")
                            break

                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), 27):
                        break
                    elif key == ord("f"):
                        SHOW_FINGER_STATES = not SHOW_FINGER_STATES
                        print("[INFO] Status jari:", "ON" if SHOW_FINGER_STATES else "OFF")
                    elif key == ord("s") and last_frame is not None:
                        filename = os.path.join(
                            SCREENSHOT_DIR,
                            "gesture_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png",
                        )
                        if cv2.imwrite(filename, last_frame):
                            print("[INFO] Screenshot disimpan:", filename)
    except aiohttp.ClientConnectorError:
        print("[ERROR] Server tidak ditemukan. Jalankan server_hp.py terlebih dahulu.")
    except KeyboardInterrupt:
        print("[INFO] Program dihentikan pengguna.")
    finally:
        hands.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        asyncio.run(run_detection())
    except KeyboardInterrupt:
        print("\n[INFO] Program dihentikan.")
