"""
Weight Distribution Analysis
"""
import torch
from scripts.neural_brain import GaramNeuralBrain

def check_weights():
    BRAIN_FILE = "core/active_config/neuro_brain_state.pth"
    brain = GaramNeuralBrain(input_size=64, mode="MAX")
    state = torch.load(BRAIN_FILE, map_location='cpu', weights_only=True)
    brain.load_state_dict(state)
    
    # Check Head Layer
    head_w = state['head.weight']
    head_b = state['head.bias']
    
    print(f"📊 [Neural Weight Check]")
    print(f"   - Head Weight Mean: {head_w.mean():.6f}, Std: {head_w.std():.6f}")
    print(f"   - Head Weight Neg Count: {(head_w < 0).sum()} / {head_w.numel()}")
    print(f"   - Head Bias: {head_b}")
    
    # Check Entry Layer
    entry_w = state['entry.0.weight']
    print(f"   - Entry Weight Mean: {entry_w.mean():.6f}, Std: {entry_w.std():.6f}")

if __name__ == "__main__":
    check_weights()
