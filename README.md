# 🤚 Proyek Membaca Gerakan Tangan

Deteksi gestur tangan secara **real-time** menggunakan webcam dengan **MediaPipe Hands** + **OpenCV**.

---

## 📁 Struktur Proyek

```
projek_membaca_gerakan/
├── venv/                  # Virtual environment (sudah terinstall)
├── main.py                # Program utama
├── gesture_classifier.py  # Logika klasifikasi gestur
├── utils.py               # Helper functions
├── screenshots/           # Screenshot tersimpan (auto-dibuat)
└── README.md              # Dokumentasi ini
```

---

## ▶️ Cara Menjalankan

### Langkah 1 — Buka PowerShell

Tekan `Win + R`, ketik `powershell`, lalu tekan **Enter**.

---

### Langkah 2 — Masuk ke folder proyek

```powershell
cd c:\projek_membaca_gerakan
```

---

### Langkah 3 — Jalankan program

```powershell
.\venv\Scripts\python.exe main.py
```

> ✅ Tidak perlu install Python atau aktifkan venv secara manual.
> Python sudah tersedia di dalam folder `venv`.

---

### ✅ Contoh tampilan terminal yang benar

```
PS C:\projek_membaca_gerakan> .\venv\Scripts\python.exe main.py
==================================================
  Proyek Membaca Gerakan Tangan
  Menggunakan MediaPipe + OpenCV
==================================================
  Kamera: 0
  Max tangan: 2
  Confidence deteksi: 0.7

  Kontrol:
    Q  = Keluar
    F  = Toggle tampilan status jari
    S  = Screenshot

  Memulai kamera...

[INFO] Kamera berhasil dibuka. Tekan Q untuk keluar.
```

Setelah itu **jendela kamera akan muncul otomatis**. Arahkan tangan ke webcam!

---

## ⌨️ Kontrol Keyboard

| Tombol | Fungsi |
|--------|--------|
| `Q` atau `Esc` | Keluar dari program |
| `F` | Tampilkan / sembunyikan status jari |
| `S` | Simpan screenshot ke folder `screenshots/` |

---

## 🤟 Gestur yang Didukung

| Gestur | Simbol | Deskripsi |
|--------|--------|-----------|
| Open Hand | ✋ | Semua jari terbuka |
| Closed Fist | ✊ | Semua jari tertutup |
| Thumbs Up | 👍 | Hanya ibu jari terbuka |
| Peace / Victory | ✌ | Telunjuk & jari tengah terbuka |
| Rock | 🤘 | Telunjuk & kelingking terbuka |
| OK | 👌 | Ibu jari + 3 jari terbuka |
| Pointing | ☞ | Hanya telunjuk terbuka |
| Call Me | 🤙 | Ibu jari & kelingking terbuka |
| Three | — | Telunjuk, tengah & manis terbuka |
| Four | — | Empat jari terbuka (kecuali ibu jari) |

---

## 🛠️ Troubleshooting

### ❌ Error: "running scripts is disabled"

```
.\venv\Scripts\activate : File cannot be loaded because running scripts is disabled
```

**Solusi:** Jalankan perintah berikut di PowerShell (cukup sekali):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Ketik `Y` lalu Enter. Setelah itu ulangi langkah menjalankan program.

---

### ❌ Error: "Python was not found"

```
Python was not found; run without arguments to install from the Microsoft Store
```

**Solusi:** Gunakan Python dari dalam venv secara langsung:

```powershell
.\venv\Scripts\python.exe main.py
```

Jangan gunakan `python main.py` saja — gunakan path lengkapnya.

---

### ❌ Kamera tidak terbuka

```
[ERROR] Tidak bisa membuka kamera index 0.
```

**Solusi:** Buka file `main.py` dan ubah baris ini:

```python
# Baris 32 di main.py
CAMERA_INDEX = 0   # Ganti ke 1, 2, dst. sampai kamera terbuka
```

---

### ❌ Jendela kamera muncul tapi lag / lambat

Kurangi resolusi kamera di `main.py`:

```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Ubah dari 1280
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Ubah dari 720
```

---

## ⚙️ Konfigurasi (di `main.py`)

| Variabel | Default | Keterangan |
|----------|---------|------------|
| `CAMERA_INDEX` | `0` | Indeks kamera (0 = webcam utama) |
| `DETECTION_CONF` | `0.7` | Min confidence deteksi tangan (0.0–1.0) |
| `TRACKING_CONF` | `0.6` | Min confidence tracking tangan (0.0–1.0) |
| `MAX_HANDS` | `2` | Maksimum tangan yang dideteksi |

---

## 📦 Teknologi

- **MediaPipe Hands** — Deteksi 21 landmark titik tangan
- **OpenCV** — Capture webcam & rendering tampilan
- **NumPy** — Pemrosesan data numerik
- **Python 3.x** (sudah tersedia di dalam `venv`)
