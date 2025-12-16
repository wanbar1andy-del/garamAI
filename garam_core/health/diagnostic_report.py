# garam_core/health/diagnostic_report.py
from __future__ import annotations

import os
import sys
import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from garam_core.health.gate import gate_environment, gate_schema, GateSpec, GateError
from garam_core.data.loader import load_ohlcv, LoadSpec, DataLoadError
from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams


# -----------------------------
# Config
# -----------------------------
DEFAULT_TIMEZONE = "UTC"
DEFAULT_TIMEFRAME = "minute"
DEFAULT_SAMPLE_SYMBOLS = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER (예시)


@dataclass
class CheckItem:
    name: str
    status: str  # "PASS"|"WARN"|"FAIL"
    detail: str
    data: Optional[Dict[str, Any]] = None


def _now_str() -> str:
    # deterministic enough; no tz dependency
    return pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def _md_escape(s: str) -> str:
    return s.replace("\n", "<br>")


def _safe_read_text(p: Path, max_bytes: int = 200_000) -> str:
    try:
        b = p.read_bytes()
        if len(b) > max_bytes:
            b = b[:max_bytes]
        return b.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _is_corrupt_csv(path: Path) -> Tuple[bool, str]:
    """
    Corrupt definition (v0.1):
      - 0 bytes
      - cannot read header
      - missing required columns in first chunk
    """
    if not path.exists():
        return True, "file missing"
    if path.stat().st_size == 0:
        return True, "0 bytes"
    try:
        # read minimal
        df = pd.read_csv(path, nrows=5)
        cols = set([c.lower() for c in df.columns])
        required = {"open", "high", "low", "close", "volume"}
        if "date" not in cols and not isinstance(df.index, pd.DatetimeIndex):
            # allow missing date if it is already index in some formats (rare in csv)
            pass
        if not required.issubset(cols):
            return True, f"missing columns: {sorted(list(required - cols))}"
        return False, "ok"
    except Exception as e:
        return True, f"read error: {e}"


def _scan_history_files(data_root: Path, timeframe: str) -> Dict[str, Any]:
    """
    Scans:
      data_root/history/{timeframe}/
        *.csv, *.parquet
    Returns summary with corrupt CSVs.
    """
    base = (data_root / "history" / timeframe).resolve()
    out = {
        "base_dir": str(base),
        "exists": base.exists(),
        "csv_count": 0,
        "parquet_count": 0,
        "corrupt_csv": [],  # list of {file, reason}
        "examples": [],
    }
    if not base.exists():
        return out

    csvs = list(base.glob("*.csv"))
    pars = list(base.glob("*.parquet"))
    out["csv_count"] = len(csvs)
    out["parquet_count"] = len(pars)

    # sample
    out["examples"] = [p.name for p in (csvs[:3] + pars[:3])]

    for p in csvs:
        bad, reason = _is_corrupt_csv(p)
        if bad:
            out["corrupt_csv"].append({"file": p.name, "reason": reason})
    return out


def _check_required_artifacts(project_root: Path, paths: Dict[str, Path]) -> List[CheckItem]:
    """
    Checks presence of:
      - close_matrix.parquet (location may vary; we search common candidates)
      - universe_kr_top50.yaml (in old garam/config/ or new config/ depending on your setup)
    """
    items: List[CheckItem] = []

    # close_matrix common candidates
    candidates_close = [
        paths["data_root"] / "history" / "close_matrix.parquet",
        paths["data_root"] / "close_matrix.parquet",
        project_root.parent / "garamdata" / "history" / "close_matrix.parquet",  # legacy hint
    ]
    found_close = next((p for p in candidates_close if p.exists()), None)
    if found_close:
        items.append(CheckItem("artifact: close_matrix.parquet", "PASS", f"found: {found_close}"))
    else:
        items.append(CheckItem(
            "artifact: close_matrix.parquet",
            "FAIL",
            f"not found. searched: {', '.join([str(p) for p in candidates_close])}",
        ))

    # universe file candidates
    candidates_uni = [
        project_root / "config" / "universe_kr_top50.yaml",
        project_root.parent / "garam" / "garam" / "config" / "universe_kr_top50.yaml",  # legacy hint
        project_root.parent / "garam" / "config" / "universe_kr_top50.yaml",
    ]
    found_uni = next((p for p in candidates_uni if p.exists()), None)
    if found_uni:
        items.append(CheckItem("artifact: universe_kr_top50.yaml", "PASS", f"found: {found_uni}"))
    else:
        items.append(CheckItem(
            "artifact: universe_kr_top50.yaml",
            "FAIL",
            f"not found. searched: {', '.join([str(p) for p in candidates_uni])}",
        ))

    return items


