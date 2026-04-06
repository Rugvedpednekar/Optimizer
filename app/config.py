import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "secret"
    DATABASE_URL: str = "sqlite:///./data/app.db"
    APP_ENV: str = "development"
    ENABLE_DEV_BOOTSTRAP: bool = False
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    MODEL_PATH: str = "app/ml/saved_models/trade_model.joblib"
    PREDICTION_THRESHOLD: float = 0.60
    NEWS_API_KEY: str = ""
    FRONTEND_ORIGIN: str = "http://localhost:8000"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
