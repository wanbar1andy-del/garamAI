from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Tuple


class HeroDiaryBuilder:
    """
    SSOT v1.2.0: Daily Decision Log (+ target_weight only)
    - Diary never re-reads price or minute data.
    - Truth source = hero_scan CSV fields:
        champion_score_norm (0~1), ref_price, veto, veto_reason, (optional) regime_ban
    - Implements user's 2/5/0 rule:
        Strong => 2 names (0.5/0.5)
        Weak   => up to 5 names (0.2 each)
        None   => rest (0 orders)
    """

    # SSOT v1.2.0 thresholds (normalized score)
    T_WEAK = 0.85
    T_STRONG = 0.93
    R_STRONG = 1.10
    D_STRONG = 0.03

    def __init__(self, project_root: Path):
        self.root = project_root
        self.results_dir = self.root / "results"
        self.diary_dir = self.results_dir / "diary"
        self.diary_dir.mkdir(parents=True, exist_ok=True)

    def _pick_score_column(self, df: pd.DataFrame) -> str:
        if "champion_score_norm" in df.columns:
            return "champion_score_norm"
        if "expectancy_net" in df.columns:
            return "expectancy_net"
        raise ValueError("[SSOT] scan file missing champion_score_norm and expectancy_net")

    def _ensure_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["symbol"] = out["symbol"].astype(str).str.zfill(6)

        for c, default in [
            ("veto", False),
            ("veto_reason", ""),
            ("regime_ban", False),
            ("ref_price", 0.0),
        ]:
            if c not in out.columns:
                out[c] = default

        out["veto"] = out["veto"].astype(bool)
        out["regime_ban"] = out["regime_ban"].astype(bool)
        out["veto_reason"] = out["veto_reason"].fillna("").astype(str)
        out["ref_price"] = pd.to_numeric(out["ref_price"], errors="coerce").fillna(0.0)

        # ref_price <= 0 is effectively veto (SSOT)
        out.loc[out["ref_price"] <= 0, "veto"] = True
        out.loc[out["ref_price"] <= 0, "veto_reason"] = out.loc[out["ref_price"] <= 0, "veto_reason"].where(
            out.loc[out["ref_price"] <= 0, "veto_reason"].str.len() > 0,
            "RefPrice<=0"
        )

        return out

    def _determine_k(self, scores: List[float]) -> Tuple[int, str]:
        """
        2/5/0 rule (normalized score 기준):
        - K=0: Top1 < T_WEAK OR empty
        - K=2: Top1,Top2 >= T_STRONG AND (ratio>=R_STRONG OR gap>=D_STRONG)
        - else: K=5 (weak/cluster)
        """
        if not scores:
            return 0, "K=0 (no eligible)"

        top1 = scores[0]
        if top1 < self.T_WEAK:
            return 0, f"K=0 (top1<{self.T_WEAK})"

        top2 = scores[1] if len(scores) >= 2 else None
        if top2 is not None and top1 >= self.T_STRONG and top2 >= self.T_STRONG:
            ratio = top1 / max(top2, 1e-12)
            gap = top1 - top2
            if (ratio >= self.R_STRONG) or (gap >= self.D_STRONG):
                return 2, f"K=2 (strong: top>= {self.T_STRONG}, ratio/gap pass)"

        return 5, "K=5 (weak/cluster)"

    def build_diary(self, scan_path: Path, current_holdings: List[str]) -> Path:
        if not scan_path.exists():
            raise FileNotFoundError(f"[SSOT] scan file not found: {scan_path}")

        df = pd.read_csv(scan_path)
        if "symbol" not in df.columns:
            raise ValueError("[SSOT] scan file missing required column: symbol")

        df = self._ensure_cols(df)
        score_col = self._pick_score_column(df)
        df[score_col] = pd.to_numeric(df[score_col], errors="coerce").fillna(0.0)

        # Operation date: prefer scan file date column, else today
        if "date" in df.columns and not df["date"].isnull().all():
            today_str = str(df["date"].iloc[0]).replace("-", "").replace("/", "")[:8]
        else:
            today_str = datetime.now().strftime("%Y%m%d")

        # Champion eligible rule (SSOT):
        # eligible = (score>=T_WEAK) & (~regime_ban) & (~veto)
        # NOTE: In fallback expectancy mode, still respect veto/regime_ban but score is expectancy_net.
        eligible = (df[score_col] >= self.T_WEAK) & (~df["regime_ban"]) & (~df["veto"])

        df_sorted = df.sort_values(score_col, ascending=False).reset_index(drop=True)
        eligible_df = df_sorted[eligible.loc[df_sorted.index]].copy()
        eligible_scores = eligible_df[score_col].astype(float).tolist()

        k, k_reason = self._determine_k(eligible_scores)

        selected = set()
        if k > 0:
            # Select up to K, but weight is fixed by regime (0.5 or 0.2), remaining cash allowed.
            take = min(k, len(eligible_df))
            selected = set(eligible_df.head(take)["symbol"].tolist())

        # Weight rule fixed
        if k == 2:
            w = 0.50
        elif k == 5:
            w = 0.20
        else:
            w = 0.00

        rows = []
        for rank, (_, r) in enumerate(df_sorted.iterrows(), start=1):
            sym = str(r["symbol"]).zfill(6)
            score = float(r.get(score_col, 0.0))
            veto = bool(r.get("veto", False))
            veto_reason = str(r.get("veto_reason", ""))
            regime_ban = bool(r.get("regime_ban", False))
            ref_price = float(r.get("ref_price", 0.0))

            decision = "DROP"
            reason = []

            if veto:
                reason.append(f"VETO({veto_reason})")
            if regime_ban:
                reason.append("RegimeBan")
            if score < self.T_WEAK:
                reason.append(f"GateFail(<{self.T_WEAK})")

            is_selected = sym in selected

            if sym in [h.zfill(6) for h in current_holdings]:
                if is_selected:
                    decision = "HOLD"
                    reason.append("Holding&Selected")
                else:
                    decision = "EXIT"
                    reason.append("HoldingNotSelected")
            else:
                if is_selected:
                    decision = "HERO"
                    reason.append(k_reason)
                else:
                    decision = "DROP"

            target_weight = w if is_selected and decision in ("HERO", "HOLD") else 0.0

            rows.append({
                "date": today_str,
                "symbol": sym,
                "score_col": score_col,
                "score": score,
                "champion_score_norm": float(r.get("champion_score_norm", 0.0)) if "champion_score_norm" in df_sorted.columns else None,
                "ref_price": ref_price,
                "veto": veto,
                "veto_reason": veto_reason,
                "regime_ban": regime_ban,
                "rank": rank,
                "decision": decision,
                "target_weight": target_weight,
                "reason": ";".join(reason),
            })

        out = pd.DataFrame(rows)

        # Output policy: top 20 + active(HERO/HOLD/EXIT)
        mask_active = out["decision"].isin(["HERO", "HOLD", "EXIT"])
        mask_top = out["rank"] <= 20
        final = out[mask_active | mask_top].drop_duplicates(subset=["symbol"]).copy()

        out_path = self.diary_dir / f"hero_diary_{today_str}.csv"
        final.to_csv(out_path, index=False)

        latest = self.diary_dir / "hero_diary_latest.csv"
        shutil.copy(out_path, latest)

        print(f"[DIARY] {out_path} rows={len(final)} | selected={len(selected)} | {k_reason} | weight={w}")
        return out_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    builder = HeroDiaryBuilder(root)

    scans = sorted((root / "results").glob("hero_scan_*.csv"), key=lambda p: p.stat().st_mtime)
    if not scans:
        raise SystemExit("No hero_scan_*.csv found in results/")

    builder.build_diary(scans[-1], current_holdings=[])
