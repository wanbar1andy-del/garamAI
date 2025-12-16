import json
import glob
import os

def check():
    files = glob.glob('../results/reports/tuning_phase17_*/tuning_report.json')
    if not files:
        print("No report found")
        return
        
    f = max(files, key=os.path.getctime)
    try:
        data = json.load(open(f))
        print(f"Report: {f}")
        print(f"Winner: {data.get('winner')}")
        
        # Print Hynix Details
        for exp in data.get('experiments', []):
            if exp['name'] == 'COST_0.15':
                 print(f"COST_0.15 Specs: {exp.get('metrics')}")
            if exp['name'] == 'COST_0.20':
                 print(f"COST_0.20 Specs: {exp.get('metrics')}")
            if exp['name'] == 'COST_0.25':
                 print(f"COST_0.25 Specs: {exp.get('metrics')}")
                 
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    check()
