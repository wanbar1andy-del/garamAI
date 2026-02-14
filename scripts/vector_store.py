
import json
import os
import numpy as np
from pathlib import Path

import ollama

def get_embedding(text, model="llama3.2:3b"):
    try:
        response = ollama.embeddings(model=model, prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"[VectorDB] Embed Error: {e}")
        return None

EMBED_MODEL = "OLLAMA"

class SimpleVectorDB:
    def __init__(self, db_path="c:/garam/garam/GARAM_Data/vectors/garam_logic.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.index = []
        self.load()

    def load(self):
        if self.db_path.exists():
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.index = json.load(f)

    def save(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=4, ensure_ascii=False)

    def add_text(self, text, metadata):
        embedding = get_embedding(text)
        if embedding:
            self.index.append({
                "text": text,
                "metadata": metadata,
                "embedding": embedding
            })

    def search(self, query, top_k=3):
        if not self.index:
            return []
        
        query_vec = get_embedding(query)
        if not query_vec: return []
        
        query_vec = np.array(query_vec)
        scored = []
        for item in self.index:
            vec = np.array(item["embedding"])
            # Cosine similarity
            sim = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-9)
            scored.append((sim, item))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"text": x[1]["text"], "score": float(x[0]), "meta": x[1]["metadata"]} for x in scored[:top_k]]

def build_garam_knowledge():
    db = SimpleVectorDB()
    root = Path("c:/garam/garam")
    
    files_to_index = [
        root / "run_real_oss_100man.py",
        root / "pipeline/backtest/run_alpha_robust.py",
        root / "core/active_config/tactical_dna.json",
        root / "scripts/ollama_bridge.py"
    ]
    
    print(f"[VectorDB] Model Status: {'LOADED' if EMBED_MODEL else 'FAILED'}")
    if not EMBED_MODEL: return

    for f in files_to_index:
        if f.exists():
            print(f" -> Indexing {f.name}...")
            content = f.read_text(encoding='utf-8')
            # Simple chunking by 1000 chars
            chunks = [content[i:i+1000] for i in range(0, len(content), 800)]
            for i, chunk in enumerate(chunks):
                db.add_text(chunk, {"file": f.name, "chunk": i})
        else:
            print(f" -> MISSING: {f}")
    
    db.save()
    print(f"[VectorDB] Success. Index size: {len(db.index)} chunks.")

if __name__ == "__main__":
    build_garam_knowledge()
