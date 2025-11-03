import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("./imc-data/round3/data/prices_round_3_day_1.csv",sep=";")
df["mid"] = df["mid_price"]

#rows = timestamp and columns products mid price
pivot_mid = df.pivot_table(
    index="timestamp",
    columns="product",
    values="mid",
    aggfunc="last"
).sort_index()

aligned = pivot_mid[["GIFT_BASKET","ROSES","CHOCOLATE","STRAWBERRIES"]].dropna()

# Spread and synthetic
aligned["synthetic"] = aligned["ROSES"] + 4.0*aligned["CHOCOLATE"] + 6.0*aligned["STRAWBERRIES"]
aligned["spread_raw"] = aligned["GIFT_BASKET"] - aligned["synthetic"]

# Rolling stats (choose window for your sampling rate)
W = 500  
aligned["spread_mean"] = aligned["spread_raw"].rolling(W, min_periods=50).mean()
aligned["spread_std"]  = aligned["spread_raw"].rolling(W, min_periods=50).std(ddof=0)

# Demeaned and z-scored spread
aligned["spread_demeaned"] = aligned["spread_raw"] - aligned["spread_mean"]
aligned["spread_z"] = aligned["spread_demeaned"] / aligned["spread_std"]

# Simple signal logic:
up_th, dn_th = 2.0, -2.0

# --- Plot 1: Demeaned spread ---
plt.figure(figsize=(11, 4.2))
plt.plot(aligned.index.values, aligned["spread_demeaned"], label="(Basket - Synthetic) - rolling mean")
plt.title("Demeaned Spread")
plt.xlabel("Time")
plt.ylabel("Demeaned Spread")
plt.legend()
plt.tight_layout()
plt.show()

# --- Plot 2: Z-score with thresholds and markers ---
plt.figure(figsize=(11, 4.2))
plt.plot(aligned.index.values, aligned["spread_z"], label="z-score of spread")
plt.axhline(up_th, linestyle="--")
plt.axhline(dn_th, linestyle="--")
plt.title("Spread Z-Score with Thresholds")
plt.xlabel("Time")
plt.ylabel("Z-score")
plt.legend()
plt.tight_layout()
plt.show()

# #make sure to drop any empty values and only the products we need
# aligned = pivot_mid[["GIFT_BASKET","ROSES","CHOCOLATE","STRAWBERRIES"]].dropna()

# #create synthetic column in df
# aligned["synthetic"] = (
#     aligned["ROSES"] + 4.0 * aligned["CHOCOLATE"] + 6.0 * aligned["STRAWBERRIES"]
# )

# aligned["spread"] = aligned["GIFT_BASKET"] - aligned["synthetic"]

# aligned["rolling_mean"] = aligned["spread"].rolling(500,50).mean()

# print(aligned)

# plt.figure(figsize=(11,4.5))
# plt.plot(aligned.index.values, aligned["spread"], label="Spread = Basket - Synthetic")
# plt.plot(aligned.index.values, aligned["rolling_mean"], label="Rolling Mean (Window=500)")
# plt.title("Traded Spread Over Time (Basket - Synthetic)")
# plt.xlabel("Timestamp")
# plt.ylabel("Spread")
# plt.legend()
# plt.show()