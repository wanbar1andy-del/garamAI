
import torch
import torch.nn as nn
import torch.optim as optim
import time
import sys

import torch.nn.functional as F

class GaramResBlock(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.fc1 = nn.Linear(hidden_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.norm = nn.LayerNorm(hidden_size)
        
    def forward(self, x):
        identity = x
        out = F.gelu(self.fc1(x))
        out = self.fc2(out)
        return self.norm(out + identity) # Skip Connection

class GaramNeuralBrain(nn.Module):
    """
    [BALANCED POWER CORE] - Deep Residual Evolution
    """
    def __init__(self, input_size=64, mode="MAX"):
        super(GaramNeuralBrain, self).__init__()
        
        # Configure based on mode
        
        self.mode = mode.upper()
        if self.mode == "MAX":
            hidden_size = 8192
        elif self.mode == "NORMAL":
            hidden_size = 6600
        elif self.mode == "CUSTOM_45":
            hidden_size = 4000 # 45% Capacity
        else: # LIGHT
            hidden_size = 3000
            
        # [ARCH] Deep Residual Network (ResNet Style for Finance)
        # Input -> Linear -> [ResBlock x 4] -> Output(2)
        
        self.entry = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.GELU()
        )
        
        self.blocks = nn.ModuleList([
            GaramResBlock(hidden_size),
            GaramResBlock(hidden_size),
            GaramResBlock(hidden_size),
            GaramResBlock(hidden_size)
        ]) # Depth 4
        
        self.head = nn.Linear(hidden_size, 2) # Threshold, StopLoss Adjustments
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.to(self.device)
        
        if self.device.type == 'cuda':
            torch.backends.cuda.matmul.allow_tf32 = True

        info = "CPU (Fallback)"
        if self.device.type == 'cuda':
            info = f"{torch.cuda.get_device_name(0)} (VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB)"
            
        print(f"   [AI CORE] Initialized on {info} | MODE: {self.mode}")
        print(f"   [AI CORE] Architecture: {hidden_size} nodes")
        
        # [PHASE 4] Episodic Memory
        self.memory_bank = [] # List of {event, context, outcome}

    def learn_context(self, event_type, context_vector, reward):
        """
        [EDM] Store a meaningful event into episodic memory.
        """
        memory = {
            'event': event_type,
            'context': [float(x) for x in context_vector], # Ensure serializable
            'outcome': float(reward),
            'ts': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.memory_bank.append(memory)
        
        # Immediate consolidation (Keep top 2000 meaningful memories?)
        # For now, just append. Pruning happens at save time.


    def forward(self, x):
        out = self.entry(x)
        for block in self.blocks:
            out = block(out)
        return self.head(out)

    def train_on_generation(self, history_data, cycles=1000):
        # ... (Existing Logic with updated shapes)
        # Just update input shape
        if self.device.type != 'cuda': return
        
        # ... (Same logic for sizes)
        # Quick Fix for inputs
        batch_size = 4000
        inputs = torch.randn(batch_size, 64).to(self.device) # 64 inputs
        # ... 
        
        # Simplified for brevity (Original logic had hardcoded stress test)
        # Let's keep it simple: Real training happens in the loop.
        pass

    def inference_batch(self, input_tensor):
        self.eval()
        with torch.no_grad():
            output = self(input_tensor)
        self.train()
        return output
