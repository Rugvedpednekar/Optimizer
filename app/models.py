from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(255), nullable=True, default="/static/uploads/default-avatar.png")
    created_at = Column(DateTime, default=datetime.utcnow)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    theme = Column(String(255), default="dark")

class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255))

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"))
    ticker = Column(String(255), index=True)

class SavedAnalysis(Base):
    __tablename__ = "saved_analyses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String(255))
    signal = Column(String(255))
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cash_balance = Column(Float, default=100000.0)

class Holding(Base):
    __tablename__ = "holdings"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    ticker = Column(String(255))
    quantity = Column(Float)
    average_price = Column(Float)

class PaperTrade(Base):
    __tablename__ = "paper_trades"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    ticker = Column(String(255))
    action = Column(String(255)) # BUY / SELL
    quantity = Column(Float)
    price = Column(Float)
    executed_at = Column(DateTime, default=datetime.utcnow)

class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String(255))
    strategy = Column(String(255))
    final_capital = Column(Float)
    total_return_pct = Column(Float)
    win_rate = Column(Float)
    max_drawdown_pct = Column(Float)
    sharpe_ratio = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("backtest_runs.id"))
    action = Column(String(255))
    price = Column(Float)
    executed_at = Column(DateTime)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String(255))
    content = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class AlgoJob(Base):
    __tablename__ = "algo_jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String(255), index=True)
    strategy = Column(String(255))
    quantity = Column(Float)
    interval_minutes = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AlgoTrade(Base):
    __tablename__ = "algo_trades"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("algo_jobs.id"))
    ticker = Column(String(255))
    strategy = Column(String(255))
    signal = Column(String(255))
    action_taken = Column(String(255))
    price = Column(Float)
    reason = Column(String(255))
    executed_at = Column(DateTime, default=datetime.utcnow)