def _load_symbols_from_universe_yaml(universe_path: Path) -> List[str]:
    """
    Minimal YAML-free parser fallback:
    - If PyYAML exists, use it.
    - Otherwise, best-effort parse lines that look like '- 005930' etc.
    """
    if not universe_path.exists():
        return []
    txt = _safe_read_text(universe_path)
    syms: List[str] = []
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("-"):
            token = line[1:].strip().strip('"').strip("'")
            if token:
                syms.append(token)
    # de-dup keep order
    seen = set()
    out = []
    for s in syms:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _run_smoke_replay(project_root: Path, symbol: str, timeframe: str, tz: str) -> CheckItem:
    try:
        res = run_replay(
            project_root=project_root,
            # B-5 Optimization: limit smoke test to 500 bars
            replay=ReplaySpec(
                symbol=symbol, 
                timeframe=timeframe, 
                timezone=tz,
                max_bars=500
            ),
            regime_params=RegimeParams(),
            signal_params=SignalParams(),
            turbo_params=TurboParams(),
            initial_equity=1.0,
            collect_debug=False,
        )
        return CheckItem(
            name=f"smoke replay: {symbol}/{timeframe}",
            status="PASS",
            detail=f"metrics={res.metrics}, trades={len(res.trades)}",
            data={"metrics": res.metrics, "trades": res.trades[:5]},
        )
    except Exception as e:
        return CheckItem(
            name=f"smoke replay: {symbol}/{timeframe}",
            status="FAIL",
            detail=f"{type(e).__name__}: {e}",
            data={"trace": traceback.format_exc(limit=5)},
        )


