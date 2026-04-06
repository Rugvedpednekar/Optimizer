import os
import joblib
import pandas as pd
from app.config import settings

def load_model():
    save_dir = os.path.join(os.path.dirname(__file__), "saved_models")
    model_path = os.path.join(save_dir, "trade_model.joblib")
    scaler_path = os.path.join(save_dir, "scaler.joblib")
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        return model, scaler
    return None, None

def predict_signal(features_df: pd.DataFrame) -> dict:
    model, scaler = load_model()
    if not model or not scaler:
        return {"probability": 0.0, "signal": "HOLD", "error": "Model not trained"}
        
    features = [
        "Close", "SMA_20", "SMA_50", "RSI", "MACD", "MACD_Signal", 
        "ATR", "Return_5d", "Volume_Spike", "sentiment_score", "impact_strength"
    ]
    
    X = features_df[features]
    X_scaled = scaler.transform(X)
    
    # Predict probability of class 1 (upward move)
    prob_up = model.predict_proba(X_scaled)[0][1]
    
    signal = "HOLD"
    if prob_up >= settings.PREDICTION_THRESHOLD:
        signal = "BUY"
    elif prob_up <= (1 - settings.PREDICTION_THRESHOLD):
        signal = "SELL"
        
    return {
        "probability": round(prob_up, 4),
        "signal": signal
    }
