
# ... Imports ...
import sys
import pandas as pd
import numpy as np
import copy
import time
import multiprocessing
import json
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from dataclasses import dataclass

sys.path.append(str(Path(__file__).resolve().parent.parent))

from garam_core.replay.replay_runner import run_replay, ReplaySpec
from garam_core.engine.regime import RegimeParams
from garam_core.engine.signal import SignalParams
from garam_core.engine.turbo import TurboParams
from garam_core.execution.fill_model import FillSpec
from garam_core.execution.cost_model import CostModel

# Import GPU Brain
try:
    from scripts.neural_brain import GaramNeuralBrain
    USE_GPU_BRAIN = True
except:
    USE_GPU_BRAIN = False

@dataclass
class Genome:
    fast_ma: int = 5
    slow_ma: int = 20
    vol_window: int = 60
    max_mult: float = 2.0
    target_vol: float = 0.002
    
    def to_dict(self):
        return {
            "fast_ma": self.fast_ma, "slow_ma": self.slow_ma,
            "vol_window": self.vol_window, "max_mult": self.max_mult,
            "target_vol": self.target_vol
        }
    
    def to_params(self):
        sp = SignalParams()
        tp = TurboParams(max_multiplier=self.max_mult, vol_window=self.vol_window, target_vol=self.target_vol)
        return sp, tp

def run_simulation(genome, symbol="005930", days=60):
    project_root = Path(__file__).resolve().parent.parent
    replay_spec = ReplaySpec(symbol=symbol, timeframe="minute", timezone="Asia/Seoul", warmup_bars=200, 
                             fill=FillSpec(method="NEXT_OPEN"), cost=CostModel(slippage_rate=0.0002, sell_tax_rate=0.0023), 
                             max_bars=days*381)
    signal_params, turbo_params = genome.to_params()
    
    try:
        import garam_core.replay.replay_runner as runner_module
        from garam_core.data.loader import load_ohlcv as original_load
        
        # Determine cutoff based on file year or just allow all
        CUTOFF_DATE = "2026-12-31"

        def patched_load(*args, **kwargs):
            df = original_load(*args, **kwargs)
            if not isinstance(df.index, pd.DatetimeIndex): df.index = pd.to_datetime(df.index)
            return df
            
        runner_module.load_ohlcv = patched_load
        
        res = run_replay(project_root=project_root, replay=replay_spec, regime_params=RegimeParams(), 
                         signal_params=signal_params, turbo_params=turbo_params, initial_equity=100_000_000.0, collect_debug=False)
        return res
    except:
        return None

def _worker_simulation(args):
    return run_simulation(*args)

def save_active_params(winner_entry):
    active_config_path = Path("config/active_strategy_params.json")
    active_config_path.parent.mkdir(exist_ok=True)
    
    genome = winner_entry['genome']
    
    active_params = {
        "timestamp": datetime.now().isoformat(),
        "market_regime": "ADAPTIVE_SHORT_SQUEEZE",
        "parameters": genome.to_dict(),
        "performance_expectation": {
            "return": winner_entry['ret'],
            "mdd": winner_entry['mdd'],
            "score": winner_entry['score']
        }
    }
    
    with open(active_config_path, "w") as f:
        json.dump(active_params, f, indent=4)
    print(f"\n>> [OSS SAVE] Active Parameters Saved: {active_config_path}")

def train_gym():
    print("=== [OSS] Garam OSS Training Gym (Quick Report Mode) ===")
    
    brain = None
    if USE_GPU_BRAIN:
        try:
            brain = GaramNeuralBrain(input_size=5, hidden_size=1024)
        except: pass

    cpu_count = multiprocessing.cpu_count()
    workers = max(1, int(cpu_count * 0.8))
    
    pop_size = 10 # Small for speed
    print(f">> [Hardware] {workers} Workers | Population: {pop_size} (Speed Mode)")

    population = [Genome() for _ in range(pop_size)]
    # Seed diversity
    for i in range(pop_size):
        population[i].target_vol = 0.002 * (0.8 + 0.4 * i/pop_size)
        population[i].max_mult = 1.0 + (4.0 * i/pop_size)

    max_generations = 2
    history = []
    
    best_ever = None

    for gen in range(max_generations + 1):
        print(f"\n>> [Gen {gen}] Simulating...")
        
        tasks = [(genome, "005930", 60) for genome in population]
        results = []
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_genome = {executor.submit(_worker_simulation, t): t[0] for t in tasks}
            for future in as_completed(future_to_genome):
                genome = future_to_genome[future]
                try:
                    res = future.result()
                    if res:
                        results.append((genome, res))
                except: pass
        
        if not results:
            print("   [!] No results. Randomizing.")
            population = [Genome(target_vol=0.001*i, max_mult=1.0+i*0.5) for i in range(pop_size)]
            continue

        gen_scores = []
        for genome, res in results:
            ret = res.metrics['total_return'] * 100
            mdd = res.metrics['max_drawdown'] * 100
            score = ret - abs(mdd*0.5)
            gen_scores.append({"genome": genome, "score": score, "ret": ret, "mdd": mdd})

        gen_scores.sort(key=lambda x: x['score'], reverse=True)
        winner = gen_scores[0]
        print(f"   [WINNER] Score: {winner['score']:.2f} (Ret: {winner['ret']:.2f}%)")
        
        if best_ever is None or winner['score'] > best_ever['score']:
            best_ever = winner
            save_active_params(winner) # Save immediately on improvement
        
        if brain:
            try: brain.train_on_generation(gen_scores, cycles=200)
            except: pass
            
        # Evolve
        new_pop = [copy.deepcopy(winner['genome'])]
        for _ in range(pop_size - 1):
            mutant = copy.deepcopy(winner['genome'])
            import random
            mutant.target_vol *= random.uniform(0.9, 1.1)
            mutant.max_mult = max(1.0, min(5.0, mutant.max_mult + random.uniform(-0.5, 0.5)))
            new_pop.append(mutant)
        population = new_pop

    print("\n[Complete] Quick Training Done.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    train_gym()
