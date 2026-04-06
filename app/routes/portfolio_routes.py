from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db
from app.services.market_data import fetch_current_price, fetch_history
from app.services.indicators import compute_all_indicators
from app.services.signal_engine import generate_signal

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])

def safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if v == v else default
    except (TypeError, ValueError):
        return default

def get_or_create_portfolio(db: Session, user_id: int):
    portfolio = db.query(models.Portfolio).filter(models.Portfolio.user_id == user_id).first()
    if not portfolio:
        portfolio = models.Portfolio(user_id=user_id, cash_balance=100000.0)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio

def refresh_holdings(db: Session, portfolio: models.Portfolio):
    holdings = db.query(models.Holding).filter(models.Holding.portfolio_id == portfolio.id).all()
    refreshed = []
    for holding in holdings:
        current_price = safe_float(fetch_current_price(holding.ticker), safe_float(holding.average_price))
        quantity = safe_float(holding.quantity)
        average_price = safe_float(holding.average_price)
        market_value = safe_float(current_price * quantity)
        unrealized_pnl = safe_float(market_value - (average_price * quantity))
        refreshed.append(
            {
                "ticker": holding.ticker,
                "quantity": quantity,
                "average_price": average_price,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
            }
        )
    return refreshed

@router.get("")
def get_portfolio(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    portfolio = get_or_create_portfolio(db, current_user.id)
    holdings = refresh_holdings(db, portfolio)
    starting_balance = 100000.0

    total_market_value = sum(safe_float(h["market_value"]) for h in holdings)
    total_unrealized_pnl = sum(safe_float(h["unrealized_pnl"]) for h in holdings)
    total_value = safe_float(portfolio.cash_balance) + total_market_value
    
    return {
        "cash_balance": safe_float(portfolio.cash_balance),
        "starting_balance": starting_balance,
        "total_value": round(total_value, 2),
        "total_market_value": round(total_market_value, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "holdings": [
            {
                "ticker": h["ticker"],
                "quantity": safe_float(h["quantity"]),
                "average_price": safe_float(h["average_price"]),
                "average_cost": safe_float(h["average_price"]),
                "current_price": safe_float(h["current_price"]),
                "market_value": safe_float(h["market_value"]),
                "unrealized_pnl": safe_float(h["unrealized_pnl"]),
            }
            for h in holdings
        ],
    }

@router.get("/recommendations")
def get_portfolio_recommendations(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    portfolio = get_or_create_portfolio(db, current_user.id)
    holdings = refresh_holdings(db, portfolio)
    if not holdings:
        return {"items": []}

    items = []
    for holding in holdings:
        df = fetch_history(holding["ticker"], period="1y", interval="1d")
        if df is None or df.empty:
            continue

        df = compute_all_indicators(df)
        if df.empty:
            continue

        signal_data = generate_signal(df)
        latest = df.iloc[-1]
        signal = signal_data["signal"]
        confidence = signal_data["confidence"]
        action = {
            "BUY": "ADD TO POSITION",
            "SELL": "CONSIDER SELLING",
            "HOLD": "HOLD POSITION",
        }.get(signal, "HOLD POSITION")

        detail_reasons = [f"{k}: {v}" for k, v in signal_data.get("details", {}).items() if v != "Neutral"]
        reason = " | ".join(detail_reasons[:3]) or "Signal remained neutral across the latest indicator set."

        items.append(
            {
                "ticker": holding["ticker"],
                "current_price": round(float(latest["Close"]), 2),
                "signal": signal,
                "confidence": float(confidence),
                "action": action,
                "reason": reason,
            }
        )

    return {"items": items}

@router.get("/history")
def get_trade_history(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    portfolio = db.query(models.Portfolio).filter(models.Portfolio.user_id == current_user.id).first()
    if not portfolio:
        return []

    trades = (
        db.query(models.PaperTrade)
        .filter(models.PaperTrade.portfolio_id == portfolio.id)
        .order_by(models.PaperTrade.executed_at.desc())
        .all()
    )

    return [
        {
            "ticker": trade.ticker,
            "action": trade.action,
            "quantity": trade.quantity,
            "price": trade.price,
            "executed_at": trade.executed_at.isoformat() if trade.executed_at else None,
        }
        for trade in trades
    ]

@router.post("/trade")
def execute_trade(trade: dict, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # trade: {ticker, action (BUY/SELL), quantity, price}
    portfolio = db.query(models.Portfolio).filter(models.Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    ticker = trade["ticker"].upper()
    action = trade["action"].upper()
    qty = float(trade["quantity"])
    submitted_price = safe_float(trade.get("price"))
    live_price = safe_float(fetch_current_price(ticker))
    price = live_price if live_price > 0 else submitted_price
    if price <= 0:
        raise HTTPException(status_code=400, detail=f"Could not fetch a live price for {ticker}")
    cost = qty * price
    
    holding = db.query(models.Holding).filter(models.Holding.portfolio_id == portfolio.id, models.Holding.ticker == ticker).first()
    
    if action == "BUY":
        if portfolio.cash_balance < cost:
            raise HTTPException(status_code=400, detail="Insufficient cash")
        
        portfolio.cash_balance -= cost
        if holding:
            # Update average price
            total_qty = holding.quantity + qty
            holding.average_price = ((holding.average_price * holding.quantity) + cost) / total_qty
            holding.quantity = total_qty
        else:
            new_holding = models.Holding(portfolio_id=portfolio.id, ticker=ticker, quantity=qty, average_price=price)
            db.add(new_holding)
    
    elif action == "SELL":
        if not holding or holding.quantity < qty:
            raise HTTPException(status_code=400, detail="Insufficient shares")
        
        portfolio.cash_balance += cost
        holding.quantity -= qty
        if holding.quantity == 0:
            db.delete(holding)
            
    # Log trade
    log = models.PaperTrade(portfolio_id=portfolio.id, ticker=ticker, action=action, quantity=qty, price=price)
    db.add(log)
    db.commit()
    
    return {"status": "success", "cash_balance": portfolio.cash_balance}
