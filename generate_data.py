"""Generate synthetic hyperbolic decline production data for testing."""

import numpy as np
import pandas as pd

qi = 1200.0
b = 0.8
Di = 0.12
months = 36

t = np.arange(1, months + 1, dtype=float)
q = qi / (1 + b * Di * t) ** (1 / b)

np.random.seed(42)
noise = np.random.normal(1.0, 0.05, size=len(q))
q_noisy = q * noise
q_noisy = np.maximum(q_noisy, 1.0)

df = pd.DataFrame({"Month": t.astype(int), "Rate": np.round(q_noisy, 2)})
df.to_csv("production_data.csv", index=False)

print(f"Generated production_data.csv with {months} months of data.")
print(f"True parameters: qi={qi}, b={b}, Di={Di}")
print(df.head(10).to_string(index=False))
