import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score
from app.services.market_data import fetch_history
from app.services.indicators import compute_all_indicators

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]

def build_dataset() -> pd.DataFrame:
    all_data = []
    for ticker in TICKERS:
        df = fetch_history(ticker, period="3y")
        if df is None or df.empty:
            continue
        
        df = compute_all_indicators(df)
        
        # Features 
        # Price, sma20, sma50, rsi, macd, macd_signal, atr, return_5d, volume_spike
        df["sentiment_score"] = 0.5 # Stub until NewsAPI integration
        df["impact_strength"] = 1.0 # Stub
        
        # Target: 1 if Return_5d 5 days from now is > 0, else 0
        df["Target"] = np.where(df["Close"].shift(-5) > df["Close"], 1, 0)
        df.dropna(inplace=True)
        all_data.append(df)
        
    return pd.concat(all_data)

def train():
    df = build_dataset()
    features = [
        "Close", "SMA_20", "SMA_50", "RSI", "MACD", "MACD_Signal", 
        "ATR", "Return_5d", "Volume_Spike", "sentiment_score", "impact_strength"
    ]
    
    X = df[features]
    y = df["Target"]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42)
    }
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    best_acc = 0
    best_model_name = ""
    best_model = None

    print("--- Training Models with 5-Fold CV ---")
    for name, model in models.items():
        fold_accs = []
        for train_idx, test_idx in kf.split(X_scaled):
            X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            fold_accs.append(accuracy_score(y_test, preds))
        
        avg_acc = np.mean(fold_accs)
        print(f"{name} Avg Accuracy: {avg_acc:.4f}")
        
        # Train on full data for final save
        model.fit(X_scaled, y)
        if avg_acc > best_acc:
            best_acc = avg_acc
            best_model_name = name
            best_model = model

    print(f"\nBest Model: {best_model_name} ({best_acc:.4f})")
    
    save_dir = os.path.join(os.path.dirname(__file__), "saved_models")
    os.makedirs(save_dir, exist_ok=True)
    
    joblib.dump(best_model, os.path.join(save_dir, "trade_model.joblib"))
    joblib.dump(scaler, os.path.join(save_dir, "scaler.joblib"))
    print("Saved best model and scaler to disk.")

if __name__ == "__main__":
    train()
