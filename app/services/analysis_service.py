from app.services.market_data import fetch_history, fetch_company_info
from app.services.indicators import compute_all_indicators
from app.services.signal_engine import generate_signal
from app.services.risk_engine import calculate_risk_levels

def run_analysis(ticker: str, model_type: str = "logistic", threshold: float = 0.5):
    df = fetch_history(ticker, period="1y", interval="1d")
    if df is None or df.empty:
        return {"error": "Could not fetch data"}
    
    company_info = fetch_company_info(ticker)
    
    df = compute_all_indicators(df)
    latest = df.iloc[-1]
    
    signal_data = generate_signal(df)
    
    # Adjust signal based on confidence threshold
    event_type = signal_data["signal"]
    confidence = signal_data["confidence"]
    if confidence < threshold:
        event_type = "HOLD"
        
    risk_data = calculate_risk_levels(
        price=latest["Close"], 
        atr=latest["ATR"], 
        signal=event_type
    )
    
    # Build a dynamic explanation based on active indicators
    explanation = f"AI Model ({model_type}) generated {event_type} signal. "
    if event_type == "HOLD":
        explanation += f"Confidence score ({confidence:.2f}) did not meet the {threshold:.2f} threshold."
    else:
        explanation += " ".join([f"{k} is {v}." for k, v in signal_data.get("details", {}).items() if "Bullish" in v or "Bearish" in v])
    
    return {
        "ticker": ticker,
        "company_name": company_info.get("name", ticker),
        "current_price": round(latest["Close"], 2),
        "indicators": {
            "return_5d": float(latest.get("Return_5d", 0)),
            "volume_spike": bool(latest.get("Volume_Spike", 0) == 1),
            "rsi": float(latest.get("RSI", 50)),
            "macd": float(latest.get("MACD", 0)),
            "macd_signal": float(latest.get("MACD_Signal", 0))
        },
        "analysis": {
            "confidence_score": confidence,
            "event_type": event_type,
            "explanation": explanation
        },
        "risk_profile": {
            "stop_loss": risk_data.get("stop_loss"),
            "take_profit": risk_data.get("take_profit")
        },
        "social_sentiment": float(latest.get("RSI", 50)) > 50,
        "date": str(latest.name)
    }
