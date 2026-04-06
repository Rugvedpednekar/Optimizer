from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    identifier: str
    password: str

class UserOut(BaseModel):
    id: int
    username: Optional[str] = None
    email: EmailStr
    avatar_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class WatchlistItemCreate(BaseModel):
    ticker: str

class AlgoJobCreate(BaseModel):
    ticker: str
    strategy: str
    quantity: float
    interval_minutes: int

class BacktestRequest(BaseModel):
    ticker: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float
    parameters: Optional[dict] = Field(default_factory=dict)
