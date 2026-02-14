from __future__ import annotations

from pathlib import Path
import pandas as pd


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def latest_file(dir_path: Path, pattern: str) -> Path | None:
    files = sorted(dir_path.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def compute_drawdown(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return (equity / peak) - 1.0


def main() -> int:
    root = repo_root()
    log_dir = root / "results" / "logs"
    out_dir = root / "results" / "reports" / "plots"
    ensure_dir(out_dir)

    hb_path = log_dir / "engine_heartbeat.csv"
    if not hb_path.exists():
        print(f"[ERR] missing heartbeat: {hb_path}")
        return 2

    hb = pd.read_csv(hb_path)
    if len(hb) < 2:
        print("[ERR] heartbeat too short")
        return 2

    hb["ts"] = pd.to_datetime(hb["ts"], errors="coerce")
    hb = hb.dropna(subset=["ts"]).sort_values("ts")
    hb["equity"] = pd.to_numeric(hb["equity"], errors="coerce").ffill()

    dd = compute_drawdown(hb["equity"])

    trade_path = latest_file(log_dir, "trade_log_*.csv")
    exits = None
    if trade_path and trade_path.exists():
        tr = pd.read_csv(trade_path)
        if "decision" in tr.columns:
            exits = tr[tr["decision"] == "EXIT"].copy()
        else:
            exits = tr.copy()
        if "pnl" in exits.columns:
            exits["pnl"] = pd.to_numeric(exits["pnl"], errors="coerce").fillna(0.0)

    # matplotlib optional (ops-safe)
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        # fallback csv export
        hb_out = out_dir / "equity_timeseries.csv"
        hb[["ts", "equity"]].to_csv(hb_out, index=False, encoding="utf-8")
        dd_out = out_dir / "drawdown_timeseries.csv"
        pd.DataFrame({"ts": hb["ts"], "drawdown": dd}).to_csv(dd_out, index=False, encoding="utf-8")
        if exits is not None:
            exits.to_csv(out_dir / "exit_trades.csv", index=False, encoding="utf-8")
        print(f"[WARN] matplotlib not available -> exported CSV only. reason={e}")
        return 0

    report_date = pd.Timestamp.now().strftime("%Y-%m-%d")

    # 1) Equity
    fig = plt.figure()
    plt.plot(hb["ts"], hb["equity"])
    plt.title(f"Equity Curve ({report_date})")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.tight_layout()
    plt.savefig(out_dir / f"Equity_{report_date}.png", dpi=150)
    plt.close(fig)

    # 2) Drawdown
    fig = plt.figure()
    plt.plot(hb["ts"], dd)
    plt.title(f"Drawdown ({report_date})")
    plt.xlabel("Time")
    plt.ylabel("Drawdown")
    plt.tight_layout()
    plt.savefig(out_dir / f"Drawdown_{report_date}.png", dpi=150)
    plt.close(fig)

    # 3) Trade PnL histogram (EXIT only)
    if exits is not None and "pnl" in exits.columns and len(exits) > 0:
        fig = plt.figure()
        plt.hist(exits["pnl"].values, bins=30)
        plt.title(f"Exit Trade PnL Histogram ({report_date})")
        plt.xlabel("PnL")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(out_dir / f"TradePnL_{report_date}.png", dpi=150)
        plt.close(fig)

    print(f"OK: charts -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
