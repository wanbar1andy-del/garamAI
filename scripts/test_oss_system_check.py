"""
OSS System Self-Check Script
Performs pre-flight diagnostics on OSS intelligence system
"""
import sys
sys.path.append('c:/garam/garam')

import torch
from scripts.neural_brain import GaramNeuralBrain
from pathlib import Path

print("=" * 60)
print("🔍 OSS SYSTEM SELF-CHECK")
print("=" * 60)

# Paths
BRAIN_PATH = Path("c:/garam/garam/core/active_config/neuro_brain_state_REAL_V2.pth")
MEMORY_PATH = Path("c:/garam/garam/core/active_config/oss_episodic_memory.json")
GENES_PATH = Path("c:/garam/garam/core/active_config/evolved_genes.json")

errors = []
warnings = []

# ========== Check 1: GPU Detection ==========
print("\n[1/6] GPU Detection...")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    print(f"   ✅ [PASS] GPU Detected: {gpu_name}")
    device = torch.device('cuda')
else:
    print("   ⚠️  [WARN] GPU NOT Detected. Running on CPU (Slow).")
    warnings.append("GPU not available - performance will be degraded")
    device = torch.device('cpu')

# ========== Check 2: Brain State File ==========
print("\n[2/6] Brain State File...")
if BRAIN_PATH.exists():
    size_mb = BRAIN_PATH.stat().st_size / 1024 / 1024
    print(f"   ✅ [PASS] Brain State Found: {size_mb:.2f} MB")
else:
    print(f"   ❌ [FAIL] Brain State NOT Found: {BRAIN_PATH}")
    errors.append("Brain state file missing")

# ========== Check 3: Brain Loading & Architecture ==========
print("\n[3/6] Brain Loading & Architecture...")
try:
    # FIXED: Use CUSTOM_45 mode for 4000-node architecture
    brain = GaramNeuralBrain(input_size=64, mode="CUSTOM_45").to(device)
    state = torch.load(BRAIN_PATH, map_location=device)
    brain.load_state_dict(state)
    
    total_params = sum(p.numel() for p in brain.parameters())
    print(f"   ✅ [PASS] Brain Loaded: {total_params:,} parameters")
    
    # Weight Health Check
    w_std = brain.entry[0].weight.std().item()
    if w_std < 0.001:
        print(f"   ❌ [FAIL] Brain Weights Flat (std={w_std:.6f})")
        errors.append(f"Dead neurons detected (std={w_std:.6f})")
    else:
        print(f"   ✅ [PASS] Weight Health OK (std={w_std:.4f})")
        
except Exception as e:
    print(f"   ❌ [FAIL] Brain Loading Failed: {e}")
    errors.append(f"Brain loading error: {e}")

# ========== Check 4: Episodic Memory File ==========
print("\n[4/6] Episodic Memory File...")
if MEMORY_PATH.exists():
    size_kb = MEMORY_PATH.stat().st_size / 1024
    print(f"   ✅ [PASS] Memory File Found: {size_kb:.1f} KB")
    
    # Test read/write access
    try:
        with open(MEMORY_PATH, "a") as f:
            pass
        print(f"   ✅ [PASS] Memory File Writable")
    except Exception as e:
        print(f"   ❌ [FAIL] Memory File Write Denied: {e}")
        errors.append(f"Memory file not writable: {e}")
else:
    print(f"   ⚠️  [WARN] Memory File NOT Found (will be created)")
    warnings.append("Memory file missing - will start with empty memory")

# ========== Check 5: Evolved Genes ==========
print("\n[5/6] Evolved Genes Configuration...")
if GENES_PATH.exists():
    import json
    try:
        with open(GENES_PATH, 'r') as f:
            genes = json.load(f)
        print(f"   ✅ [PASS] Genes Loaded: {len(genes)} parameters")
        print(f"      - RSI Low: {genes.get('rsi_low', 'N/A')}")
        print(f"      - Vol Explosive: {genes.get('vol_explosive', 'N/A')}")
    except Exception as e:
        print(f"   ❌ [FAIL] Genes Parse Error: {e}")
        errors.append(f"Genes file corrupt: {e}")
else:
    print(f"   ⚠️  [WARN] Genes File NOT Found")
    warnings.append("Evolved genes missing - using defaults")

# ========== Check 6: Inference Test ==========
print("\n[6/6] Inference Test...")
try:
    test_input = torch.randn(5, 64).to(device)
    with torch.no_grad():
        output = brain(test_input)
    
    if output.shape == torch.Size([5, 2]):
        print(f"   ✅ [PASS] Inference OK: {output.shape}")
        print(f"      - Sample Output: [{output[0, 0]:.4f}, {output[0, 1]:.4f}]")
    else:
        print(f"   ❌ [FAIL] Unexpected Output Shape: {output.shape}")
        errors.append(f"Wrong output shape: {output.shape}")
        
except Exception as e:
    print(f"   ❌ [FAIL] Inference Failed: {e}")
    errors.append(f"Inference error: {e}")

# ========== FINAL REPORT ==========
print("\n" + "=" * 60)
print("📊 FINAL REPORT")
print("=" * 60)

if warnings:
    print(f"\n⚠️  Warnings ({len(warnings)}):")
    for w in warnings:
        print(f"   - {w}")

if errors:
    print(f"\n❌ Errors ({len(errors)}):")
    for e in errors:
        print(f"   - {e}")
    print("\n🛑 [RESULT] SYSTEM CHECK FAILED")
    print("   System is NOT ready for deployment.")
    sys.exit(1)
else:
    print("\n✅ [RESULT] ALL CHECKS PASSED")
    print("   System is READY for deployment.")
    if warnings:
        print("   (Some warnings present - review above)")
    sys.exit(0)
