# scripts/activate_profile.py
import sys
import yaml
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/activate_profile.py <profile_name>")
        print("Available profiles can be checked in config/strategy_profile.yaml")
        return

    target_profile = sys.argv[1]
    
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "garam_core" / "config" / "strategy_profile.yaml"
    
    if not config_path.exists():
        print(f"Error: Config not found at {config_path}")
        return

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    
    profiles = data.get("profiles", {})
    if target_profile not in profiles:
        print(f"Error: Profile '{target_profile}' does not exist.")
        print(f"Available: {list(profiles.keys())}")
        return
        
    print(f"Switching Active Profile: {data.get('active_profile', 'None')} -> {target_profile}")
    data["active_profile"] = target_profile
    
    config_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print("[OK] Profile Updated.")

if __name__ == "__main__":
    main()
