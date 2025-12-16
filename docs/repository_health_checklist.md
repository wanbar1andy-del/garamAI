# GARAM Phase 3/4 Common Health Checklist & Error Classification v1

## 1. Code / Repository Structure Errors

### 1-1. Duplicate Functions, Copy-Paste, Merge Artifacts

**Pattern:**

- Same function/endpoint repeated at the bottom of the file (e.g., `server_fixed.py` case).
- Two versions of the same function with slight differences.
- Markdown artifacts (e.g., ` ```python `) mixed in code.

**Risk:**

- Python uses the last definition, potentially ignoring fixes in the upper version.
- Flask routing conflicts, circular imports.

**Prevention & Check:**

- **Tooling:** Run `scripts/repo_health_scan.py` after major edits.
- **Manual:** Search for function definitions (`def func_name`) to ensure uniqueness.
- **Git:** Review `git diff` carefully for large block additions.

### 1-2. Invalid Strings / Encoding / Escape Warnings

**Pattern:**

- `SyntaxWarning: invalid escape sequence '\g'` in Windows paths (e.g., `"C:\garam..."`).

**Prevention & Check:**

- Use raw strings: `r"C:\garam..."`.
- Use `os.path.join` or `pathlib.Path`.

---

## 2. Server & API Routing Errors

**Patterns:**

- URL path typos (`/health/latest` vs `/health_last`).
- Missing Blueprint registration in `server.py`.
- Running the wrong server file (`server.py` vs `server_fixed.py`).
- **GARAM Specific:** HealthCollector running but API returning stale/dummy data.

**Prevention & Check:**

- **Route Definition:** Check `ui/api/*.py` and `api/server_fixed.py`.
- **Registration:** Verify `app.register_blueprint(...)`.
- **Execution:** Verify `start_garam.bat` targets the correct python file.
- **Restart Check:**

  ```powershell
  Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
  .\start_garam.bat
  curl http://localhost:5003/api/system/health/latest | ConvertFrom-Json
  ```

  Expect `status: OK`.

---

## 3. File/Path & Data Flow Errors

**Patterns:**

- Missing directories (`C:\garam\logs`, `GARAM_Data\system`).
- Relative path issues (FileNotFoundError).
- Scheduler running with different CWD than manual execution.

**Key Files:**

- `C:\garam\logs\health_service.log`
- `C:\garam\garam\GARAM_Data\system\health_YYYYMMDD.json`
- `C:\garam\garam\GARAM_Data\kiwoom_ready.flag`

**Prevention & Check:**

- Ensure code auto-creates directories.
- Use absolute paths derived from `Path(__file__).resolve()`.
- Verify file creation: `dir C:\garam\garam\GARAM_Data\system`.

---

## 4. Task Scheduler & Batch Job Errors

**Patterns:**

- "Start in" not set -> relative paths break.
- Wrong Python executable (32-bit vs 64-bit).
- Quote/Redirection escaping issues in command line.
- Log directory missing.

**GARAM Config:**

- **Task:** `GARAM_HealthCollector`
- **Command:** `cmd /c "C:\Python313\python.exe C:\garam\garam\health_service.py --once >> C:\garam\logs\health_service.log 2>&1"`

**Check:**

- `schtasks /query /tn "GARAM_HealthCollector" /fo LIST /v` (Check Last Run Result: 0x0).
- Check log content: `Get-Content C:\garam\logs\health_service.log -Tail 20`.

---

## 5. Frontend / Dashboard Errors

**Patterns:**

- Fetch URL mismatch between JS and Backend.
- JSON schema changes breaking UI.
- No error handling (blank screen).

**Prevention & Check:**

- **Contract:** Document API response fields.
- **JS Wrapper:** Use a common fetch wrapper with error logging.
- **Verification:** Check Browser DevTools > Network tab. Verify 200 OK and JSON structure.

---

## 6. Environment / Dependency Errors

**Patterns:**

- Python version mismatch (3.13 vs 3.9-32bit).
- Missing packages.

**GARAM Environment:**

- **Kiwoom:** `C:\Python39-32\python.exe`
- **Main/Health:** `C:\Python313\python.exe`
- **Dashboard:** `python` (Check version)

**Check:**

- `python -V` for each executable.

---

## 7. GARAM Phase 3/4 Health Checklist v1

### Code / Repo

- [ ] `scripts/repo_health_scan.py` runs with no critical errors.
- [ ] No duplicate functions in `server_fixed.py` / `ui/api/*.py`.
- [ ] `python -m py_compile ...` passes.

### Server / API

- [ ] No duplicate python processes.
- [ ] Server starts via `start_garam.bat`.
- [ ] `curl http://localhost:5003/api/system/health/latest` returns `status: OK` (not "no_checks_run").
- [ ] `curl http://localhost:5003/api/ai/summary` returns `context_loaded: True`.
- [ ] `curl http://localhost:5003/api/strategy/daily_plan` returns data.

### File / Path

- [ ] `C:\garam\logs` exists.
- [ ] `GARAM_Data\system` exists and has recent `health_*.json`.
- [ ] `kiwoom_ready.flag` exists (during operation).

### Task Scheduler

- [ ] `GARAM_HealthCollector` Last Run Result is 0x0.
- [ ] `health_service.log` is updating.

### Dashboard

- [ ] `http://localhost:5003` accessible.
- [ ] AI Control Center shows Status + Summary.
- [ ] Strategy/Simulation tabs show data or explicit "NO_DATA".

### Environment

- [ ] Python versions verified.
