@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   MeriCode C++ - Construccion del ejecutable para Windows
echo ============================================================
echo.

echo [1/2] Instalando/actualizando PyInstaller...
python -m pip install --upgrade pip pyinstaller

echo.
echo [2/2] Construyendo MeriCode.exe (un solo archivo, sin consola)...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name MeriCode main.py

echo.
echo ============================================================
echo   Listo. Ejecutable en:  dist\MeriCode.exe
echo ============================================================
echo.
echo Para crear el instalador, abre installer.iss con Inno Setup 6
echo y pulsa Compilar (generara dist\MeriCode-Setup.exe).
echo.
pause
