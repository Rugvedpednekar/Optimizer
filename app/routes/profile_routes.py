from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app import models, auth, schemas
from app.database import get_db
import os
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

@router.get("", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("", response_model=schemas.UserOut)
def update_profile(profile: ProfileUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if profile.username:
        # check collision
        existing = db.query(models.User).filter(models.User.username == profile.username, models.User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = profile.username
        
    if profile.email:
        existing = db.query(models.User).filter(models.User.email == profile.email, models.User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        current_user.email = profile.email

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/image", response_model=schemas.UserOut)
async def upload_profile_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"user_{current_user.id}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    current_user.avatar_url = f"/static/uploads/{filename}"
    db.commit()
    db.refresh(current_user)
    
    return current_user
