import pandas as pd
import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from datetime import datetime, timedelta
from backend.storage import SessionLocal, Tick


def get_ticks(symbol: str, minutes: int = 5):
    """
    Fetch ticks from DB for the last `minutes` minutes
    """
    db = SessionLocal()
    since = datetime.utcnow() - timedelta(minutes=minutes)
    ticks = (
        db.query(Tick)
        .filter(Tick.symbol == symbol, Tick.timestamp >= since)
        .order_by(Tick.timestamp)
        .all()
    )
    db.close()

    df = pd.DataFrame([{
        "timestamp": t.timestamp,
        "price": t.price,
        "size": t.size
    } for t in ticks])

    if df.empty:
        return df

    df.set_index("timestamp", inplace=True)
    return df

def resample_ticks(df: pd.DataFrame, timeframe: str = "1T"):
    """
    Resample ticks into OHLCV bars.
    timeframe: '1s, '1T', '5T' etc.
    
    NOTE: Added a check for the deprecated 'S' alias to prevent FutureWarnings.
    """
    if df.empty:
        return df

    # CRITICAL FIX for FutureWarning: replace deprecated 'S' with 's'
    # This ensures no warnings even if the old format is somehow passed.
    if timeframe.endswith('S'):
        timeframe = timeframe.lower()

    ohlc = df['price'].resample(timeframe).ohlc()
    vol = df['size'].resample(timeframe).sum()
    ohlc['volume'] = vol
    return ohlc

def hedge_ratio_ols(symbol_y: str, symbol_x: str, minutes: int = 5):
    """
    Compute hedge ratio via OLS: Y ~ beta*X
    """
    df_y = get_ticks(symbol_y, minutes)
    df_x = get_ticks(symbol_x, minutes)

    if df_y.empty or df_x.empty:
        return None

    # Align timestamps
    df = pd.concat([df_y['price'], df_x['price']], axis=1, keys=[symbol_y, symbol_x])
    df.dropna(inplace=True)

    # Need at least two data points for OLS
    if len(df) < 2:
        return None

    X = add_constant(df[symbol_x])
    y = df[symbol_y]

    model = OLS(y, X).fit()
    beta = model.params[symbol_x]
    spread = y - beta * df[symbol_x]
    
    # Check for zero standard deviation (not enough unique prices)
    spread_std = spread.std()
    if spread_std == 0:
         zscore = pd.Series(0, index=spread.index)
    else:
         zscore = (spread - spread.mean()) / spread_std
    
    return {
        "beta": beta,
        "spread": spread,
        "zscore": zscore
    }

def rolling_correlation(symbol1: str, symbol2: str, window: int = 10, minutes: int = 5):
    """
    Compute rolling correlation of two symbols
    """
    df1 = get_ticks(symbol1, minutes)
    df2 = get_ticks(symbol2, minutes)

    if df1.empty or df2.empty:
        return None

    df = pd.concat([df1['price'], df2['price']], axis=1, keys=[symbol1, symbol2])
    df.dropna(inplace=True)
    
    if len(df) < window:
        return None

    return df[symbol1].rolling(window).corr(df[symbol2])