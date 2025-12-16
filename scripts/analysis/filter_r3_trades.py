import pandas as pd
import sys

input_file = "results/champion_v2_1y/trades_by_regime.csv"
output_file = "results/champion_v2_1y/trades_R4.csv"

df = pd.read_csv(input_file)
r4 = df[df['entry_regime'] == 'R4_DOWN']
r4.to_csv(output_file, index=False)
print(f"Filtered {len(r4)} R4 trades to {output_file}")
