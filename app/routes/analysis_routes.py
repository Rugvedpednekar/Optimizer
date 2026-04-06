from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db
from app.services.analysis_service import run_analysis
from app.services.market_data import fetch_history
from datetime import datetime

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

@router.get("/chart/{ticker}")
def get_chart_data(ticker: str, period: str = Query("3mo", enum=["1mo","3mo","6mo","1y"])):
    """Returns historical closing price data for charting."""
    df = fetch_history(ticker, period=period, interval="1d")
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data found for ticker")
    df = df.tail(90)  # max 90 candles
    prices = [
        {"t": str(idx.date()), "o": round(float(row["Open"]),2), "h": round(float(row["High"]),2),
         "l": round(float(row["Low"]),2), "c": round(float(row["Close"]),2), "v": int(row["Volume"])}
        for idx, row in df.iterrows()
    ]
    return {"ticker": ticker.upper(), "prices": prices}

@router.get("/history")
def get_analysis_history(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.SavedAnalysis).filter(models.SavedAnalysis.user_id == current_user.id).order_by(models.SavedAnalysis.created_at.desc()).all()

@router.post("/{ticker}")
def analyze_ticker(ticker: str, model_type: str = "logistic", threshold: float = 0.5, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    ticker = ticker.upper()
    result = run_analysis(ticker, model_type=model_type, threshold=threshold)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Save to history
    saved = models.SavedAnalysis(
        user_id=current_user.id,
        ticker=ticker,
        signal=result["analysis"]["event_type"],
        confidence=result["analysis"]["confidence_score"]
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    
    return result
