from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/signup", response_model=dict)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user.username:
        db_username = db.query(models.User).filter(models.User.username == user.username).first()
        if db_username:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-create portfolio and watchlist
    portfolio = models.Portfolio(user_id=new_user.id, cash_balance=100000.0)
    watchlist = models.Watchlist(user_id=new_user.id, name="My Watchlist")
    db.add(portfolio)
    db.add(watchlist)
    db.commit()
    
    access_token = auth.create_access_token(data={"sub": str(new_user.id)})
    return {"access_token": access_token, "user": schemas.UserOut.from_orm(new_user).dict()}

@router.post("/login", response_model=dict)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    identifier = user.identifier.strip()
    db_user = db.query(models.User).filter(
        or_(models.User.email == identifier, models.User.username == identifier)
    ).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth.create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "user": schemas.UserOut.from_orm(db_user).dict()}

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
