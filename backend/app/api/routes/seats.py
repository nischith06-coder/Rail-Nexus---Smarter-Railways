from fastapi import APIRouter
from app.data_loader import coaches as csv_coaches, seats as csv_seats, reservations as csv_reservations, routes

router = APIRouter(prefix="/api/v1/trains", tags=["seats"])


def _stations(train_number: str):
    rs = routes(train_number)
    if rs:
        return rs
    # Fallback for prototype trains without an explicit route: derive a compact
    # deterministic route so seat intelligence still works for any fleet train.
    return [
        {"sequence": str(i + 1), "station_code": code, "station_name": name,
         "scheduled_arrival": f"{8+i:02d}:00", "scheduled_departure": f"{8+i:02d}:05"}
        for i, (code, name) in enumerate([
            ("SRC", "Source Station"), ("ST01", "Central Junction"),
            ("ST02", "City Junction"), ("ST03", "North Junction"),
            ("DST", "Destination")])
    ]


def _seat_inventory(train_number: str):
    """Build deterministic prototype seat inventory for the requested train.

    The reservation segments deliberately chain across stations. A seat can be
    occupied by passenger A, become vacant at A's destination, and then be
    reassigned to passenger B further along the route. This is prototype data,
    not live IRCTC/reservation data.
    """
    cs = csv_coaches(train_number)
    if cs:
        coach_rows = cs
    else:
        coach_rows = [
            {"train_number": train_number, "coach_id": f"S{i}",
             "coach_type": "SLEEPER", "total_seats": "20"}
            for i in range(1, 6)
        ]
    station_rows = _stations(train_number)
    n = len(station_rows)
    if n < 2:
        return [], [], station_rows

    berth_types = ["LOWER", "MIDDLE", "UPPER", "LOWER", "UPPER", "SIDE LOWER", "SIDE UPPER"]
    all_seats = []
    segments = []
    for ci, coach in enumerate(coach_rows):
        count = int(coach.get("total_seats", 20))
        for j in range(1, count + 1):
            sid = f"{coach['coach_id']}-{j}"
            # Different deterministic patterns create realistic turnover.
            pattern = (ci * 7 + j * 3) % 6
            if pattern == 0:
                blocks = [(0, min(2, n-1)), (2, min(5, n-1)), (5, n-1)]
            elif pattern == 1:
                blocks = [(0, min(3, n-1)), (4, n-1)]
            elif pattern == 2:
                blocks = [(1, min(4, n-1)), (5, n-1)] if n > 5 else [(1, n-1)]
            elif pattern == 3:
                blocks = [(0, min(4, n-1)), (4, n-1)]
            elif pattern == 4:
                blocks = [(0, min(2, n-1)), (3, min(6, n-1)), (6, n-1)]
            else:
                blocks = [(1, min(3, n-1)), (3, min(7, n-1)), (7, n-1)]
            # Remove zero-length/duplicate ranges and keep valid station spans.
            clean = []
            for a, b in blocks:
                if b > a and (a, b) not in clean:
                    clean.append((a, b))
            for k, (a, b) in enumerate(clean):
                if k and a < clean[k-1][1]:
                    a = clean[k-1][1]
                if b <= a:
                    continue
                frm = station_rows[a]
                to = station_rows[b]
                seg = {
                    "train_number": train_number, "coach_id": coach["coach_id"],
                    "seat_id": sid, "from_station": frm.get("station_name", frm.get("station_code")),
                    "from_station_code": frm.get("station_code", ""),
                    "to_station": to.get("station_name", to.get("station_code")),
                    "to_station_code": to.get("station_code", ""),
                    "from_sequence": a + 1, "to_sequence": b + 1,
                    "status": "RESERVED", "passenger_ref": f"P{ci+1:02d}{j:02d}{k+1:02d}",
                }
                segments.append(seg)

            # Current status is evaluated on the first route segment for the
            # summary; the station matrix below gives the complete journey view.
            current = clean[0] if clean and clean[0][0] == 0 else None
            all_seats.append({
                "train_number": train_number,
                "coach_id": coach["coach_id"], "seat_id": sid,
                "berth_number": str(j), "berth_type": berth_types[(j-1) % len(berth_types)],
                "status": "OCCUPIED" if current else "AVAILABLE",
            })
    return all_seats, segments, station_rows


