@echo off
echo Stopping Garam System...
taskkill /IM python.exe /F
taskkill /IM cmd.exe /F
echo All processes terminated.
pause
