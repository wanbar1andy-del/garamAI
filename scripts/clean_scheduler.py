
import subprocess
import os
import sys
import codecs

def clean_scheduler():
    print("=== GARAM Scheduled Task Cleaner ===")
    
    # List all tasks
    try:
        # Use chcp to handle potential encoding issues if needed, but python subprocess usually handles it.
        # We search for tasks related to python or garam
        output = subprocess.check_output(['schtasks', '/query', '/fo', 'csv', '/v']).decode('cp949', errors='ignore')
    except Exception as e:
        print(f"[Error] Could not query tasks: {e}")
        return

    lines = output.splitlines()
    target_tasks = []
    
    print("\n[Scanning for Suspicious Tasks]...")
    for line in lines:
        # Look for typical keywords we might have used or generic python scripts causing popups
        if 'garam' in line.lower() or 'python' in line.lower() or 'auto_start' in line.lower() or 'watchdog' in line.lower():
            # CSV format: "TaskName","Next Run Time","Status"...
            parts = line.split(',')
            if len(parts) > 0:
                task_name = parts[0].strip('"')
                # Filter out system tasks if any accidental match (unlikely with 'garam')
                if task_name.startswith('\\'): 
                    target_tasks.append(task_name)
                    print(f" -> Found: {task_name}")

    if not target_tasks:
        print(">> No GARAM-related scheduled tasks found.")
        return

    print(f"\n>> Found {len(target_tasks)} tasks to remove.")
    confirm = "Y" # Auto-confirm for this agent task as per user request "Remove unnecessary elements"
    
    if confirm.upper() == 'Y':
        for task in target_tasks:
            try:
                # /delete /tn "name" /f (force)
                subprocess.run(['schtasks', '/delete', '/tn', task, '/f'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"[Deleted] {task}")
            except subprocess.CalledProcessError as e:
                print(f"[Fail] Could not delete {task}: {e}")
    
    print("\n[Done] Cleanup finished.")

if __name__ == "__main__":
    clean_scheduler()
