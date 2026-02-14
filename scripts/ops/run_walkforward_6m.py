import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import sys
import shutil

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.ops.run_replay_batch import run_replay_batch

def month_start(dt: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(dt.year, dt.month, 1)

def month_end(dt: pd.Timestamp) -> pd.Timestamp:
    nm = (pd.Timestamp(dt.year, dt.month, 1) + pd.offsets.MonthBegin(1))
    return (nm - pd.Timedelta(days=1))

def iter_last_full_months(end_month: str, n_months: int):
    end_dt = pd.to_datetime(end_month + "-01")
    months = []
    cur = end_dt
    for _ in range(n_months):
        s = month_start(cur)
        e = month_end(cur)
        months.append((s.strftime("%Y-%m"), s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")))
        cur = (s - pd.offsets.MonthBegin(1))
    return list(reversed(months))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--end_month", type=str, required=True, help="YYYY-MM (last month included, e.g. 2025-11)")
    ap.add_argument("--months", type=int, default=6)
    ap.add_argument("--init_capital", type=float, default=10_000_000.0)
    ap.add_argument("--tag", type=str, default="phase22_sealed_wf6m")

    # SEALED params (lock)
    ap.add_argument("--entry_roc", type=float, default=-0.02)
    ap.add_argument("--entry_vol", type=float, default=1.2)
    ap.add_argument("--exit_sl", type=float, default=-0.02)
    ap.add_argument("--exit_tp", type=float, default=0.03)
    ap.add_argument("--time_stop", type=int, default=40)
    ap.add_argument("--max_slots", type=int, default=3)
    ap.add_argument("--reversal", type=int, default=0)
    args = ap.parse_args()

    months = iter_last_full_months(args.end_month, args.months)

    equity = float(args.init_capital)
    all_rows = []

    out_base = project_root / "results" / "walkforward" / args.tag
    out_base.mkdir(parents=True, exist_ok=True)

    wf_months = []

    for ym, s, e in months:
        run_tag = f"{args.tag}_{ym}"
        out_root = str(out_base / ym)

        print(f"\n>>> Running WFA Month: {ym} ({s} ~ {e}) | StartEq: {equity:,.0f}")

        summary = run_replay_batch(
            days2run=9999,
            entry_roc=args.entry_roc,
            entry_vol=args.entry_vol,
            ma60_check=True,
            exit_sl=args.exit_sl,
            exit_tp=args.exit_tp,
            time_stop=args.time_stop,
            max_slots=args.max_slots,
            reversal_type=args.reversal,
            tag=run_tag,
            start_date=s,
            end_date=e,
            init_capital=equity,
            out_root=out_root,
            reset_out=True,   # Reset monthly folder
        )

        equity = summary["final_equity"]
        summary["month"] = ym
        all_rows.append(summary)
        wf_months.append(ym)

    df = pd.DataFrame(all_rows)

    # Monthly report CSV
    csv_path = out_base / "wf_monthly.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    plots_dir = out_base / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # 1) Aggregate daily equity curve (from each month out_root)
    all_eq = []
    for m in wf_months:
        tag_m = f"{args.tag}_{m}"
        eq_path = out_base / m / f"EquityCurve_{tag_m}.csv"
        if not eq_path.exists():
            print(f"[WARN] Missing equity curve: {eq_path}")
            continue
        df_m = pd.read_csv(eq_path)
        df_m["date"] = pd.to_datetime(df_m["date"])
        all_eq.append(df_m)

    if all_eq:
        df_all = pd.concat(all_eq, ignore_index=True).sort_values("date")
        df_all = df_all.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)

        plt.figure()
        plt.plot(df_all["date"], df_all["equity"])
        plt.title(f"WF Equity ({args.months}M) - {args.tag}")
        plt.savefig(plots_dir / f"WF_Equity_{args.months}M_{args.tag}.png")
        plt.close()

        peak = df_all["equity"].cummax()
        dd = (df_all["equity"] / peak) - 1.0
        plt.figure()
        plt.plot(df_all["date"], dd)
        plt.title(f"WF Drawdown ({args.months}M) - {args.tag}")
        plt.savefig(plots_dir / f"WF_Drawdown_{args.months}M_{args.tag}.png")
        plt.close()
    else:
        print("[WARN] No equity curves collected. Aggregate plots skipped.")

    # 2) Monthly returns bar
    if not df.empty:
        df_plot = df.copy()
        df_plot["month"] = df_plot["month"].astype(str)

        plt.figure()
        plt.bar(df_plot["month"], df_plot["return_pct"].values)
        plt.title(f"WF Monthly Returns - {args.tag}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(plots_dir / f"WF_Monthly_Returns_{args.tag}.png")
        plt.close()

    # Final markdown summary
    md_lines = []
    md_lines.append(f"# Walk-Forward Report ({args.tag})")
    md_lines.append("")
    md_lines.append(f"- Months: {args.months} (end_month={args.end_month})")
    md_lines.append(f"- Init Capital: {args.init_capital:,.0f}")
    md_lines.append(f"- Final Equity: {equity:,.0f}")
    total_ret = (equity / args.init_capital - 1.0) * 100
    md_lines.append(f"- Total Return: {total_ret:.2f}%")
    md_lines.append("")
    md_lines.append("## Monthly Breakdown")
    disp_cols = ["month","return_pct","trades","win_rate","mdd_pct","final_equity","pnl_sum"]
    if not df.empty:
        md_lines.append(df[disp_cols].to_markdown(index=False))
    else:
        md_lines.append("(no rows)")
    md_lines.append("")

    md_path = out_base / "wf_summary.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[OK] Saved: {csv_path}")
    print(f"[OK] Saved: {md_path}")
    print(f"[OK] Saved Plots in: {plots_dir}")

if __name__ == "__main__":
    main()
