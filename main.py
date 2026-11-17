"""Deteksi gerakan tangan menggunakan webcam PC."""
import ctypes
import os
import platform
import shutil
import subprocess
import time
import urllib.request
from datetime import datetime
from importlib import resources

import cv2
import numpy as np

from utils import draw_landmarks, get_finger_states, draw_finger_states, draw_fps
from gesture_classifier import classify_gesture, count_fingers

CAMERA_INDEX = 0
DETECTION_CONF = 0.7
TRACKING_CONF = 0.6
MAX_HANDS = 2
SHOW_FINGER_STATES = True
SCREENSHOT_DIR = "screenshots"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
COLOR_PRIMARY = (0, 255, 100)
COLOR_LEFT = (255, 150, 0)
COLOR_RIGHT = (0, 150, 255)
GESTURE_SPEECH = {
    "Open Hand": "buka",
    "Closed Fist": "tutup",
    "Thumbs Up": "jempol",
    "Peace / Victory": "peace",
    "Rock": "rock",
    "OK": "oke",
    "Pointing": "tunjuk",
    "Call Me": "telepon",
    "Three": "tiga",
    "Four": "empat",
}


class GestureSpeaker:
    def __init__(self):
        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if not powershell:
            raise RuntimeError("PowerShell tidak ditemukan; fitur suara membutuhkan Windows PowerShell.")

        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "while (($text = [Console]::In.ReadLine()) -ne $null) { $speaker.Speak($text) }"
        )
        try:
            self.process = subprocess.Popen(
                [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="ascii",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except OSError as error:
            raise RuntimeError(f"Tidak bisa memulai suara Windows: {error}") from error

    def speak(self, text):
        if self.process.poll() is not None:
            raise RuntimeError("Proses suara Windows berhenti sebelum dapat membacakan gestur.")
        try:
            self.process.stdin.write(text + "\n")
            self.process.stdin.flush()
        except OSError as error:
            raise RuntimeError(f"Gagal mengirim gestur ke suara Windows: {error}") from error

    def close(self):
        if self.process.poll() is None:
            try:
                self.process.stdin.close()
            except OSError as error:
                print(f"[WARNING] Gagal menutup input suara: {error}")
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=2)


class GestureAnnouncer:
    def __init__(self, speaker):
        self.speaker = speaker
        self.previous_gestures = {}

    def update(self, gestures):
        current_gestures = {}
        for hand_label, gesture, _ in gestures:
            name = gesture["name"]
            current_gestures[hand_label] = name
            spoken_text = GESTURE_SPEECH.get(name)
            if spoken_text and self.previous_gestures.get(hand_label) != name:
                self.speaker.speak(spoken_text)
                print(f"[INFO] Suara gestur: {spoken_text}")
        self.previous_gestures = current_gestures


def patch_mediapipe_windows():
    """MediaPipe pada Windows memerlukan patch kecil agar loader C++ bisa memanggil free() dari CRT."""
    try:
        import mediapipe
        if hasattr(mediapipe, "solutions"):
            return
    except Exception:
        pass

    try:
        from mediapipe.tasks.python.core import mediapipe_c_bindings

        def load_raw_library_fixed(signatures=()):
            if mediapipe_c_bindings._shared_lib is None:
                if os.name == "posix":
                    if platform.system() == "Darwin":
                        lib_filename = "libmediapipe.dylib"
                    else:
                        lib_filename = "libmediapipe.so"
                else:
                    lib_filename = "libmediapipe.dll"
                lib_path_context = resources.files("mediapipe.tasks.c")
                absolute_lib_path = str(lib_path_context / lib_filename)
                mediapipe_c_bindings._shared_lib = ctypes.CDLL(absolute_lib_path)

            for signature in signatures:
                c_func = getattr(mediapipe_c_bindings._shared_lib, signature.func_name)
                c_func.argtypes = signature.argtypes
                c_func.restype = signature.restype

            msvcrt = ctypes.CDLL("msvcrt")
            mediapipe_c_bindings._shared_lib.free = msvcrt.free
            mediapipe_c_bindings._shared_lib.free.argtypes = [ctypes.c_void_p]
            mediapipe_c_bindings._shared_lib.free.restype = None
            return mediapipe_c_bindings._shared_lib

        mediapipe_c_bindings.load_raw_library = load_raw_library_fixed
    except Exception:
        pass


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("[INFO] Mengunduh model MediaPipe Hand Landmarker...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[INFO] Model siap:", MODEL_PATH)


def setup_mediapipe():
    patch_mediapipe_windows()
    ensure_model()

    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision.core import image as mp_image

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=MAX_HANDS,
        min_hand_detection_confidence=DETECTION_CONF,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=TRACKING_CONF,
    )
    landmarker = vision.HandLandmarker.create_from_options(options)
    return landmarker, mp_image


