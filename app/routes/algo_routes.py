from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, models, auth
from app.database import get_db
from app.services.algo_engine import add_job_to_scheduler, remove_job_from_scheduler

router = APIRouter(prefix="/api/v1/algo", tags=["algo"])

@router.post("/start")
def start_algo(job_data: schemas.AlgoJobCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    job = models.AlgoJob(
        user_id=current_user.id,
        ticker=job_data.ticker,
        strategy=job_data.strategy,
        quantity=job_data.quantity,
        interval_minutes=job_data.interval_minutes,
        is_active=True
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    add_job_to_scheduler(job.id, job.interval_minutes)
    return {"status": "success", "job_id": job.id}

@router.post("/stop/{job_id}")
def stop_algo(job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    job = db.query(models.AlgoJob).filter(models.AlgoJob.id == job_id, models.AlgoJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.is_active = False
    db.commit()
    
    remove_job_from_scheduler(job.id)
    return {"status": "success", "job_id": job.id}

@router.get("/jobs")
def get_jobs(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.AlgoJob).filter(models.AlgoJob.user_id == current_user.id).all()

@router.get("/log")
def get_log(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Simple join to get trades for user's jobs
    trades = db.query(models.AlgoTrade).join(models.AlgoJob).filter(models.AlgoJob.user_id == current_user.id).all()
    return trades