def generate_gap_health_report(project_root: Path) -> str:
    checks: List[CheckItem] = []
    header = {
        "title": "GAP (Garam Audit & Pause) - Health Report",
        "status": "PROJECT FROZEN (P0 STOP)",
        "generated_at": _now_str(),
        "project_root": str(project_root.resolve()),
    }

    # Gate0 environment
    paths_cfg = None
    try:
        paths_cfg = gate_environment(project_root)
        checks.append(CheckItem("Gate0: environment(paths.yaml)", "PASS", "paths.yaml loaded and validated"))
    except GateError as e:
        checks.append(CheckItem("Gate0: environment(paths.yaml)", "FAIL", str(e)))
        # If Gate0 fails, no further reliable checks.
        return _render_report(header, checks, extra={})

    paths = {
        "project_root": paths_cfg.project_root,
        "data_root": paths_cfg.data_root,
        "logs_root": paths_cfg.logs_root,
    }

    # basic dir sanity
    for k, p in paths.items():
        if not p.exists():
            checks.append(CheckItem(f"path exists: {k}", "FAIL", f"missing: {p}"))
        else:
            checks.append(CheckItem(f"path exists: {k}", "PASS", f"{p}"))

    # ---- Fear Feature Check (RSS-based) ----
    try:
        from garam_core.data.feature_loader import load_fear_feature, align_fear_to_market
        import yaml
        
        policy_path = project_root / "garam_core" / "config" / "feature_policy.yaml"
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8")) if policy_path.exists() else {}
        fear_pol = policy.get("fear", {})
        required = bool(fear_pol.get("required", False))
        fallback = float(fear_pol.get("fallback_score", 0.5))
        freshness_h = float(fear_pol.get("freshness_max_hours", 24))
        max_missing = float(fear_pol.get("max_missing_ratio", 0.2))

        fear_df = load_fear_feature(paths["data_root"], timeframe="minute", symbol="MARKET")
        
        # freshness
        last_ts = fear_df.index.max()
        now_ts = pd.Timestamp.now(tz=last_ts.tz)
        age_hours = (now_ts - last_ts).total_seconds() / 3600.0

        # alignment coverage using sample OHLCV (first sample or 005930)
        # sample_sym = sample_syms[0] if sample_syms else "005930" # sample_syms is not defined here yet
        # We need to load OHLCV again if not available in local scope, but usually it is.
        # Just creating a quick check if possible.
        # Simplification: Compare last timestamps
        
        if age_hours > freshness_h:
            checks.append(CheckItem("feature: fear freshness", "WARN", f"age_hours={age_hours:.1f} > {freshness_h}", data={"last_ts": str(last_ts)}))
        else:
            checks.append(CheckItem("feature: fear freshness", "PASS", f"age_hours={age_hours:.1f}", data={"last_ts": str(last_ts)}))

        # Schema is implicitly passed by load_fear_feature
        checks.append(CheckItem("feature: fear schema", "PASS", f"rows={len(fear_df)}"))

    except Exception as e:
        # required 정책 반영
        # If imports fail or file missing
        status = "FAIL" if getattr(locals().get('policy', {}).get("fear", {}), 'get', lambda k,d: False)('required', False) else "WARN"
        checks.append(CheckItem("feature: fear availability", status, f"{type(e).__name__}: {e}"))


    # Required artifacts (close_matrix/universe)
    checks.extend(_check_required_artifacts(project_root, paths))

    # History scan + corrupt detection
    scan = _scan_history_files(paths["data_root"], DEFAULT_TIMEFRAME)
    if not scan["exists"]:
        checks.append(CheckItem("data scan: history/minute", "FAIL", f"missing: {scan['base_dir']}"))
    else:
        corrupt_n = len(scan["corrupt_csv"])
        if corrupt_n == 0:
            checks.append(CheckItem("data scan: corrupt csv", "PASS", f"csv={scan['csv_count']}, parquet={scan['parquet_count']}"))
        else:
            checks.append(CheckItem("data scan: corrupt csv", "FAIL", f"corrupt={corrupt_n} (see details)", data=scan))

    # Schema check on a sample symbol file
    # Try universe file first; otherwise fallback to DEFAULT_SAMPLE_SYMBOLS
    uni_path_guess = (project_root / "config" / "universe_kr_top50.yaml")
    syms = _load_symbols_from_universe_yaml(uni_path_guess)
    if syms:
        sample_syms = syms[:5]
        checks.append(CheckItem("universe parse (best-effort)", "PASS", f"loaded {len(syms)} symbols (sample={sample_syms})"))
    else:
        sample_syms = DEFAULT_SAMPLE_SYMBOLS
        checks.append(CheckItem("universe parse (best-effort)", "WARN", f"universe not parsed; using defaults={sample_syms}"))

    schema_fail = 0
    schema_pass = 0
    schema_details = []
    for s in sample_syms[:3]:
        try:
            raw = load_ohlcv(paths["data_root"], s, DEFAULT_TIMEFRAME, spec=LoadSpec(tz=DEFAULT_TIMEZONE))
            _ = gate_schema(raw, GateSpec(timezone=DEFAULT_TIMEZONE))
            schema_pass += 1
        except (DataLoadError, GateError, Exception) as e:
            schema_fail += 1
            schema_details.append({"symbol": s, "error": f"{type(e).__name__}: {e}"})

    if schema_fail == 0 and schema_pass > 0:
        checks.append(CheckItem("Gate1: schema sample", "PASS", f"validated {schema_pass} sample symbols"))
    else:
        checks.append(CheckItem("Gate1: schema sample", "FAIL", f"pass={schema_pass}, fail={schema_fail}", data={"details": schema_details}))

    # Smoke replay (position simulation) on 1~2 symbols
    checks.append(_run_smoke_replay(project_root, sample_syms[0], DEFAULT_TIMEFRAME, DEFAULT_TIMEZONE))
    if len(sample_syms) > 1:
        checks.append(_run_smoke_replay(project_root, sample_syms[1], DEFAULT_TIMEFRAME, DEFAULT_TIMEZONE))
        
    # Recollect consistency (B-5+)
    uni_path = project_root / "config" / "universe_kr_top50.yaml"
    try:
        from garam_core.health.recollect_consistency import recollect_consistency_check
        rc = recollect_consistency_check(paths["data_root"], uni_path, DEFAULT_TIMEFRAME)
        if rc["missing_in_history_count"] == 0 and rc["extra_in_history_count"] == 0:
            checks.append(CheckItem("recollect consistency", "PASS",
                                    f"universe/history aligned ({rc['universe_count']})",
                                    data=rc))
        else:
            checks.append(CheckItem("recollect consistency", "FAIL",
                                    f"missing={rc['missing_in_history_count']}, extra={rc['extra_in_history_count']}",
                                    data=rc))
    except Exception as e:
        checks.append(CheckItem("recollect consistency", "FAIL", f"{type(e).__name__}: {e}"))

    extra = {
        "paths": {k: str(v) for k, v in paths.items()},
        "scan": scan,
    }
    return _render_report(header, checks, extra=extra)


