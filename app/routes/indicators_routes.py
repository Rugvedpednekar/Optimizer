from fastapi import APIRouter, HTTPException
from app.services.indicators import compute_all_indicators
from app.services.market_data import fetch_history

router = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


@router.get("/{ticker}")
def get_indicators(ticker: str):
    df = fetch_history(ticker.upper(), period="1y", interval="1d")
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data found for ticker")

    df = compute_all_indicators(df)
    if df.empty:
        raise HTTPException(status_code=400, detail="Not enough data to compute indicators")

    latest = df.iloc[-1]
    return {
        "ticker": ticker.upper(),
        "rsi": round(float(latest.get("RSI", 0.0)), 2),
        "macd": round(float(latest.get("MACD", 0.0)), 4),
        "macd_signal": round(float(latest.get("MACD_Signal", 0.0)), 4),
        "atr": round(float(latest.get("ATR", 0.0)), 2),
        "sma20": round(float(latest.get("SMA_20", 0.0)), 2),
        "sma50": round(float(latest.get("SMA_50", 0.0)), 2),
        "volume_spike": bool(latest.get("Volume_Spike", 0) == 1),
    }
