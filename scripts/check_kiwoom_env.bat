@echo off
echo Checking Kiwoom Environment...
if exist "C:\Python39-32\python.exe" (
    echo [OK] 32-bit Python found at C:\Python39-32\python.exe
    "C:\Python39-32\python.exe" --version
    "C:\Python39-32\python.exe" -c "import struct; print('Bitness:', struct.calcsize('P')*8)"
) else (
    echo [FAIL] C:\Python39-32\python.exe NOT FOUND.
    echo Please install Python 3.9 32-bit to this path.
)
