"""
Replay Variant Orchestrator (Experiment Runner)

목적: 실험 스펙(YAML)을 읽어 여러 Replay 변형(Variant)을 순차 실행하고, 결과를 SSOT 형식으로 비교/저장한다.
"""
import yaml
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_variants(config_path: str):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    experiment_id = config['experiment_id']
    global_conf = config['global']
    variants = config['variants']
    
    print(f"=== [EXPERIMENT] {experiment_id} ===")
    print(f"Variants: {len(variants)}")
    
    results = []
    
    for v in variants:
        v_id = v['id']
        v_name = v['name']
        print(f"\n>> Running Variant {v_id}: {v_name}")
        
        # Build Command
        cmd = [
            sys.executable, "-m", "scripts.replay_1month_test",
            "--start", global_conf['period']['start'],
            "--end", global_conf['period']['end'],
            "--universe", global_conf['universe_csv'],
            "--minute_dir", global_conf['minute_dir'],
            "--probe", global_conf['probe'],
            "--window", str(global_conf['window']),
            "--aum", str(global_conf['aum']),
            "--exit", v['exit_strategy'],
            "--cost_bps", str(v['cost_bps'])
        ]
        
        try:
            # Run Replay (synchronous)
            subprocess.run(cmd, check=True)
            
            # Find the run directory (latest created)
            # This is tricky because replay script generates timestamped dir.
            # Best way: Check stdout or find latest dir in results/replay matching ID pattern?
            # Or assume valid because we just ran it.
            
            # Find latest run dir
            root = Path("results/replay")
            # Sort by mtime
            latest_run = sorted([d for d in root.iterdir() if d.is_dir() and "replay_1m_" in d.name], 
                                key=lambda d: d.stat().st_mtime)[-1]
            
            print(f"Confirmed Run Directory: {latest_run}")
            
            # Verify Metrics (Generate metrics_verified.json)
            print("Verifying metrics...")
            verify_cmd = [
                sys.executable, "-m", "scripts.verify_replay_metrics",
                "--equity", str(latest_run / "equity_curve.csv"),
                "--out", str(latest_run / "metrics_verified.json")
            ]
            subprocess.run(verify_cmd, check=True)
            
            # Load Verified Metrics
            with open(latest_run / "metrics_verified.json", "r") as mf:
                metrics = json.load(mf)
                
            # Load Manifest (to get Proxy Rate if available)
            proxy_rate = 0.0
            if (latest_run / "manifest.json").exists():
                 with open(latest_run / "manifest.json", "r") as man_f:
                     man_data = json.load(man_f)
                     proxy_rate = man_data.get("open_proxy_rate", 0.0)

            # Collect Result
            results.append({
                "variant_id": v_id,
                "name": v_name,
                "run_id": latest_run.name,
                "metrics": metrics,
                "open_proxy_rate": proxy_rate
            })
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Variant {v_id} failed: {e}")
            results.append({
                "variant_id": v_id,
                "name": v_name,
                "status": "FAILED",
                "error": str(e)
            })

    # Save Aggregate Report
    report = {
        "experiment_id": experiment_id,
        "generated_at": datetime.now().isoformat(),
        "baseline_run_id": config.get("base_run_id", "UNKNOWN"),
        "results": results
    }
    
    out_path = Path(f"results/replay/{experiment_id}.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\n[DONE] Experiment Complete. Report: {out_path}")
    
    # Generate MD Summary (Optional simple text)
    md_path = Path(f"results/replay/{experiment_id}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Experiment Report: {experiment_id}\n\n")
        f.write("| Variant | Strategy | Cost | Return % | MDD % | Sharpe | Proxy Rate |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for res in results:
            if "metrics" in res:
                m = res["metrics"]
                f.write(f"| {res['variant_id']} ({res['name']}) | {res.get('name')} | "
                        f"{m['total_return_pct']:.2f}% | {m['mdd_pct']:.2f}% | {m['sharpe_annualized']:.2f} | {res['open_proxy_rate']:.1f}% |\n")
    print(f"MD Report: {md_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", default="config/replay_exit_variants.yaml")
    args = parser.parse_args()
    
    run_variants(args.spec)
