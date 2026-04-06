import yfinance as yf
import pandas as pd
import os
from typing import Optional, Dict, Any

def fetch_history(ticker: str, period: str = "2y", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetches historical market data for a given ticker."""
    try:
        t = yf.Ticker(ticker)
        # Using auto_adjust=True as requested for historical OHLCV
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
            
        # Strip timezone information from index to prevent JSON serialization errors downstream
        if isinstance(df.index, pd.DatetimeIndex):
            df.index = df.index.tz_localize(None)
            
        return df
    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        return None

def fetch_current_price(ticker: str) -> Optional[float]:
    """Extracts the most recent closing price for a given ticker."""
    df = fetch_history(ticker, period="5d")
    if df is not None and not df.empty:
        return float(df["Close"].iloc[-1])
    return None

def fetch_company_info(ticker: str) -> Dict[str, Any]:
    """Extracts fundamental company data and metadata."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "ticker": ticker,
            "name": info.get("shortName", info.get("longName", ticker)),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", 0)
        }
    except Exception as e:
        print(f"Error extracting info for {ticker}: {e}")
        return {"ticker": ticker, "name": ticker, "sector": "Unknown", "industry": "Unknown"}

def extract_data_to_csv(ticker: str, period: str = "max", output_dir: str = "data") -> Optional[str]:
    """Extracts historical data and saves it locally to a CSV file."""
    df = fetch_history(ticker, period=period)
    if df is not None and not df.empty:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"{ticker}_data.csv")
        df.to_csv(filepath)
        print(f"Data for {ticker} extracted to {filepath}")
        return filepath
    return None
