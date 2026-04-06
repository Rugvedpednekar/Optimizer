from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

class ChatMessage(BaseModel):
    message: str

from app.services.nova_service import nova_service

@router.post("/")
async def chat_interaction(payload: ChatMessage):
    reply = nova_service.get_response(payload.message)
    return {"reply": reply}
