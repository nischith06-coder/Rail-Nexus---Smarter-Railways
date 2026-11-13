from pathlib import Path
import csv
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

@lru_cache(maxsize=None)
def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@lru_cache(maxsize=1)
def train_index():
    return {str(r["train_number"]): r for r in read_csv("trains_master.csv")}

@lru_cache(maxsize=1)
def route_index():
    out={}
    for r in read_csv("train_routes_master.csv"):
        out.setdefault(str(r["train_number"]), []).append(r)
    return out

def trains():
    return read_csv("trains_master.csv")

def routes(train_number):
    return route_index().get(str(train_number), [])

def coaches(train_number):
    return [r for r in read_csv("coaches_master.csv") if r["train_number"] == str(train_number)]

def seats(train_number):
    coach_ids={r["coach_id"] for r in coaches(train_number)}
    return [r for r in read_csv("seats_master.csv") if r["coach_id"] in coach_ids]

def reservations(train_number):
    return [r for r in read_csv("reservations_master.csv") if r["train_number"] == str(train_number)]
