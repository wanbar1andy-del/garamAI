
import ollama
try:
    models = [m['name'] for m in ollama.list()['models']]
    print(f"Models: {models}")
except Exception as e:
    print(f"Error: {e}")
