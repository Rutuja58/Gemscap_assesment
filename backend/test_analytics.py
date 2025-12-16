# backend/test_analytics.py

from backend.analytics import get_ticks, resample_ticks, hedge_ratio_ols, rolling_correlation

SYMBOL1 = "btcusdt"
SYMBOL2 = "ethusdt"

# 1. Fetch last 5 minutes ticks
df1 = get_ticks(SYMBOL1, minutes=5)
print("Ticks for", SYMBOL1)
print(df1.head())

# 2. Resample to 1-minute bars
ohlc = resample_ticks(df1, timeframe="1T")
print("1-min OHLCV")
print(ohlc.head())

# 3. Hedge ratio OLS
result = hedge_ratio_ols(SYMBOL1, SYMBOL2, minutes=5)
if result:
    print("Hedge ratio (beta):", result["beta"])
    print("Spread head:")
    print(result["spread"].head())
    print("Z-score head:")
    print(result["zscore"].head())
else:
    print("Not enough data for hedge ratio")

# 4. Rolling correlation
corr = rolling_correlation(SYMBOL1, SYMBOL2, window=5, minutes=5)
if corr is not None:
    print("Rolling correlation head:")
    print(corr.head())
else:
    print("Not enough data for correlation")
