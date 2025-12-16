@echo off
echo Installing Dependencies for 32-bit Python...
echo Path: C:\Python39-32\python.exe

C:\Python39-32\python.exe -m pip install --upgrade pip
C:\Python39-32\python.exe -m pip install pandas pyqt5 pywin32 requests

echo.
echo Installation Complete. Now try running run_ingest_32bit.bat again.
pause
