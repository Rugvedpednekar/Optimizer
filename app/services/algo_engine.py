from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.database import SessionLocal
from app.models import AlgoJob, AlgoTrade, Portfolio, Holding
from app.services.analysis_service import run_analysis

scheduler = BackgroundScheduler()

def run_strategy(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(AlgoJob).filter(AlgoJob.id == job_id).first()
        if not job or not job.is_active:
            return

        # Fetch strategy logic
        analysis = run_analysis(job.ticker)
        if "error" in analysis:
            return
        
        signal = analysis["analysis"]["event_type"]
        current_price = analysis["current_price"]
        
        # Simple paper execution logic
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == job.user_id).first()
        if not portfolio:
            return

        holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.ticker == job.ticker
        ).first()

        action_taken = "NONE"
        reason = f"Signal was {signal}"

        if signal == "BUY" and not holding:
            cost = current_price * job.quantity
            if portfolio.cash_balance >= cost:
                portfolio.cash_balance -= cost
                new_holding = Holding(portfolio_id=portfolio.id, ticker=job.ticker, quantity=job.quantity, average_price=current_price)
                db.add(new_holding)
                action_taken = "BOUGHT"
            else:
                reason = "Insufficient funds"
        
        elif signal == "SELL" and holding:
            revenue = current_price * holding.quantity
            portfolio.cash_balance += revenue
            db.delete(holding)
            action_taken = "SOLD"

        # Log Trade
        trade_log = AlgoTrade(
            job_id=job.id,
            ticker=job.ticker,
            strategy=job.strategy,
            signal=signal,
            action_taken=action_taken,
            price=current_price,
            reason=reason
        )
        db.add(trade_log)
        db.commit()

    except Exception as e:
        print(f"Error executing algo job {job_id}: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.start()

def add_job_to_scheduler(job_id: int, interval_minutes: int):
    job_ref = str(job_id)
    scheduler.add_job(
        run_strategy, 
        'interval', 
        minutes=interval_minutes, 
        args=[job_id], 
        id=job_ref, 
        replace_existing=True
    )

def remove_job_from_scheduler(job_id: int):
    job_ref = str(job_id)
    if scheduler.get_job(job_ref):
        scheduler.remove_job(job_ref)
