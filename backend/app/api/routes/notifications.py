from fastapi import APIRouter
from app.state import list_notifications, add_notification, now_iso

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("")
def notifications():
    return list_notifications()

@router.post("/send")
def send(payload: dict):
    item = {"id": str(len(list_notifications())+1), **payload, "created_at": now_iso()}
    return add_notification(item)
