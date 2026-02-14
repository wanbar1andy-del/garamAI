import pandas as pd
import os

class UniverseLoader:
    def __init__(self, universe_file):
        self.universe_file = universe_file
        
    def load(self):
        if not os.path.exists(self.universe_file):
            print(f"[Universe] File not found: {self.universe_file}")
            return []
            
        try:
            df = pd.read_csv(self.universe_file)
            cols = [c.lower() for c in df.columns]
            df.columns = cols
            
            sym_col = "symbol" if "symbol" in df.columns else "code"
            if "shcode" in df.columns: sym_col = "shcode"
            
            # Validator: 6-digit zero-pad
            symbols = df[sym_col].astype(str).str.zfill(6).tolist()
            valid_symbols = [s for s in symbols if len(s) == 6 and s.isdigit()]
            
            # Limit to Top N (Assume file is already sorted or we take all)
            # In Phase 29, we used whatever was in the file.
            # Here we assume the file IS the daily universe.
            
            print(f"[Universe] Loaded {len(valid_symbols)} symbols from {self.universe_file}")
            return valid_symbols
            
        except Exception as e:
            print(f"[Universe] Error loading universe: {e}")
            return []
