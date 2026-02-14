from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Any
import pandas as pd
import numpy as np

from scripts._hero_common import now_ts

Op = Literal["<=", ">="]

@dataclass(frozen=True)
class Rule:
    feature: str
    op: Op
    thr: float
    feature2: str | None = None
    op2: Op | None = None
    thr2: float | None = None

    def name(self) -> str:
        if self.feature2 is None:
            return f"{self.feature}{self.op}{self.thr:.6g}"
        return f"{self.feature}{self.op}{self.thr:.6g} & {self.feature2}{self.op2}{self.thr2:.6g}"

def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def apply_rule(df: pd.DataFrame, r: Rule) -> pd.Series:
    x = pd.to_numeric(df[r.feature], errors="coerce")
    m1 = (x <= r.thr) if r.op == "<=" else (x >= r.thr)

    if r.feature2 is None:
        return m1.fillna(False)

    x2 = pd.to_numeric(df[r.feature2], errors="coerce")
    m2 = (x2 <= float(r.thr2)) if r.op2 == "<=" else (x2 >= float(r.thr2))
    return (m1 & m2).fillna(False)

def eval_rule(df: pd.DataFrame, r: Rule, min_spd: int, max_spd: int) -> dict[str, Any]:
    mask = apply_rule(df, r)
    d = df.loc[mask, ["date", "hero", "fwd_ret_H"]].copy()
    if d.empty:
        return {"rule": r.name(), "signals": 0, "days": 0, "signals_per_day": 0.0,
                "avg_fwd_ret": float("nan"), "precision_hero": float("nan"), "objective": float("nan")}
    signals = len(d)
    by_day = d.groupby("date").size()
    spd = float(by_day.mean())
    if spd < min_spd or spd > max_spd:
        return {"rule": r.name(), "signals": signals, "days": int(by_day.shape[0]), "signals_per_day": spd,
                "avg_fwd_ret": float("nan"), "precision_hero": float("nan"), "objective": float("nan")}

    avg_ret = float(pd.to_numeric(d["fwd_ret_H"], errors="coerce").mean())
    prec = float(pd.to_numeric(d["hero"], errors="coerce").mean())
    return {"rule": r.name(), "signals": signals, "days": int(by_day.shape[0]), "signals_per_day": spd,
            "avg_fwd_ret": avg_ret, "precision_hero": prec, "objective": avg_ret}

def quantile_thresholds(s: pd.Series, grid: int) -> list[float]:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return []
    qs = np.linspace(0.02, 0.98, grid)
    thrs = list(np.unique(np.quantile(x.values, qs)))
    return [float(t) for t in thrs]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project_root", default=".")
    p.add_argument("--config", default="config/rule_search.json")
    p.add_argument("--labels", default=None)
    p.add_argument("--features", default=None)
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    cfg = load_config(project_root / args.config)

    labels_path = project_root / (args.labels or cfg.get("labels_path"))
    features_path = project_root / (args.features or cfg.get("features_path"))

    df_feat = pd.read_csv(features_path, dtype={"date": "string", "symbol": "string"})
    df_lab = pd.read_csv(labels_path, dtype={"date": "string", "symbol": "string"})

    df = df_feat.merge(df_lab[["date", "symbol", "hero", "fwd_ret_H"]], on=["date", "symbol"], how="inner")
    if df.empty:
        raise SystemExit("[FAIL] merge(features, labels) empty. Check paths and alignment.")

    numeric_cols = [c for c in df_feat.columns if c not in ("date", "symbol", "open", "high", "low", "close", "volume")]
    top_features = int(cfg.get("top_features", 12))
    def _prio(c: str) -> int:
        c2 = c.lower()
        if "rsi" in c2: return 0
        if "ret_" in c2: return 1
        if "zclose" in c2 or c2.startswith("z"): return 2
        if "vol_ratio" in c2: return 3
        return 9
    numeric_cols.sort(key=_prio)
    feats = numeric_cols[:top_features]

    grid = int(cfg.get("threshold_grid", 40))
    max_rules = int(cfg.get("max_rules", 200))
    min_spd = int(cfg.get("min_signals_per_day", 3))
    max_spd = int(cfg.get("max_signals_per_day", 25))
    allow_2 = bool(cfg.get("allow_two_condition", True))
    max_2 = int(cfg.get("max_two_condition_rules", 150))
    from_top = int(cfg.get("two_condition_from_top_n_1cond", 50))

    candidates_1: list[Rule] = []
    for f in feats:
        thrs = quantile_thresholds(df[f], grid)
        for t in thrs:
            candidates_1.append(Rule(feature=f, op="<=", thr=t))
            candidates_1.append(Rule(feature=f, op=">=", thr=t))

    scored_1 = [eval_rule(df, r, min_spd=min_spd, max_spd=max_spd) for r in candidates_1]
    df1 = pd.DataFrame(scored_1).dropna(subset=["objective"])
    df1 = df1.sort_values("objective", ascending=False).head(max_rules).reset_index(drop=True)

    df2 = pd.DataFrame()
    if allow_2 and not df1.empty:
        top1 = df1.head(from_top)["rule"].tolist()

        def parse_rule(s: str) -> Rule | None:
            s = s.strip()
            if "<=" in s:
                f, t = s.split("<=", 1)
                return Rule(feature=f.strip(), op="<=", thr=float(t))
            if ">=" in s:
                f, t = s.split(">=", 1)
                return Rule(feature=f.strip(), op=">=", thr=float(t))
            return None

        rules1 = [parse_rule(s) for s in top1]
        rules1 = [r for r in rules1 if r is not None]

        cand2: list[Rule] = []
        for i in range(len(rules1)):
            for j in range(i + 1, len(rules1)):
                a, b = rules1[i], rules1[j]
                if a.feature == b.feature:
                    continue
                cand2.append(Rule(feature=a.feature, op=a.op, thr=a.thr,
                                  feature2=b.feature, op2=b.op, thr2=b.thr))
                if len(cand2) >= max_2 * 5:
                    break
            if len(cand2) >= max_2 * 5:
                break

        scored_2 = [eval_rule(df, r, min_spd=min_spd, max_spd=max_spd) for r in cand2]
        df2 = pd.DataFrame(scored_2).dropna(subset=["objective"])
        df2 = df2.sort_values("objective", ascending=False).head(max_2).reset_index(drop=True)

    out = pd.concat([df1.assign(rule_type="1cond"), df2.assign(rule_type="2cond")], ignore_index=True)
    out = out.sort_values("objective", ascending=False).reset_index(drop=True)

    ts = now_ts()
    out_path = project_root / "results" / "rules" / f"hero_rules_candidates_{Path(labels_path).stem}_{ts}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"[OK] rules written: {out_path}")
    print(out.head(20).to_string(index=False))

if __name__ == "__main__":
    main()
