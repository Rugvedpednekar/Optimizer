import pandas as pd
import numpy as np

def add_sma(df: pd.DataFrame, window: int, column="Close"):
    df[f"SMA_{window}"] = df[column].rolling(window=window).mean()
    return df

def add_rsi(df: pd.DataFrame, window: int = 14, column="Close"):
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def add_macd(df: pd.DataFrame, fast=12, slow=26, signal=9, column="Close"):
    exp1 = df[column].ewm(span=fast, adjust=False).mean()
    exp2 = df[column].ewm(span=slow, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    return df

def add_atr(df: pd.DataFrame, window: int = 14):
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df["ATR"] = true_range.rolling(window=window).mean()
    return df

def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: int = 2, column="Close"):
    rolling_mean = df[column].rolling(window=window).mean()
    rolling_std = df[column].rolling(window=window).std()
    df["BB_Upper"] = rolling_mean + (rolling_std * num_std)
    df["BB_Lower"] = rolling_mean - (rolling_std * num_std)
    return df

def add_vwap(df: pd.DataFrame):
    q = df["Volume"]
    p = (df["Close"] + df["High"] + df["Low"]) / 3
    df["VWAP"] = (p * q).cumsum() / q.cumsum()
    return df

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = add_sma(df, 20)
    df = add_sma(df, 50)
    df = add_sma(df, 200)
    df = add_rsi(df, 14)
    df = add_macd(df)
    df = add_atr(df)
    df = add_bollinger_bands(df)
    df = add_vwap(df)
    df["Return_5d"] = df["Close"].pct_change(periods=5)
    volume_mean = df["Volume"].rolling(window=20).mean()
    df["Volume_Spike"] = np.where(df["Volume"] > (volume_mean * 1.5), 1, 0)
    return df.dropna()
