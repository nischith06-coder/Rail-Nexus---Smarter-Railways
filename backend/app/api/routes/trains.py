from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.data_loader import trains, routes
from app.state import get_train_state, set_train_state, all_train_states
from app.services.risk_service import risk

router = APIRouter(prefix="/api/v1/trains", tags=["trains"])

class StateUpdate(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    current_station: str | None = None
    next_station: str | None = None
    current_speed: float | None = None
    current_delay: float | None = None
    congestion_level: float | None = None
    rainfall: float | None = None
    signal_delay: float | None = None
    unscheduled_halt: bool | None = None
    unscheduled_halt_duration: float | None = None
    track_congestion: float | None = None
    speed_restriction: float | None = None
    platform: str | None = None

@router.get("")
def list_trains():
    return trains()

@router.get("/live")
def live_trains():
    """Return every currently simulated/authorized live train state."""
    master = {t["train_number"]: t for t in trains()}
    from app.services.eta_service import predict_many
    states = all_train_states()
    etas = predict_many(states)
    result = []
    for number, state in states.items():
        item = {**master.get(number, {"train_number": number}), **state}
        item["risk"] = risk(state)
        item["eta"] = etas.get(str(number))
        result.append(item)
    return result

@router.get("/{train_number}")
def get_train(train_number: str):
    found = next((t for t in trains() if t["train_number"] == train_number), None)
    if not found:
        raise HTTPException(404, "Train not found")
    return found

@router.get("/{train_number}/route")
def get_route(train_number: str):
    return routes(train_number)

@router.post("/{train_number}/state")
def update_state(train_number: str, update: StateUpdate):
    if not any(t["train_number"] == train_number for t in trains()):
        raise HTTPException(404, "Train not found")
    current = get_train_state(train_number) or {"train_number": train_number}
    current.update({k: v for k, v in update.model_dump().items() if v is not None})
    from datetime import datetime, timezone
    current["timestamp"] = datetime.now(timezone.utc).isoformat()
    set_train_state(train_number, current)
    return {"message": "Train state updated successfully", "train_number": train_number, "state": current}

@router.get("/{train_number}/state")
def read_state(train_number: str):
    state = get_train_state(train_number)
    if not state:
        raise HTTPException(404, "Train state not initialized")
    return {**state, "risk": risk(state)}
