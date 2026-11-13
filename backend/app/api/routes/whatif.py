from fastapi import APIRouter
from app.state import get_train_state
from app.services.eta_service import predict

router = APIRouter(prefix="/api/v1/whatif", tags=["what-if"])

@router.post("")
def what_if(payload: dict):
    train = str(payload.get("train_number", "12627"))
    state = get_train_state(train)
    if not state:
        return {"error": "Train state not initialized"}
    before = predict(train)
    simulated = dict(state)
    for key in ("signal_delay", "congestion_level", "rainfall", "track_congestion", "speed_restriction"):
        if key in payload:
            simulated[key] = payload[key]
    if payload.get("unscheduled_halt") is not None:
        simulated["unscheduled_halt"] = payload["unscheduled_halt"]
    from app.ml.model_adapter import predict_eta
    from app.services.eta_service import _route_context
    distance, stops = _route_context(train, simulated)
    speed = max(20, float(simulated.get("current_speed",60)))
    scheduled = max(10, distance/speed*60)
    features = {
        "current_delay": simulated.get("current_delay",0),
        "current_speed": speed,
        "distance_remaining": distance,
        "scheduled_remaining_time": scheduled,
        "historical_average_section_time": scheduled,
        "number_of_stops_remaining": stops,
        "congestion_level": simulated.get("congestion_level",0),
        "rainfall": simulated.get("rainfall",0),
        "previous_station_delay": simulated.get("current_delay",0),
        "dwell_time": 2,
        "speed_restriction": simulated.get("speed_restriction",0),
        "signal_delay": simulated.get("signal_delay",0),
        "unscheduled_halt": int(bool(simulated.get("unscheduled_halt",False))),
        "track_congestion": simulated.get("track_congestion",0),
        "hour": 18
    }
    after = predict_eta(features)
    return {"train_number": train, "baseline_eta_minutes": before["predicted_remaining_minutes"],
            "what_if_eta_minutes": round(after,1), "delta_minutes": round(after-before["predicted_remaining_minutes"],1),
            "affected_trains": 2 if after-before["predicted_remaining_minutes"] > 5 else 0,
            "cascade_risk": "HIGH" if after-before["predicted_remaining_minutes"] > 10 else "MEDIUM" if after-before["predicted_remaining_minutes"] > 5 else "LOW"}
