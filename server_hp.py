"""
Server untuk:
- Menyajikan web_mobile/index.html ke browser HP.
- Menerima frame kamera HP melalui WebSocket /ws/phone.
- Mengirim frame tersebut ke main.py melalui WebSocket /ws/pc.

Jalankan: .\venv\Scripts\python.exe server_hp.py
"""
import asyncio
import os
from aiohttp import web, WSMsgType

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web_mobile")

# Satu slot saja: frame terbaru menggantikan frame lama agar tidak menumpuk.
FRAME_QUEUE = None


async def index(request):
    return web.FileResponse(os.path.join(WEB_DIR, "index.html"))


async def phone_stream(request):
    ws = web.WebSocketResponse(max_msg_size=2 * 1024 * 1024, heartbeat=20)
    await ws.prepare(request)
    print("[INFO] HP terhubung sebagai kamera.")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.BINARY:
                # Buang frame lama jika PC belum sempat mengambilnya.
                if FRAME_QUEUE.full():
                    try:
                        FRAME_QUEUE.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await FRAME_QUEUE.put(msg.data)
            elif msg.type == WSMsgType.ERROR:
                print(f"[WARNING] WebSocket HP error: {ws.exception()}")
                break
    finally:
        print("[INFO] Koneksi kamera HP terputus.")
    return ws


async def pc_stream(request):
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)
    print("[INFO] Program Python terhubung untuk menerima video.")

    try:
        while not ws.closed:
            frame = await FRAME_QUEUE.get()
            await ws.send_bytes(frame)
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    finally:
        print("[INFO] Koneksi program Python ditutup.")
    return ws


async def on_startup(app):
    global FRAME_QUEUE
    FRAME_QUEUE = asyncio.Queue(maxsize=1)


def create_app():
    app = web.Application(client_max_size=2 * 1024 * 1024)
    app.on_startup.append(on_startup)
    app.router.add_get("/", index)
    app.router.add_get("/ws/phone", phone_stream)
    app.router.add_get("/ws/pc", pc_stream)
    return app


if __name__ == "__main__":
    if not os.path.isfile(os.path.join(WEB_DIR, "index.html")):
        raise FileNotFoundError(f"File tidak ditemukan: {WEB_DIR}\\index.html")

    print("=" * 58)
    print("  SERVER DETEKSI GERAKAN TANGAN - USB")
    print("=" * 58)
    print(f"  Browser HP : http://localhost:{PORT}")
    print(f"  WebSocket  : ws://localhost:{PORT}/ws/phone")
    print("  Pastikan ADB reverse sudah dijalankan:")
    print(f"  adb reverse tcp:{PORT} tcp:{PORT}")
    print("  Tekan Ctrl+C untuk menghentikan server.")
    print("=" * 58)
    web.run_app(create_app(), host="0.0.0.0", port=PORT)
