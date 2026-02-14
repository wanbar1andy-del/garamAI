"""
Runtime 32-bit Enforcement Module

SSOT for all 32-bit Python path resolution and enforcement.
Prevents 64-bit Python from executing Kiwoom-related operations.
"""
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path


def python32() -> str:
    """
    Return validated 32-bit Python path.
    
    Raises:
        SystemExit: If python32 not found or is not actually 32-bit
    
    Returns:
        Absolute path to verified 32-bit Python executable
    """
    p = os.environ.get("GARAM_PYTHON32", r"C:\Python39-32\python.exe")
    
    # Verify existence
    if not Path(p).exists():
        raise SystemExit(
            f"[CRITICAL] python32 not found: {p}\n"
            f"Set GARAM_PYTHON32 environment variable to valid 32-bit Python path"
        )
    
    # Verify it is truly 32-bit (not just named that way)
    try:
        r = subprocess.run(
            [p, "-c", "import sys; print('32' if sys.maxsize <= 2**32 else '64')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if r.returncode != 0:
            raise SystemExit(
                f"[CRITICAL] python32 failed to execute: {p}\n"
                f"stderr: {r.stderr}"
            )
        
        if "32" not in (r.stdout or ""):
            raise SystemExit(
                f"[CRITICAL] python32 is NOT 32-bit: {p}\n"
                f"Detected: {r.stdout.strip()}-bit\n"
                f"This will cause Kiwoom API failures!"
            )
            
    except subprocess.TimeoutExpired:
        raise SystemExit(f"[CRITICAL] python32 verification timeout: {p}")
    except Exception as e:
        raise SystemExit(f"[CRITICAL] python32 verification error: {e}")
    
    return p


def ensure_32bit_or_reexec() -> None:
    """
    Ensure current process is 32-bit, or re-exec with python32.
    
    This MUST be called at the very top of entry point scripts.
    If the current Python is 64-bit, this function will NOT return -
    it will replace the current process with a 32-bit one.
    """
    # Already 32-bit? Good to go
    if sys.maxsize <= 2**32:
        return
    
    # We are 64-bit. Must re-exec.
    print(f"[REEXEC] Detected 64-bit Python. Re-executing with 32-bit...")
    print(f"[REEXEC] Current: {sys.executable}")
    
    p32 = python32()  # Will exit if invalid
    print(f"[REEXEC] Target: {p32}")
    
    # Re-exec: Replace current process entirely
    # os.execv does NOT return - it replaces the process
    try:
        os.execv(p32, [p32] + sys.argv)
    except Exception as e:
        raise SystemExit(f"[CRITICAL] Re-exec failed: {e}")


def validate_runtime() -> None:
    """
    Full runtime validation (call once at startup for comprehensive check).
    
    Verifies:
    - Current process is 32-bit
    - python32() path is valid and 32-bit
    """
    # Validate we are 32-bit
    if sys.maxsize > 2**32:
        raise SystemExit(
            "[CRITICAL] Runtime validation failed: Current process is 64-bit!\n"
            "This should never happen if ensure_32bit_or_reexec() was called."
        )
    
    # Validate python32() helper
    p32 = python32()
    
    print(f"[✓] Runtime Validation Passed")
    print(f"    Current Python: {sys.executable}")
    print(f"    Verified 32-bit: {sys.maxsize <= 2**32}")
    print(f"    python32() path: {p32}")
