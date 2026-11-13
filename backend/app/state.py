from datetime import datetime, timezone
from threading import Lock
import hashlib

_lock = Lock()
_train_states = {}
_events = []
_notifications = []
_decisions = []
_demo_overrides = {}
_platforms = {
    "KSR": [
        {"platform_id": "PF1", "status": "AVAILABLE", "train_number": None},
        {"platform_id": "PF2", "status": "AVAILABLE", "train_number": None},
        {"platform_id": "PF3", "status": "OCCUPIED", "train_number": "20661"},
        {"platform_id": "PF4", "status": "AVAILABLE", "train_number": None},
    ]
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def set_train_state(train_number, state):
    with _lock:
        _train_states[str(train_number)] = state

def get_train_state(train_number):
    with _lock:
        return _train_states.get(str(train_number))

def all_train_states():
    with _lock:
        return dict(_train_states)

def add_event(event):
    with _lock:
        _events.append(event)
    return event

def list_events():
    with _lock:
        return list(_events)

def update_event(event_id, patch):
    with _lock:
        for e in _events:
            if e["event_id"] == event_id:
                e.update(patch)
                return e
    return None

def add_notification(item):
    with _lock:
        _notifications.insert(0, item)
        del _notifications[50:]
    return item

def list_notifications():
    with _lock:
        return list(_notifications)

def add_decision(item):
    with _lock:
        _decisions.insert(0, item)
        del _decisions[50:]
    return item

def list_decisions():
    with _lock:
        return list(_decisions)

def platform_state(station_id="KSR"):
    # Deterministic simulated platform board for any station, with a mix of
    # available and occupied platforms. KSR keeps its explicit demo state.
    if station_id not in _platforms:
        seed = int(hashlib.md5(str(station_id).encode()).hexdigest()[:8], 16)
        count = 6 if str(station_id).upper() in {"KSR", "PUNE", "NDLS", "BPL"} else 4
        occupied_count = 1 + (seed % max(1, min(2, count - 1)))
        rows=[]
        for i in range(1, count+1):
            occ = i <= occupied_count
            rows.append({"platform_id": f"PF{i}", "status": "OCCUPIED" if occ else "AVAILABLE", "train_number": str(12000 + ((seed + i*37) % 8999)) if occ else None})
        _platforms[station_id] = rows
    return _platforms.get(station_id, [])

def set_platform_train(station_id, platform_id, train_number):
    for p in _platforms.setdefault(station_id, []):
        if p["platform_id"] == platform_id:
            p["train_number"] = train_number
            p["status"] = "OCCUPIED" if train_number else "AVAILABLE"



def set_platform_state(station_id, platform_id, status, train_number=None):
    for p in _platforms.setdefault(station_id, []):
        if p["platform_id"] == platform_id:
            p["train_number"] = train_number
            p["status"] = status
            return p
    return None

def set_demo_override(train_number, override):
    with _lock:
        _demo_overrides[str(train_number)] = dict(override)

def get_demo_override(train_number):
    with _lock:
        return dict(_demo_overrides.get(str(train_number), {}))

def clear_demo_override(train_number):
    with _lock:
        _demo_overrides.pop(str(train_number), None)
