# scripts/verify_profile_loader.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from garam_core.config.profile_loader import load_strategy_profile

def main():
    print(">>> Verifying Profile Loader...")
    
    # Load default
    try:
        spec = load_strategy_profile()
        print(f"[OK] Loaded active profile: '{spec.name}'")
        print(f" - Signal: {spec.signal}")
        print(f" - Turbo: {spec.turbo}")
        print(f" - Cost: {spec.cost}")
        print(f" - Risk: {spec.risk}")
    except Exception as e:
        print(f"[FAIL] Loading active profile failed: {e}")
        return

    # Load specific (aggressive_v1 placeholder)
    try:
        spec2 = load_strategy_profile(profile_name="aggressive_v1")
        print(f"\n[OK] Loaded specific profile: '{spec2.name}'")
        print(f" - Signal Cooldown: {spec2.signal.cooldown_bars}")
        print(f" - Turbo Multiplier: {spec2.turbo.max_multiplier}")
    except Exception as e:
        print(f"[FAIL] Loading 'aggressive_v1' failed: {e}")

if __name__ == "__main__":
    main()
