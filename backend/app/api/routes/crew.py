from fastapi import APIRouter, HTTPException
import hashlib
from app.data_loader import trains, coaches

router = APIRouter(prefix="/api/v1/trains", tags=["crew"])

FIRST = ["Arjun", "Vikram", "Rahul", "Suresh", "Karan", "Manoj", "Ravi", "Amit", "Prakash", "Naveen"]
LAST = ["Sharma", "Patil", "Kumar", "Reddy", "Singh", "Nair", "Iyer", "Joshi", "Verma", "Das"]

def person(label: str, seed: int, role: str):
    name = f"{FIRST[seed % len(FIRST)]} {LAST[(seed // len(FIRST)) % len(LAST)]}"
    return {"role": role, "name": name, "employee_id": f"RN-{label}-{1000 + seed:04d}", "status": "ON DUTY", "data_status": "SIMULATED PROTOTYPE"}

@router.get("/{train_number}/crew")
def get_crew(train_number: str):
    if not any(str(t["train_number"]) == str(train_number) for t in trains()):
        raise HTTPException(404, "Train not found")
    # Stable but strongly train-specific seed: different train numbers get different crews.
    digest = hashlib.sha256(str(train_number).encode("utf-8")).hexdigest()
    seed = int(digest[:12], 16) % 100000
    cs = coaches(train_number)
    coach_ids = [c["coach_id"] for c in cs]
    attendants = []
    for i, cid in enumerate(coach_ids[:8]):
        attendants.append({**person("CA", seed + i + 20, "Coach Attendant"), "coach_id": cid})
    return {
        "train_number": str(train_number),
        "data_status": "SIMULATED PROTOTYPE CREW DATA",
        "crew_assignment_id": f"RN-CREW-{str(train_number)}",
        "locomotive_id": f"RN-LOCO-{(seed % 9000) + 1000:04d}",
        "crew": {
            "driver": person("DRV", seed, "Loco Pilot / Driver"),
            "assistant_loco_pilot": person("ALP", seed + 1, "Assistant Loco Pilot"),
            "train_manager": person("TM", seed + 2, "Train Manager / Guard"),
            "chief_tte": person("TTE", seed + 3, "Chief Ticket Examiner"),
            "ticket_examiners": [person("TTE", seed + 4 + i, "Ticket Examiner (TTE)") for i in range(3)],
            "rpf_security": person("RPF", seed + 8, "Railway Security Liaison"),
            "coach_attendants": attendants,
        },
    }
