# scripts/run_launcher.py
import sys
import yaml
import subprocess
import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path(__file__).resolve().parents[1] / "garam_core" / "config"
MENU_PATH = CONFIG_DIR / "strategy_menu.yaml"
HISTORY_PATH = Path(__file__).resolve().parent / ".launcher_history.json"


def load_menu() -> Dict[str, Any]:
    with open(MENU_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_history() -> Dict[str, str]:
    if HISTORY_PATH.exists():
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_history(history: Dict[str, str]):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def get_input(prompt: str, default: str) -> str:
    val = input(f"{prompt} [{default}]: ").strip()
    return val if val else default


def main():
    print("=" * 60)
    print(" GARAM Profit-First Engine Launcher")
    print("=" * 60)

    menu = load_menu()
    history = load_history()
    defaults = menu.get("defaults", {})

    # Flatten items for selection
    options = []
    idx = 1
    for cat in menu["categories"]:
        print(f"\n[{cat['name']}]")
        for item in cat["items"]:
            print(f" {idx}. {item['label']}")
            options.append(item)
            idx += 1
    
    print("\n q. Quit")
    
    choice = input("\nSelect Option: ").strip().lower()
    if choice == 'q':
        sys.exit(0)
    
    try:
        sel_idx = int(choice) - 1
        if sel_idx < 0 or sel_idx >= len(options):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        sys.exit(1)

    selected = options[sel_idx]
    cmd_tmpl = selected["command"]
    
    # Check variables
    args = {}
    
    if selected.get("needs_symbol"):
        default_sym = history.get("last_symbol", defaults.get("symbol", "005930"))
        sym = get_input("Enter Symbol", default_sym)
        args["symbol"] = sym
        history["last_symbol"] = sym

    if selected.get("needs_symbols"):
        default_syms = history.get("last_symbols", defaults.get("symbols", "005930"))
        syms = get_input("Enter Symbols (comma separated)", default_syms)
        args["symbols"] = syms
        history["last_symbols"] = syms

    # Danger Check
    if selected.get("confirmation"):
        confirm = input(f"\n{selected['confirmation']} (Type 'YES' to confirm): ")
        if confirm != "YES":
            print("Aborted.")
            sys.exit(0)

    # Format Command
    final_cmd = cmd_tmpl.format(**args)
    print(f"\nExecuting: {final_cmd}\n")
    
    save_history(history)
    
    # Run
    try:
        subprocess.run(final_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
    except KeyboardInterrupt:
        print("\nTerminated by user.")

if __name__ == "__main__":
    main()
