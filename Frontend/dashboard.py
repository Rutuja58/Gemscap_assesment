import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="Gemscap Quant Analytics Dashboard", layout="wide")
st.title("Gemscap Quant Analytics Dashboard")

# -------------------------
# Sidebar Controls
# -------------------------
st.sidebar.header("Controls")

symbol1_ui = st.sidebar.selectbox("Asset 1", ["BTCUSDT", "ETHUSDT"])
symbol2_ui = st.sidebar.selectbox("Asset 2", ["BTCUSDT", "ETHUSDT"], index=1)

symbol1 = symbol1_ui.lower()
symbol2 = symbol2_ui.lower()

timeframe_ui = st.sidebar.selectbox("Timeframe", ["1s", "1m", "5m"])
rolling_window = st.sidebar.number_input("Rolling Window", min_value=5, max_value=500, value=30)
alert_threshold = st.sidebar.number_input("Z-score Alert Threshold", min_value=0.1, max_value=10.0, value=2.0)

TIMEFRAME_MAP = {"1s": "1S", "1m": "1T", "5m": "5T"}
timeframe = TIMEFRAME_MAP[timeframe_ui]

st.sidebar.markdown("Auto refresh: **1 second**")

# -------------------------
# Auto Refresh
# -------------------------
st_autorefresh(interval=1000, key="refresh")

# -------------------------
# Backend API
# -------------------------
API_BASE = "http://127.0.0.1:8000"


def fetch_latest_ticks(limit=5000):
    try:
        r = requests.get(
            "http://127.0.0.1:8000/latest-ticks",
            params={"limit": limit},
            timeout=1.5   # VERY IMPORTANT
        )
        r.raise_for_status()
        df = pd.DataFrame(r.json())

        if df.empty:
            return df

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df.set_index("timestamp", inplace=True)
        return df

    except requests.exceptions.Timeout:
        st.warning("Backend timeout – waiting for ticks...")
        return pd.DataFrame()

    except Exception as e:
        st.error(f"Backend error: {e}")
        return pd.DataFrame()


# -------------------------
# Fetch Data
# -------------------------
df = fetch_latest_ticks()

st.sidebar.metric("Total ticks", len(df))

if df.empty:
    st.warning("Waiting for tick data...")
    st.stop()

df1 = df[df["symbol"] == symbol1]
df2 = df[df["symbol"] == symbol2]

if df1.empty or df2.empty:
    st.warning("Waiting for both symbols...")
    st.stop()

# -------------------------
# OHLCV Construction
# -------------------------
def build_ohlcv(df, rule):
    return df["price"].resample(rule).ohlc().dropna()

ohlcv1 = build_ohlcv(df1, timeframe)
ohlcv2 = build_ohlcv(df2, timeframe)

min_len = min(len(ohlcv1), len(ohlcv2))
ohlcv1 = ohlcv1.tail(min_len)
ohlcv2 = ohlcv2.tail(min_len)

if len(ohlcv1) < rolling_window:
    st.warning("Collecting more data...")
    st.stop()

# -------------------------
# Pair Analytics (LOCAL)
# -------------------------
y = ohlcv1["close"]
x = ohlcv2["close"]

model = OLS(y, add_constant(x)).fit()
beta = model.params[1]

spread = y - beta * x
zscore = (spread - spread.mean()) / spread.std()

rolling_corr = y.rolling(rolling_window).corr(x)

# -------------------------
# OHLCV Plot
# -------------------------
fig_ohlcv = go.Figure()
fig_ohlcv.add_candlestick(
    x=ohlcv1.index,
    open=ohlcv1["open"],
    high=ohlcv1["high"],
    low=ohlcv1["low"],
    close=ohlcv1["close"],
    name=symbol1_ui
)
fig_ohlcv.add_candlestick(
    x=ohlcv2.index,
    open=ohlcv2["open"],
    high=ohlcv2["high"],
    low=ohlcv2["low"],
    close=ohlcv2["close"],
    name=symbol2_ui
)
fig_ohlcv.update_layout(height=450, xaxis_rangeslider_visible=False)
st.plotly_chart(fig_ohlcv, use_container_width=True)

# -------------------------
# Spread & Z-score Plot
# -------------------------
fig_spread = go.Figure()
fig_spread.add_trace(go.Scatter(x=spread.index, y=spread, name="Spread"))
fig_spread.add_trace(go.Scatter(x=zscore.index, y=zscore, name="Z-score"))
fig_spread.add_hline(y=alert_threshold, line_dash="dash", line_color="red")
fig_spread.add_hline(y=-alert_threshold, line_dash="dash", line_color="red")
fig_spread.update_layout(height=400)
st.plotly_chart(fig_spread, use_container_width=True)

# -------------------------
# Rolling Correlation
# -------------------------
fig_corr = go.Figure()
fig_corr.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr, name="Rolling Correlation"))
fig_corr.update_layout(height=300)
st.plotly_chart(fig_corr, use_container_width=True)

# -------------------------
# Statistics
# -------------------------
st.subheader("Key Statistics")
stats = pd.DataFrame({
    "Metric": ["Hedge Ratio (Beta)", "Spread Mean", "Spread Std", "Latest Z-score"],
    "Value": [
        round(beta, 6),
        round(spread.mean(), 6),
        round(spread.std(), 6),
        round(zscore.iloc[-1], 6)
    ]
})
st.table(stats)

# -------------------------
# Alerts
# -------------------------
if abs(zscore.iloc[-1]) > alert_threshold:
    st.error(f"ALERT: Z-score {round(zscore.iloc[-1],2)} exceeds threshold")
else:
    st.success("Z-score within normal range")

# -------------------------
# Export
# -------------------------
st.subheader("Export Data")

if st.button("Download CSV"):
    export_df = pd.DataFrame({
        "spread": spread,
        "zscore": zscore,
        "rolling_corr": rolling_corr
    }).dropna()

    st.download_button(
        "Download CSV",
        export_df.to_csv().encode(),
        file_name=f"pair_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