def _station_summary(train_number: str, seat_rows, segments, station_rows):
    total = len(seat_rows)
    out = []
    for i, st in enumerate(station_rows):
        occupied = 0
        arrivals = 0
        departures = 0
        for s in segments:
            a, b = s["from_sequence"] - 1, s["to_sequence"] - 1
            if a <= i < b:
                occupied += 1
            if b == i:
                arrivals += 1
            if a == i:
                departures += 1
        out.append({
            "sequence": i + 1,
            "station_code": st.get("station_code", ""),
            "station_name": st.get("station_name", st.get("station_code", "")),
            "available": max(0, total - occupied),
            "occupied": occupied,
            "total": total,
            "passengers_vacating": arrivals,
            "new_boardings": departures,
        })
    return out


@router.get("/{train_number}/coaches")
def get_coaches(train_number: str):
    ss, _, _ = _seat_inventory(train_number)
    coach_ids = sorted({s["coach_id"] for s in ss})
    return [{"train_number": train_number, "coach_id": cid,
             "occupied": sum(s["coach_id"] == cid and s["status"] == "OCCUPIED" for s in ss),
             "available": sum(s["coach_id"] == cid and s["status"] == "AVAILABLE" for s in ss)}
            for cid in coach_ids]


@router.get("/{train_number}/seats")
def get_seats(train_number: str):
    ss, segs, stations = _seat_inventory(train_number)
    summary = _station_summary(train_number, ss, segs, stations)
    # Attach the complete journey for every seat so the UI can show turnover.
    for seat in ss:
        seat["journey_segments"] = [s for s in segs if s["seat_id"] == seat["seat_id"]]
    return {
        "train_number": train_number,
        "total": len(ss),
        "available": sum(s["status"] == "AVAILABLE" for s in ss),
        "occupied": sum(s["status"] == "OCCUPIED" for s in ss),
        "seats": ss, "station_summary": summary,
        "prototype": True, "data_status": "SIMULATED PROTOTYPE",
    }


@router.get("/{train_number}/coaches/{coach_id}/seats")
def coach_seats(train_number: str, coach_id: str):
    ss, segs, _ = _seat_inventory(train_number)
    for s in ss:
        if s["coach_id"] == coach_id:
            s["journey_segments"] = [x for x in segs if x["seat_id"] == s["seat_id"]]
    return [s for s in ss if s["coach_id"] == coach_id]


@router.get("/{train_number}/seats/{seat_id}/segments")
def seat_segments(train_number: str, seat_id: str):
    _, segs, _ = _seat_inventory(train_number)
    return [s for s in segs if s["seat_id"] == seat_id]


@router.get("/{train_number}/vacancy-forecast")
def vacancy_forecast(train_number: str):
    ss, segs, stations = _seat_inventory(train_number)
    return {"train_number": train_number, "prototype": True,
            "data_status": "SIMULATED PROTOTYPE",
            "total_seats": len(ss),
            "stations": _station_summary(train_number, ss, segs, stations)}


@router.get("/{train_number}/vacancy/{station_code}")
def vacancy(train_number: str, station_code: str):
    ss, segs, stations = _seat_inventory(train_number)
    rows = _station_summary(train_number, ss, segs, stations)
    hit = next((r for r in rows if r["station_code"].upper() == station_code.upper()), None)
    if not hit:
        return {"train_number": train_number, "station_code": station_code,
                "prototype": True, "available": 0, "occupied": 0, "total": len(ss)}
    return {"train_number": train_number, **hit, "prototype": True}