def draw_header(frame):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 45), (20, 20, 20), -1)
    cv2.putText(frame, "Deteksi Gerakan Tangan - Webcam PC", (10, 32),
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


def process_frame(frame, hand_landmarker, mp_image, show_fingers):
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp_image.Image(mp_image.ImageFormat.SRGB, rgb)
    results = hand_landmarker.detect_for_video(image, int(time.time() * 1000))
    gestures = []

    if results.hand_landmarks:
        for i, (landmarks, handedness) in enumerate(zip(results.hand_landmarks, results.handedness)):
            label = handedness[0].category_name if handedness else "Right"
            label = "Left" if label == "Left" else "Right"
            draw_landmarks(frame, landmarks)
            states = get_finger_states(landmarks)
            gesture = classify_gesture(states)
            gestures.append((label, gesture, states))
            draw_hand_info(frame, label, gesture, states, i, show_fingers)
    return frame, gestures


def run_detection():
    global SHOW_FINGER_STATES
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    hand_landmarker, mp_image = setup_mediapipe()
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_MSMF)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not camera.isOpened():
        camera.release()
        hand_landmarker.close()
        raise RuntimeError(
            f"Tidak bisa membuka webcam index {CAMERA_INDEX}. "
            "Periksa izin kamera Windows, tutup aplikasi lain yang memakai kamera, "
            "atau ubah CAMERA_INDEX."
        )

    last_frame = None
    prev_time = time.time()
    fps_smooth = 0.0
    speaker = None

    print(f"[INFO] Webcam PC aktif (index {CAMERA_INDEX}). Tekan Q untuk keluar.")
    try:
        speaker = GestureSpeaker()
        announcer = GestureAnnouncer(speaker)
        while True:
            success, frame = camera.read()
            if not success:
                raise RuntimeError(
                    "Webcam terbuka tetapi tidak mengirim video. "
                    "Periksa izin kamera Windows dan sambungan kamera."
                )

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-9)
            fps_smooth = fps_smooth * 0.9 + fps * 0.1
            prev_time = now
            frame, gestures = process_frame(
                frame, hand_landmarker, mp_image, SHOW_FINGER_STATES
            )
            announcer.update(gestures)
            draw_header(frame)
            draw_fps(frame, fps_smooth)
            if not gestures:
                h, w = frame.shape[:2]
                cv2.putText(frame, "Arahkan tangan ke kamera...",
                            (max(10, w // 2 - 180), h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)
            cv2.putText(frame, "[Q] Keluar  [F] Status jari  [S] Screenshot",
                        (10, frame.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX,
                        0.48, (180, 180, 180), 1)
            last_frame = frame.copy()
            cv2.imshow("Deteksi Gerakan Tangan - Webcam PC", frame)

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
    except KeyboardInterrupt:
        print("[INFO] Program dihentikan pengguna.")
    finally:
        camera.release()
        hand_landmarker.close()
        if speaker is not None:
            speaker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        run_detection()
    except KeyboardInterrupt:
        print("\n[INFO] Program dihentikan.")
    except RuntimeError as error:
        print(f"[ERROR] {error}")
