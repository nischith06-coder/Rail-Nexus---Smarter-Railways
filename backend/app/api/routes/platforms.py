from fastapi import APIRouter
from app.services.platform_service import conflicts, recommend, decide
from app.state import platform_state

router = APIRouter(prefix="/api/v1", tags=["platforms"])

@router.get("/stations/{station_id}/platforms")
def platforms(station_id: str):
    return {"station_id": station_id, "platforms": platform_state(station_id)}

@router.get("/platforms/conflicts")
def get_conflicts(station_id: str = "KSR"):
    return conflicts(station_id)

@router.post("/platforms/recommend")
def recommendation(payload: dict):
    return recommend(str(payload.get("train_number", "12627")), payload.get("station_id", "KSR"))

@router.post("/platforms/decision")
def decision(payload: dict):
    return decide(str(payload.get("train_number", "12627")), payload.get("station_id", "KSR"))
