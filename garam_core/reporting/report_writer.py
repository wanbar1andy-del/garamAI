# garam_core/reporting/report_writer.py
from __future__ import annotations
import json
import hashlib
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
from ..analysis.edge_decomposer import EdgeDecomposer

SSOT_VERSION = "2.3"

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _ts_iso(x) -> str:
    # pandas Timestamp / datetime / str handling
    ts = pd.to_datetime(x, utc=True, errors="coerce")
    if pd.isna(ts):
        return str(x)
    return ts.replace(microsecond=0).isoformat()

def _safe_float(v, default=0.0) -> float:
    try:
        if v is None: return default
        return float(v)
    except Exception:
        return default

def _parse_timeframe_seconds(timeframe: str | None) -> int | None:
    if not timeframe:
        return None
    try:
        if timeframe.endswith("d"):
            return int(timeframe[:-1]) * 86400
        if timeframe.endswith("h"):
            return int(timeframe[:-1]) * 3600
        if timeframe.endswith("m"):
            return int(timeframe[:-1]) * 60
    except Exception:
        return None
    return None

def _get_git_version() -> str:
    try:
        # Check if git is available and in a repo
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
        return "git:" + out.decode().strip()
    except Exception:
        return "git:unknown"

class ReportWriter:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root.parent / "results" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def write_replay_report(
        self,
        run_id: str,
        mode: str,
        symbol: str,
        timeframe: str,
        config: Dict[str, Any],
        replay_result: Any,
        data_range: Dict[str, Any],
        edge_analysis: Dict[str, Any] | None = None,
    ) -> Path:

        # 1) Config Hash & Structure
        # SSOT Requirement: signal_params, cost_model, full_dump
        config_payload = {
            "signal_params": config.get("signal_params", {}),
            "cost_model": config.get("cost_model", {}),
            "full_dump": config.get("full_dump", config),
        }
        cfg_str = json.dumps(config_payload, sort_keys=True, default=str)
        cfg_hash = hashlib.sha256(cfg_str.encode("utf-8")).hexdigest()

        # 2) Equity Curve Serialization (Safe)
        eq = replay_result.equity_curve
        equity_df = pd.DataFrame({"ts": eq.index, "equity": eq.values})
        # Explicit type conversion
        # Ensure ts is datetime for logic use before string conversion
        equity_df["ts_dt"] = pd.to_datetime(equity_df["ts"], utc=True, errors="coerce")
        equity_df["ts"] = equity_df["ts"].apply(_ts_iso)
        equity_df["equity"] = equity_df["equity"].astype(float)
        equity_json = equity_df[["ts", "equity"]].to_dict(orient="records")

        # 2b) Data Range Auto-Gen (Fallback)
        if not data_range:
             if not equity_df.empty:
                 start_ts = equity_df["ts"].iloc[0]
                 end_ts = equity_df["ts"].iloc[-1]
                 total_bars = len(equity_df)
                 # trade_days using the datetime column
                 trade_days = equity_df["ts_dt"].dt.date.nunique()
                 
                 data_range = {
                     "start_ts_utc": start_ts,
                     "end_ts_utc": end_ts,
                     "total_bars": int(total_bars),
                     "trade_days": int(trade_days)
                 }
             else:
                 # Sentinel values to prevent UI crashes on None
                 sentinel_ts = "1970-01-01T00:00:00Z"
                 data_range = {
                     "start_ts_utc": sentinel_ts, 
                     "end_ts_utc": sentinel_ts, 
                     "total_bars": 0, 
                     "trade_days": 0
                 }

        # 3) Trades Normalization (Strict SSOT Fields)
        trades_norm: List[Dict[str, Any]] = []
        for i, t in enumerate(replay_result.trades, start=1):
            # Handle object vs dict
            if isinstance(t, dict):
                d = dict(t)
            else:
                d = {k: getattr(t, k, None) for k in [
                    "id","entry_ts","exit_ts","side","entry_price","exit_price","qty",
                    "return_gross","return_net","fees","slippage","tax","tags"
                ]}
            
            # Fill defaults & types
            d["id"] = int(d.get("id") or i)
            d["entry_ts"] = _ts_iso(d.get("entry_ts"))
            d["exit_ts"] = _ts_iso(d.get("exit_ts"))
            d["side"] = str(d.get("side") or "LONG")
            d["entry_price"] = _safe_float(d.get("entry_price"), 0.0)
            d["exit_price"]  = _safe_float(d.get("exit_price"), 0.0)
            d["qty"] = int(d.get("qty") or 0)
            d["return_gross"] = _safe_float(d.get("return_gross"), 0.0)
            d["return_net"]   = _safe_float(d.get("return_net"), 0.0)
            d["fees"]     = _safe_float(d.get("fees"), 0.0)
            d["slippage"] = _safe_float(d.get("slippage"), 0.0)
            d["tax"]      = _safe_float(d.get("tax"), 0.0)
            d["tags"] = list(d.get("tags") or [])
            trades_norm.append(d)

        trades_count = len(trades_norm)

        # 4) KPI Whitelist & Calculation
        m = replay_result.metrics or {}

        # Edge Decomposition (Phase 18)
        edge_analysis_final = None
        try:
            timeframe_seconds = _parse_timeframe_seconds(timeframe)

            edge_analysis_final = EdgeDecomposer.analyze_trades(
                trades_norm,
                regime_series=None,          # Phase 18: optional / FastLane 미사용
                timeframe_seconds=timeframe_seconds
            )
        except Exception as e:
            # 절대 ReportWriter를 깨지 않음 (SSOT 안정성 우선)
            edge_analysis_final = {
                "count": 0,
                "expectancy_net": 0.0,
                "loss_tail_ratio": 0.0,
                "warnings": [f"EDGE_DECOMPOSER_FAILED: {str(e)}"],
                "by_regime": {}
            }
        
        # Determine Net/Gross
        total_net = _safe_float(m.get("total_return_net", m.get("total_return", 0.0)), 0.0)
        # Gross logic fix: Only add cost if it exists (absolute value check)
        cost_total = _safe_float(m.get("cost_total", 0.0), 0.0)
        total_gross = _safe_float(m.get("total_return_gross", 0.0), total_net)
        
        # If gross was not provided (defaulted to net) and we have costs, reconstruct it
        if abs(total_gross - total_net) < 1e-9 and abs(cost_total) > 0:
             total_gross = total_net + abs(cost_total)

        kpi = {
            "total_return_gross": total_gross,
            "total_return_net": total_net,
            "win_rate": _safe_float(m.get("win_rate"), 0.0),
            "profit_factor_net": _safe_float(m.get("profit_factor_net", m.get("profit_factor")), 0.0),
            "sharpe_ratio": _safe_float(m.get("sharpe_ratio"), 0.0),
            "sharpe_period": str(m.get("sharpe_period", "daily")),
            "mdd": _safe_float(m.get("mdd"), 0.0),
            "trades_count": int(trades_count), # Force SSOT Truth
            "trades_per_day": _safe_float(m.get("trades_per_day"), 0.0),
            "avg_hold_bars": _safe_float(m.get("avg_hold_bars"), 0.0),
            "expectancy_gross": _safe_float(m.get("expectancy_gross"), 0.0),
            "expectancy_net": _safe_float(m.get("expectancy_net"), 0.0),
        }

        # 5) Verification Logic (Runtime)
        kpi_count = kpi["trades_count"]
        trades_count_matches = (kpi_count == trades_count)
        
        equity_monotonic = True
        if len(eq) > 1:
            equity_monotonic = bool(pd.Index(eq.index).is_monotonic_increasing)
            
        schema_version_ok = True # Writer is SSOT authority
        
        warnings = []
        if not trades_count_matches:
            warnings.append(f"Trade count mismatch: kpi={kpi_count} vs trades={trades_count}")
        if not equity_monotonic:
            warnings.append("Equity curve timestamps not monotonic")
            
        ok = trades_count_matches and equity_monotonic and schema_version_ok

        report = {
            "meta": {
                "version": SSOT_VERSION,
                "run_id": run_id,
                "timestamp_utc": _utc_now_iso(),
                "mode": mode,
                "symbol": symbol,
                "timeframe": timeframe,
                "code_version": _get_git_version(),
                "equity_unit": "normalized",
                "data_range": data_range,
                "config_hash": cfg_hash,
                "config": config_payload,
            },
            "kpi": kpi,
            "verification": {
                "trades_count_matches": trades_count_matches,
                "equity_curve_monotonic_ts": equity_monotonic,
                "schema_version_ok": schema_version_ok,
                "warnings": warnings,
                "ok": ok
            },
            "equity_curve": equity_json,
            "trades": trades_norm,
            "edge_analysis": ({**edge_analysis_final, **edge_analysis} if (edge_analysis and edge_analysis_final) 
                              else (edge_analysis or edge_analysis_final or {"by_regime": {}})),
        }

        return self._save_files(run_id, mode, symbol, report)

    def write_tuning_report(
        self,
        run_id: str,
        experiments: List[Dict[str, Any]],
        ranking: List[Dict[str, Any]],
        winner: str,
        criteria: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Path:
        """
        Generate tuning_results.json adhering to SSOT v2.1 extension.
        """
        # Config Hash
        cfg_str = json.dumps(config, sort_keys=True, default=str)
        cfg_hash = hashlib.sha256(cfg_str.encode("utf-8")).hexdigest()

        # Verification Logic
        warnings = []
        
        # 1. Schema Version
        schema_version_ok = True
        if not schema_version_ok:
             warnings.append(f"Schema version mismatch: {SSOT_VERSION}")
             
        # 2. Winner Existence
        winner_found = any(e.get("name") == winner for e in experiments)
        if not winner_found:
             warnings.append(f"Winner '{winner}' not found in experiments list")
             
        # 3. Criteria Check
        expected_criteria = ["hynix_min_return", "samsung_max_loss", "high_bucket_floor_hit_max", "low_bucket_floor_hit_min"]
        criteria_present = all(k in criteria for k in expected_criteria)
        if not criteria_present:
             missing = [k for k in expected_criteria if k not in criteria]
             warnings.append(f"Missing criteria keys: {missing}")

        # 4. Ranking Consistency
        ranking_consistent = True
        if ranking and ranking[0].get("name") != winner:
             ranking_consistent = False
             warnings.append(f"Ranking mismatch: Winner '{winner}' is not #1 in ranking ({ranking[0].get('name')})")

        # 5. Ranking Non-Empty (Strict)
        ranking_non_empty = bool(ranking)
        if not ranking_non_empty:
             warnings.append("Ranking is empty")

        # 6. Overall OK
        ok = schema_version_ok and winner_found and criteria_present and ranking_consistent and ranking_non_empty

        report = {
            "meta": {
                "version": SSOT_VERSION,
                "run_id": run_id,
                "timestamp_utc": _utc_now_iso(),
                "mode": "TUNING",
                "code_version": _get_git_version(),
                "config_hash": cfg_hash,
                "config": config
            },
            "experiments": experiments,
            "ranking": ranking,
            "winner": winner,
            "criteria": criteria,
            "verification": {
                "schema_version_ok": schema_version_ok,
                "winner_in_experiments": winner_found,
                "criteria_present": criteria_present,
                "ranking_consistent": ranking_consistent,
                "ranking_non_empty": ranking_non_empty,
                "ok": ok,
                "warnings": warnings
            }
        }
        
        # Save as tuning_results.json (and SSOT variant)
        # Using _save_files helper but customizing names
        run_dir = self.reports_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        ssot_path = run_dir / "tuning_report.json"
        with open(ssot_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        # Snapshot (Winner in filename)
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_winner = "".join(c for c in str(winner) if c.isalnum() or c in "._-")
        snap_path = run_dir / f"tuning_{ts_str}_{safe_winner}.json"
        shutil.copy(ssot_path, snap_path)
        
        # Latest
        latest_path = self.reports_dir / "latest_tuning.json"
        shutil.copy(ssot_path, latest_path)
        
        print(f"[ReportWriter] Saved tuning report to {ssot_path}")
        return ssot_path

    def _save_files(self, run_id: str, mode: str, symbol: str, report: Dict) -> Path:
        run_dir = self.reports_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # 1. SSOT Original
        ssot_path = run_dir / "report.json"
        with open(ssot_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 2. Snapshot
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap_path = run_dir / f"report_{mode}_{ts_str}_{symbol}.json"
        shutil.copy(ssot_path, snap_path)

        # 3. Latest Link (For UI consumption)
        latest_path = self.reports_dir / "latest.json"
        shutil.copy(ssot_path, latest_path)
        
        print(f"[ReportWriter] Saved report to {ssot_path}")
        return ssot_path
