import subprocess
import sys
import os

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    try:
        subprocess.run([sys.executable, f"scripts/{script_name}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")

def main():
    print(">>> Starting Full Report Generation Pipeline...")
    
    # Check if we should re-aggregate CSVs?
    # Maybe optional. But standard flow assumes verify is done.
    # We'll run aggregation just in case.
    run_script("edge_map_400.py")
    
    # Visualizations & Analysis
    run_script("visualize_edge_map.py") # The one from before
    run_script("visualize_edge_map_regime.py") # New robust regime viz
    run_script("auto_guard_param_reco.py") # Guard reco
    
    # Detailed Reports
    run_script("report_overall_summary.py")
    run_script("report_cost_impact.py")
    run_script("report_regime_guard_reco.py")
    
    print(">>> Full Report Generation Complete.")
    print("Check 'results/' and 'reports/' directories for output.")

if __name__ == "__main__":
    main()
