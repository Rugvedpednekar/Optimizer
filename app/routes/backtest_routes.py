from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import get_db
from app.services.backtester import run_backtest

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])

@router.post("")
def perform_backtest(req: schemas.BacktestRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    result = run_backtest(
        req.ticker,
        req.strategy,
        req.initial_capital,
        start_date=req.start_date,
        end_date=req.end_date,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Save backtest run
    run_log = models.BacktestRun(
        user_id=current_user.id,
        ticker=req.ticker,
        strategy=req.strategy,
        final_capital=result["final_capital"],
        total_return_pct=result["total_return_pct"],
        win_rate=result["win_rate"],
        max_drawdown_pct=result["max_drawdown_pct"],
        sharpe_ratio=result["sharpe_ratio"]
    )
    db.add(run_log)
    db.commit()
    
    return {
        "ticker": req.ticker.upper(),
        "strategy": req.strategy,
        "metrics": {
            "final_capital": result["final_capital"],
            "total_return_pct": result["total_return_pct"],
            "win_rate": result["win_rate"],
            "max_drawdown_pct": result["max_drawdown_pct"],
            "sharpe_ratio": result["sharpe_ratio"],
        },
        "equity_curve": result["equity_curve"],
        "price_curve": result["price_curve"],
        "data_start": result["data_start"],
        "data_end": result["data_end"],
    }
