import pandas as pd

def generate_signal(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"signal": "HOLD", "confidence": 0.0, "details": {}}
    
    latest = df.iloc[-1]
    bullish = 0
    bearish = 0
    details = {}

    # 1. Price vs SMA20
    if latest["Close"] > latest["SMA_20"]:
        bullish += 1
        details["Price/SMA20"] = "Bullish"
    else:
        bearish += 1
        details["Price/SMA20"] = "Bearish"

    # 2. SMA Crossover
    if latest["SMA_20"] > latest["SMA_50"]:
        bullish += 1
        details["SMA20/SMA50"] = "Bullish"
    else:
        bearish += 1
        details["SMA20/SMA50"] = "Bearish"

    # 3. RSI
    if latest["RSI"] < 30:
        bullish += 1
        details["RSI"] = "Oversold (Bullish)"
    elif latest["RSI"] > 70:
        bearish += 1
        details["RSI"] = "Overbought (Bearish)"
    else:
        details["RSI"] = "Neutral"

    # 4. MACD
    if latest["MACD"] > latest["MACD_Signal"]:
        bullish += 1
        details["MACD"] = "Bullish Cross"
    else:
        bearish += 1
        details["MACD"] = "Bearish Cross"

    # 5. Bollinger Bands
    if latest["Close"] < latest["BB_Lower"]:
        bullish += 1
        details["Bollinger"] = "Bounce (Bullish)"
    elif latest["Close"] > latest["BB_Upper"]:
        bearish += 1
        details["Bollinger"] = "Reversion (Bearish)"
    else:
        details["Bollinger"] = "Neutral"

    # 6. Return 5d momentum
    if latest["Return_5d"] > 0:
        bullish += 1
        details["Momentum"] = "Bullish"
    else:
        bearish += 1
        details["Momentum"] = "Bearish"

    # 7. Volume Spike
    if latest["Volume_Spike"] == 1:
        if latest["Close"] > df.iloc[-2]["Close"]:
            bullish += 1
            details["Volume"] = "Bullish Spike"
        else:
            bearish += 1
            details["Volume"] = "Bearish Spike"
    else:
        details["Volume"] = "Normal"

    # Signal Logic
    if bullish >= bearish + 2:
        signal = "BUY"
    elif bearish >= bullish + 2:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = min(0.5 + abs(bullish - bearish) * 0.1, 0.95)

    return {
        "signal": signal,
        "confidence": round(confidence, 2),
        "bullish_votes": bullish,
        "bearish_votes": bearish,
        "details": details
    }
