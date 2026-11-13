from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from app.state import add_event, list_events, update_event, now_iso

router = APIRouter(prefix="/api/v1/events", tags=["events"])

class EventIn(BaseModel):
    event_type: str
    category: str
    location: str
    description: str
    severity: str = "MEDIUM"
    affected_section: str = ""
    start_time: str = ""
    end_time: str = ""
    status: str = "ACTIVE"

@router.post("")
def create_event(item: EventIn):
    event = {"event_id": str(uuid4())[:8], **item.model_dump(), "created_at": now_iso()}
    return add_event(event)

@router.get("")
def get_events():
    return list_events()

@router.get("/{event_id}")
def get_event(event_id: str):
    item = next((e for e in list_events() if e["event_id"] == event_id), None)
    if not item:
        raise HTTPException(404, "Event not found")
    return item

@router.patch("/{event_id}")
def patch_event(event_id: str, patch: dict):
    item = update_event(event_id, patch)
    if not item:
        raise HTTPException(404, "Event not found")
    return item
