from scripts.vector_store import SimpleVectorDB
import ollama
import json
import re

class OllamaOracle:
    def __init__(self, model="llama3.1", logger=None):
        self.log = logger if logger else print
        self.db = SimpleVectorDB() # [RAG] Load Garam Knowledge
        
        # [SMART FALLBACK] Check for model availability
        try:
             resp = ollama.list()
             # Handle both object-based and dict-based responses
             models = []
             if hasattr(resp, 'models'):
                 models = [m.model for m in resp.models]
             elif isinstance(resp, dict) and 'models' in resp:
                 models = [m.get('name') or m.get('model') for m in resp['models']]
             
             if model not in models and f"{model}:latest" not in models:
                 self.log(f"⚠️ {model} not found in {models}. Falling back to llama3.2:3b.")
                 self.model = "llama3.2:3b"
             else:
                 self.model = model if model in models else f"{model}:latest"
             
             self.active = True
             self.log(f"[Ollama] ONLINE. Model: {self.model} | RAG Active.")
        except Exception as e:
             self.log(f"[Ollama] OFFLINE or Error: {e}")
             self.model = "llama3.2:3b"
             self.active = False

    def consult(self, symbol, context_dict):
        if not self.active: return 0.0
            
        # [RAG] Retrieve related Garam Logic
        query = f"Trading decision for {symbol} with RSI {context_dict.get('rsi')}"
        related = self.db.search(query, top_k=2)
        local_logic = "\n---\n".join([r['text'] for r in related])

        prompt = f"""
        [CORE LOGIC CONTEXT]
        {local_logic}
        
        [CURRENT SETUP: {symbol}]
        - RSI: {context_dict.get('rsi', 50):.1f}
        - Volume Ratio: {context_dict.get('vol_ratio', 1.0):.1f}x
        - BB Width Z: {context_dict.get('width_z', 0.0):.1f}
        - Trend (15m): {"BULLISH" if context_dict.get('trend_15m', 0) > 0 else "BEARISH"}
        - Whale Presence: {"DETECTED" if context_dict.get('whale', 0) > 0 else "NONE"}
        - Short Squeeze Sign: {"HIGH" if context_dict.get('squeeze', 0) > 0 else "LOW"}
        
        [TASK]
        You are Garam's Strategic Oracle. 
        Evaluate if this is a high-conviction HERO_FORCE move.
        SPECIAL ATTENTION: If price is dipping but VOLUME IS LOW, consider it a 'SHAKEOUT' (개미 털기) and maintain high conviction if the trend is intact.
        
        Answer with ONLY a number from 0 to 10.
        """
        
        try:
            response = ollama.chat(model=self.model, messages=[
              {'role': 'system', 'content': 'You are an elite algo-trader specialized in Garam protocol.'},
              {'role': 'user', 'content': prompt},
            ])
            content = response['message']['content']
            match = re.search(r"(\d+(\.\d+)?)", content)
            if match:
                return min(10.0, max(0.0, float(match.group(1))))
            return 5.0
        except Exception as e:
            return 5.0
