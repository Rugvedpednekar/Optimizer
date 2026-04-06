from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.config import settings
from app.routes import auth_routes, algo_routes, chat_routes, analysis_routes, backtest_routes, portfolio_routes, watchlist_routes, profile_routes, market_routes, indicators_routes
from app.services.algo_engine import start_scheduler
import os

app = FastAPI(title="Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list({
        settings.FRONTEND_ORIGIN,
        "http://localhost:8000",
        "http://localhost:5173",
    }),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
import joblib, numpy as np
from sklearn.dummy import DummyClassifier

def ensure_model_stub():
    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        model_path.parent.mkdir(parents=True, exist_ok=True)
        # 10 rows of 5 arbitrary features and binary labels
        X = np.zeros((10, 5))
        y = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        model = DummyClassifier(strategy="most_frequent")
        model.fit(X, y)
        joblib.dump(model, model_path)
        print(f"Generated minimal model stub at {model_path}")

from app.database import SessionLocal
from app import models, auth

def ensure_test_user():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "test").first()
        if not user:
            hashed = auth.get_password_hash("1234")
            # Also use test@optimizer.ai as email since it's required
            user = models.User(username="test", email="test@optimizer.ai", hashed_password=hashed)
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Setup portfolio and watchlist for test user
            portfolio = models.Portfolio(user_id=user.id, cash_balance=100000.0)
            watchlist = models.Watchlist(user_id=user.id, name="Test Watchlist")
            db.add(portfolio)
            db.add(watchlist)
            db.commit()
            print(f"Created test user (username: test, email: test@optimizer.ai) with password 1234")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    init_db()
    if settings.ENABLE_DEV_BOOTSTRAP:
        ensure_test_user()
    ensure_model_stub()
    start_scheduler() # Start the algo trading background engine

app.include_router(auth_routes.router)
app.include_router(algo_routes.router)
app.include_router(chat_routes.router)
app.include_router(analysis_routes.router)
app.include_router(backtest_routes.router)
app.include_router(portfolio_routes.router)
app.include_router(watchlist_routes.router)
app.include_router(profile_routes.router)
app.include_router(market_routes.router)
app.include_router(indicators_routes.router)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})

@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.get("/signup")
def signup(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html", context={})

@app.get("/analyze")
def analyze(request: Request):
    return templates.TemplateResponse(request=request, name="analyze.html", context={})

@app.get("/watchlist")
def watchlist(request: Request):
    return templates.TemplateResponse(request=request, name="watchlist.html", context={})

@app.get("/portfolio")
def portfolio(request: Request):
    return templates.TemplateResponse(request=request, name="portfolio.html", context={})

@app.get("/backtest")
def backtest(request: Request):
    return templates.TemplateResponse(request=request, name="backtest.html", context={})

@app.get("/chat")
def chat(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html", context={})

@app.get("/algo")
def algo(request: Request):
    return templates.TemplateResponse(request=request, name="algo.html", context={})
