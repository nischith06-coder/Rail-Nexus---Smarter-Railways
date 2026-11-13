from fastapi import APIRouter, HTTPException
from app.data_loader import routes, trains
from app.state import all_train_states, add_event, add_notification, now_iso
import hashlib
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1", tags=["station-view"])
_last_snapshots = {}

def _platform_count(station):
    return 6 if station in {"KSR Bengaluru", "Pune", "Bhopal", "New Delhi"} else 4

def _seed(text):
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)

def _station_platforms(station_code, station_name, train_number):
    states = all_train_states()
    candidates = []
    for n, s in states.items():
        if s.get("next_station") == station_name or s.get("current_station") == station_name:
            candidates.append((str(n), s))
    candidates.sort(key=lambda x: (0 if x[0] == str(train_number) else 1, x[0]))
    count = _platform_count(station_name)
    platforms = [{"platform_id": f"PF{i}", "status": "AVAILABLE", "train_number": None, "movement": "OPEN"} for i in range(1, count + 1)]
    bucket = int(datetime.now(timezone.utc).timestamp() // 20)
    # Keep occupancy realistic: never fill every platform merely because many
    # trains are in the 2,000-train simulation. Occupancy is a small operational
    # sample, not a count of every nearby train.
    max_occupancy = max(1, min(count - 1, 1 + (_seed(f"{station_code}:{bucket}") % 2)))
    selected_pair = next((x for x in candidates if x[0] == str(train_number)), None)
    pool = ([selected_pair] if selected_pair else []) + [x for x in candidates if x[0] != str(train_number)]
    for idx, (n, s) in enumerate(pool[:max_occupancy]):
        pidx = (_seed(f"{station_code}:{bucket}:{n}") % count)
        # Avoid collisions deterministically.
        for _ in range(count):
            if platforms[pidx]["train_number"] is None:
                break
            pidx = (pidx + 1) % count
        platforms[pidx].update({
            "status": "OCCUPIED",
            "train_number": n,
            "movement": "ARRIVING" if s.get("next_station") == station_name else "AT STATION",
            "delay_minutes": round(float(s.get("current_delay", 0) or 0), 1),
            "speed_kmh": round(float(s.get("current_speed", 0) or 0), 1),
        })
    # If no live simulated train is currently at this station, keep one
    # deterministic occupied platform so the operator can still compare an
    # occupied platform against available capacity. This is prototype data.
    if not any(p.get("train_number") for p in platforms):
        pidx = _seed(f"fallback:{station_code}:{bucket}") % count
        platforms[pidx].update({
            "status":"OCCUPIED",
            "train_number":str(12000 + (_seed(f"occupant:{station_code}") % 8999)),
            "movement":"AT STATION",
            "delay_minutes":0,
            "speed_kmh":0,
        })

    # Selected train is guaranteed visible when it is approaching/at the station.
    selected = states.get(str(train_number))
    if selected and (selected.get("next_station") == station_name or selected.get("current_station") == station_name):
        if not any(p.get("train_number") == str(train_number) for p in platforms):
            p = platforms[0]
            if p.get("train_number"):
                p = next((x for x in platforms if not x.get("train_number")), platforms[0])
            p.update({"status":"OCCUPIED", "train_number":str(train_number), "movement":"ARRIVING" if selected.get("next_station") == station_name else "AT STATION", "delay_minutes":round(float(selected.get("current_delay",0) or 0),1), "speed_kmh":round(float(selected.get("current_speed",0) or 0),1)})
    return platforms

def _record_changes(train_number, station):
    key = f"{train_number}:{station['station_code']}"
    snapshot = tuple((p["platform_id"], p["status"], p.get("train_number")) for p in station["platforms"])
    old = _last_snapshots.get(key)
    _last_snapshots[key] = snapshot
    if old is not None and old != snapshot:
        old_map = {x[0]: (x[1], x[2]) for x in old}
        for p in station["platforms"]:
            before = old_map.get(p["platform_id"])
            after = (p["status"], p.get("train_number"))
            if before != after:
                desc = f"{station['station_name']} {p['platform_id']} changed: {before[1] or 'AVAILABLE'} → {p.get('train_number') or 'AVAILABLE'}"
                event = {"event_id": _seed(f"{key}:{p['platform_id']}:{snapshot}") % 100000000, "event_type":"PLATFORM_CHANGE", "category":"PLATFORM", "location":station['station_name'], "description":desc, "severity":"HIGH" if p.get('train_number') else "MEDIUM", "affected_section":station['station_code'], "status":"ACTIVE", "created_at":now_iso()}
                add_event(event)
                add_notification({"id":str(event['event_id']), "type":"PLATFORM_CHANGE", "title":"Platform status changed", "description":desc, "location":station['station_name'], "severity":event['severity'], "created_at":event['created_at']})

@router.get("/trains/{train_number}/station-platforms")
def train_station_platforms(train_number: str):
    if not any(str(t["train_number"]) == str(train_number) for t in trains()):
        raise HTTPException(404, "Train not found")
    rr = routes(train_number)
    result = []
    for r in rr:
        station = {"station_code":r["station_code"], "station_name":r["station_name"], "state":r.get("state",""), "sequence":int(r["sequence"]), "scheduled_arrival":r.get("scheduled_arrival",""), "scheduled_departure":r.get("scheduled_departure",""), "platforms":_station_platforms(r["station_code"], r["station_name"], train_number)}
        _record_changes(train_number, station)
        result.append(station)
    return {"train_number":str(train_number), "stations":result, "data_status":"SIMULATED PROTOTYPE", "snapshot_seconds":20, "updated_at":now_iso()}
