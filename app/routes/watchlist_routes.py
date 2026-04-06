from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, auth, schemas
from app.database import get_db

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])

@router.get("")
def get_watchlist(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    watchlist = db.query(models.Watchlist).filter(models.Watchlist.user_id == current_user.id).first()
    if not watchlist:
        watchlist = models.Watchlist(user_id=current_user.id, name="Default")
        db.add(watchlist)
        db.commit()
        db.refresh(watchlist)
    
    items = db.query(models.WatchlistItem).filter(models.WatchlistItem.watchlist_id == watchlist.id).all()
    return [item.ticker for item in items]

@router.post("")
def add_to_watchlist(item: schemas.WatchlistItemCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    watchlist = db.query(models.Watchlist).filter(models.Watchlist.user_id == current_user.id).first()
    if not watchlist:
        watchlist = models.Watchlist(user_id=current_user.id, name="Default")
        db.add(watchlist)
        db.commit()
        db.refresh(watchlist)
    
    # Check if already in watchlist
    existing = db.query(models.WatchlistItem).filter(models.WatchlistItem.watchlist_id == watchlist.id, models.WatchlistItem.ticker == item.ticker.upper()).first()
    if existing:
        return {"status": "already exists", "ticker": item.ticker.upper()}
    
    new_item = models.WatchlistItem(watchlist_id=watchlist.id, ticker=item.ticker.upper())
    db.add(new_item)
    db.commit()
    
    return {"status": "success", "ticker": item.ticker.upper()}

@router.delete("/{ticker}")
def remove_from_watchlist(ticker: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    watchlist = db.query(models.Watchlist).filter(models.Watchlist.user_id == current_user.id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    item = db.query(models.WatchlistItem).filter(models.WatchlistItem.watchlist_id == watchlist.id, models.WatchlistItem.ticker == ticker.upper()).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ticker not in watchlist")
    
    db.delete(item)
    db.commit()
    
    return {"status": "success", "ticker": ticker.upper()}
