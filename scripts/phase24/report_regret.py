import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def _regime_label(mkt_r60: float) -> str:
    # SSOT: UP/DOWN threshold ±0.20% (raw 기준)
    if not np.isfinite(mkt_r60):
        return "NA"
    if mkt_r60 >= 0.002:
        return "UP"
    if mkt_r60 <= -0.002:
        return "DOWN"
    return "FLAT"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle_csv", required=True, help="Global Oracle for Top1 Benchmark")
    ap.add_argument("--tape_csv", required=True)
    ap.add_argument("--oracle_tape_csv", required=False, help="Dedicated Oracle for Tape Symbols (Guarantees match)")
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--horizon", type=int, default=60)
    ap.add_argument("--hero_thr", type=str, default="0.0,0.002", help="HeroExists 임계값들(net 기준, 콤마)")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    thr_list = [float(x.strip()) for x in args.hero_thr.split(",") if x.strip()]

    df_o = pd.read_csv(args.oracle_csv, dtype={"symbol": str})
    df_t = pd.read_csv(args.tape_csv, dtype={"symbol": str})
    
    df_ot = None
    if args.oracle_tape_csv:
        df_ot = pd.read_csv(args.oracle_tape_csv, dtype={"symbol": str})
        df_ot["ts"] = pd.to_datetime(df_ot["ts"])
        df_ot = df_ot[df_ot["horizon_min"] == args.horizon].copy()

    df_o["ts"] = pd.to_datetime(df_o["ts"])
    df_t["ts"] = pd.to_datetime(df_t["ts"])

    # 선택 horizon만 필터
    df_o = df_o[df_o["horizon_min"] == args.horizon].copy()

    # oracle (ts, symbol) -> net_ret
    # If oracle_tape_csv provides specific coverage, use it for policy matching
    # Global oracle is used for "market top1"
    
    m_global = df_o[["ts", "symbol", "net_ret"]].dropna().copy()
    m_tape = df_ot[["ts", "symbol", "net_ret"]].dropna().copy() if df_ot is not None else m_global.copy()

    # oracle top1 per ts (정확히 net_ret max from Global)
    oracle_top1 = df_o.groupby("ts")["net_ret"].max().rename("oracle_top1_net")

    # regime (mkt_raw_ret_60) per ts (oracle에 컬럼이 있으면 우선 사용)
    if "mkt_raw_ret_60" in df_o.columns:
        mkt_r60 = df_o.groupby("ts")["mkt_raw_ret_60"].first().rename("mkt_raw_ret_60")
    else:
        mkt_r60 = pd.Series(index=oracle_top1.index, data=np.nan, name="mkt_raw_ret_60")

    # policy candidates (rank 1~3)
    t3 = df_t[(df_t["rank"] >= 1) & (df_t["rank"] <= 3)].copy()
    
    # ts별로 후보가 있었는지
    policy_has = t3.groupby("ts").size().rename("policy_cand_cnt")
    
    # Join verification
    t3m = t3.merge(m_tape, on=["ts", "symbol"], how="left")
    
    # MATCH RATE CHECK
    total_t3 = len(t3m)
    match_count = t3m["net_ret"].notna().sum()
    match_rate = (match_count / total_t3 * 100.0) if total_t3 > 0 else 0.0
    
    print(f"[INFO] H={args.horizon} | T3 Rows: {total_t3} | Match: {match_count} ({match_rate:.2f}%)")
    if match_rate < 95.0 and total_t3 > 0:
        print(f"[WARN] Match rate {match_rate:.2f}% < 95%. Results may be biased 0.")

    # policy_best3: rank1~3 중 최대 net_ret
    policy_best3 = t3m.groupby("ts")["net_ret"].max().rename("policy_best3_net")

    # policy_top1: rank==1의 net_ret
    pol1 = df_t[df_t["rank"] == 1].copy()
    pol1m = pol1.merge(m_tape, on=["ts", "symbol"], how="left")
    policy_top1 = pol1m.set_index("ts")["net_ret"].rename("policy_top1_net")

    df = pd.concat([oracle_top1, policy_best3, policy_top1, policy_has, mkt_r60], axis=1).reset_index().rename(columns={"index": "ts"})

    # 정책 후보가 없으면(미진입) policy_best3_net=0 처리 (SSOT: “히어로 없음”과 “미진입”을 분리해 관찰 가능)
    df["policy_cand_cnt"] = df["policy_cand_cnt"].fillna(0).astype(int)
    df.loc[df["policy_cand_cnt"] == 0, "policy_best3_net"] = 0.0
    df.loc[df["policy_cand_cnt"] == 0, "policy_top1_net"] = 0.0

    # 데이터 이슈: 후보는 있는데 oracle net_ret 매칭이 전부 NaN이면 해당 ts는 제외(왜곡 금지)
    data_issue = (df["policy_cand_cnt"] > 0) & (~np.isfinite(df["policy_best3_net"]))
    df["data_issue"] = data_issue.astype(int)

    # 평가대상 ts: oracle_top1이 유효 & data_issue 아님
    df["oracle_top1_net"] = df["oracle_top1_net"].fillna(np.nan)
    eval_mask = np.isfinite(df["oracle_top1_net"]) & (df["data_issue"] == 0)
    df_eval = df.loc[eval_mask].copy()

    # 남은 NaN은 0으로 두지 않고 제거(정직한 평가)
    df_eval["policy_best3_net"] = df_eval["policy_best3_net"].fillna(np.nan)
    df_eval = df_eval[np.isfinite(df_eval["policy_best3_net"])].copy()

    df_eval["regret"] = df_eval["oracle_top1_net"] - df_eval["policy_best3_net"]
    df_eval["regime"] = df_eval["mkt_raw_ret_60"].apply(_regime_label)

    # ===== 요약 저장 =====
    summary = df_eval.agg({
        "oracle_top1_net": ["mean", "median"],
        "policy_best3_net": ["mean", "median"],
        "regret": ["mean", "median"]
    })
    summary.to_csv(out_dir / "regret_summary.csv", encoding="utf-8-sig")

    reg = df_eval.groupby("regime")[["oracle_top1_net", "policy_best3_net", "regret"]].mean()
    reg.to_csv(out_dir / "regret_by_regime.csv", encoding="utf-8-sig")

    # HeroExists / Capture metrics
    hero_rows = []
    for thr in thr_list:
        hero_exists = (df_eval["oracle_top1_net"] >= thr)
        hero_rate = float(hero_exists.mean()) if len(df_eval) else 0.0

        # capture: hero가 있을 때 policy_best3가 thr 이상인가
        if hero_exists.any():
            capture = (df_eval.loc[hero_exists, "policy_best3_net"] >= thr)
            capture_rate = float(capture.mean())
        else:
            capture_rate = np.nan

        hero_rows.append({
            "thr_net": thr,
            "hero_exists_rate": hero_rate,
            "capture_rate_given_hero": capture_rate,
            "n_eval_ts": int(len(df_eval)),
        })

    df_hero = pd.DataFrame(hero_rows)
    df_hero.to_csv(out_dir / "hero_metrics.csv", index=False, encoding="utf-8-sig")

    # ===== 그래프 =====
    df_eval = df_eval.sort_values("ts")

    # 1) cumulative oracle vs policy
    df_eval["cum_oracle"] = (1.0 + df_eval["oracle_top1_net"]).cumprod()
    df_eval["cum_policy"] = (1.0 + df_eval["policy_best3_net"]).cumprod()

    plt.figure()
    plt.plot(df_eval["ts"], df_eval["cum_oracle"])
    plt.plot(df_eval["ts"], df_eval["cum_policy"])
    plt.title(f"Cumulative: OracleTop1 vs PolicyBest3 (H={args.horizon}m)")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(out_dir / f"cum_oracle_vs_policy_H{args.horizon}.png")
    plt.close()

    # 2) regret distribution
    plt.figure()
    plt.hist(df_eval["regret"].values, bins=50)
    plt.title(f"Regret Distribution (OracleTop1 - PolicyBest3) H={args.horizon}m")
    plt.tight_layout()
    plt.savefig(out_dir / f"regret_hist_H{args.horizon}.png")
    plt.close()

    # 3) time series regret
    plt.figure()
    plt.plot(df_eval["ts"], df_eval["regret"].values)
    plt.title(f"Regret Time Series H={args.horizon}m")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(out_dir / f"regret_ts_H{args.horizon}.png")
    plt.close()

    # 4) hero/capture bar
    if not df_hero.empty:
        plt.figure()
        plt.bar(df_hero["thr_net"].astype(str), df_hero["hero_exists_rate"].values)
        plt.title(f"Hero Exists Rate by Threshold (H={args.horizon}m)")
        plt.tight_layout()
        plt.savefig(out_dir / f"hero_exists_bar_H{args.horizon}.png")
        plt.close()

        plt.figure()
        plt.bar(df_hero["thr_net"].astype(str), df_hero["capture_rate_given_hero"].values)
        plt.title(f"Capture Rate | Hero Exists (PolicyBest3) (H={args.horizon}m)")
        plt.tight_layout()
        plt.savefig(out_dir / f"capture_rate_bar_H{args.horizon}.png")
        plt.close()

    out_csv = out_dir / f"regret_ts_H{args.horizon}.csv"
    df_eval.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # 운영용 핵심 로그
    n_all = len(df)
    n_eval = len(df_eval)
    n_issue = int(df["data_issue"].sum())
    print(f"[OK] {out_dir}")
    print(f"[INFO] ts_total={n_all} ts_eval={n_eval} data_issue_ts={n_issue}")

if __name__ == "__main__":
    main()
