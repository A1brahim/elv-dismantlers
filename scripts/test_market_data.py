import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.metrics.market_data import get_electricity_se3

df = get_electricity_se3(force_refresh=True)

print("DF SHAPE:", df.shape)
print(df.head())