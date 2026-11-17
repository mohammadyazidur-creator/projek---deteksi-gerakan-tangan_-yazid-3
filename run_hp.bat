@echo off
cd /d "%~dp0"
echo Memulai Web Server untuk Akses dari HP...
.\venv\Scripts\python.exe server_hp.py
pause
