from app.state import platform_state, all_train_states, add_decision, set_platform_train
from app.services.eta_service import predict
from app.state import now_iso

def conflicts(station_id="KSR"):
    states = all_train_states()
    incoming = []
    for n, s in states.items():
        if s.get("next_station") in ("KSR Bengaluru", "KSR") or s.get("current_station") in ("KSR Bengaluru", "KSR"):
            incoming.append({
                "train_number": n,
                "platform": s.get("platform", "PF3"),
                "speed": s.get("current_speed", 0),
                "delay": s.get("current_delay", 0),
                "eta": predict(n),
            })
    return {"station_id": station_id, "platforms": platform_state(station_id), "conflicts": incoming}

def recommend(train_number, station_id="KSR"):
    train_number = str(train_number)
    state = dict(__import__('app.state', fromlist=['get_train_state']).get_train_state(train_number) or {})
    current_platform = state.get("platform") or "PF3"
    platform_rows = [dict(p) for p in platform_state(station_id)]
    # Ensure the selected train has a visible current platform in the prototype board.
    # Keep other platforms available so the operator can compare real options.
    if not any(str(p.get("train_number")) == train_number for p in platform_rows):
        target = next((p for p in platform_rows if p.get("platform_id") == current_platform), None)
        if target is not None and target.get("status") == "AVAILABLE":
            target["status"] = "OCCUPIED"
            target["train_number"] = train_number
    occupied = [p for p in platform_rows if p.get("status") == "OCCUPIED"]
    available = [p for p in platform_rows if p.get("status") == "AVAILABLE"]
    conflict = any(str(p.get("train_number")) == train_number for p in occupied) or (current_platform in [p.get("platform_id") for p in occupied])
    risk_score = 0
    factors=[]
    delay=float(state.get("current_delay",0) or 0)
    congestion=int(state.get("track_congestion",0) or 0)
    signal=float(state.get("signal_delay",0) or 0)
    speed=float(state.get("current_speed",0) or 0)
    if delay>5: risk_score += 25; factors.append(f"Existing delay: +{round(delay)} min")
    if congestion>=2: risk_score += 25; factors.append("Track congestion is elevated")
    if signal>0: risk_score += 20; factors.append(f"Signal impact: +{round(signal)} min")
    if speed<60: risk_score += 15; factors.append(f"Low speed: {round(speed)} km/h")
    if conflict: risk_score += 20; factors.append(f"Platform {current_platform} has a conflict")
    risk_level = "CRITICAL" if risk_score>=70 else "HIGH" if risk_score>=45 else "MEDIUM" if risk_score>=20 else "LOW"
    options=[]
    for pf in platform_rows:
        if pf.get("status")=="AVAILABLE":
            extra = 2 if pf.get("platform_id")=="PF2" else 4
            options.append({"action":"MOVE","platform":pf.get("platform_id"),"predicted_delay":extra + (5 if congestion>=2 else 0),"availability":"AVAILABLE"})
    options.append({"action":"KEEP","platform":current_platform,"predicted_delay":round(delay + (6 if conflict else 2),1),"availability":"OCCUPIED" if conflict else "CURRENT"})
    best=min(options,key=lambda x:x["predicted_delay"])
    return {
        "train_number":train_number,"station_id":station_id,"current_platform":current_platform,
        "platforms":platform_rows,"occupied_platforms":len(occupied),"available_platforms":len(available),
        "conflict":conflict,"risk_score":min(100,risk_score),"risk_level":risk_level,"factors":factors,
        "options":options,"recommendation":best,
        "reason":("Move to the recommended available platform to reduce conflict and downstream delay." if best["action"]=="MOVE" else "Keep the current platform and monitor; no lower-impact available platform is required."),
        "decision_scope":"Simulated operational decision support only — no physical railway control.","timestamp":now_iso(),
    }

def decide(train_number, station_id="KSR"):
    result = recommend(train_number, station_id)
    r = result["recommendation"]
    if r["action"] == "MOVE":
        set_platform_train(station_id, r["platform"], str(train_number))
    decision = {**result,"decision":r,"mode":"SIMULATED_OPERATIONAL_DECISION"}
    add_decision(decision)
    return decision