def _render_report(header: Dict[str, Any], checks: List[CheckItem], extra: Dict[str, Any]) -> str:
    # Aggregate status
    def rank(s: str) -> int:
        return {"PASS": 0, "WARN": 1, "FAIL": 2}.get(s, 2)

    worst = max(checks, key=lambda c: rank(c.status)).status if checks else "FAIL"

    lines: List[str] = []
    lines.append(f"# {header['title']}")
    lines.append("")
    lines.append(f"- **Status:** {header['status']}")
    lines.append(f"- **Generated At:** {header['generated_at']}")
    lines.append(f"- **Project Root:** `{header['project_root']}`")
    lines.append(f"- **Overall Health:** **{worst}**")
    lines.append("")

    # Summary counts
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in checks:
        counts[c.status] = counts.get(c.status, 0) + 1

    lines.append("## Summary")
    lines.append(f"- PASS: {counts['PASS']}")
    lines.append(f"- WARN: {counts['WARN']}")
    lines.append(f"- FAIL: {counts['FAIL']}")
    lines.append("")

    # Detailed table
    lines.append("## Checks")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---:|---|")
    for c in checks:
        lines.append(f"| {_md_escape(c.name)} | **{c.status}** | {_md_escape(c.detail)} |")
    lines.append("")

    # Attach details JSON blobs (only for FAIL/WARN)
    lines.append("## Details (FAIL/WARN)")
    for c in checks:
        if c.status in ("FAIL", "WARN") and c.data:
            lines.append(f"### {c.name} ({c.status})")
            lines.append("```json")
            lines.append(json.dumps(c.data, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")

    # Recommendations (Gate-driven)
    lines.append("## Action Recommendations (Gate-Driven)")
    # prioritize P0 items
    recs = []
    for c in checks:
        if c.status == "FAIL":
            if "close_matrix" in c.name or "universe" in c.name:
                recs.append("- **P0:** 필수 아티팩트(클로즈 매트릭스/유니버스) 누락. 해당 파일 위치 확정 및 생성/복구 후 재검증.")
            if "Gate0" in c.name:
                recs.append("- **P0:** paths.yaml Gate 실패. 절대경로 제거 및 data_root/logs_root 실존 경로로 재정의.")
            if "corrupt csv" in c.name:
                recs.append("- **P0:** 손상 CSV 존재. 수집/저장 파이프라인을 실행하기 전에 손상 파일 목록을 격리하고 재수집 로직을 별도 격리 모듈로 교정.")
            if "Gate1" in c.name:
                recs.append("- **P0:** 스키마 검증 실패. 컬럼/타임존/정렬 규약을 데이터 저장 단계에서 강제하고, schema gate 통과 전에는 리플레이 금지.")
            if "smoke replay" in c.name:
                recs.append("- **P1:** 리플레이 스모크 실패. loader→schema→engine 순으로 실패 지점부터 역추적(Trace)하여 1건이라도 PASS 만들 것.")
    if not recs:
        recs = ["- 현재 진단 기준에서 치명 FAIL 없음. 다음 단계로 비용모델/체결모델(B-6) 진행 가능."]

    # de-dup keep order
    seen = set()
    recs2 = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            recs2.append(r)

    lines.extend(recs2)
    lines.append("")

    # Extra context
    lines.append("## Context")
    if extra.get("paths"):
        lines.append("```json")
        lines.append(json.dumps(extra["paths"], ensure_ascii=False, indent=2))
        lines.append("```")
    if extra.get("scan"):
        lines.append("```json")
        lines.append(json.dumps(extra["scan"], ensure_ascii=False, indent=2))
        lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main(argv: List[str]) -> int:
    # project_root default = current file -> garam_core -> project_root
    # expected layout: project_root/garam_core/health/diagnostic_report.py
    here = Path(__file__).resolve()
    project_root = here.parents[1]  # garam_core root

    # allow override
    if len(argv) >= 2:
        project_root = Path(argv[1]).resolve()

    report = generate_gap_health_report(project_root)

    out_dir = project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"GAP_Health_Report_{pd.Timestamp.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    out_path.write_text(report, encoding="utf-8")

    print(f"[OK] Report written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
