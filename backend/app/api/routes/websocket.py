import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.state import get_train_state
from app.services.eta_service import predict

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/trains/{train_number}")
async def train_socket(websocket: WebSocket, train_number: str):
    await websocket.accept()
    try:
        while True:
            state = get_train_state(train_number)
            if state:
                eta = predict(train_number)
                await websocket.send_json({"type": "train_update", "state": state, "eta": eta})
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass

@router.websocket("/ws/stations/{station_id}")
async def station_socket(websocket: WebSocket, station_id: str):
    from app.state import platform_state, list_notifications
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "type": "station_update",
                "station_id": station_id,
                "platforms": platform_state(station_id),
                "notifications": list_notifications()[:5],
            })
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass
