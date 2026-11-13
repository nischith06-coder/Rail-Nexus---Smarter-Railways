from pathlib import Path
import csv, random

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
random.seed(42)

# Prototype-only network catalogue. The 2,000 train records are simulated and are
# intentionally not presented as official Indian Railways operational data.
STATION_SETS = [
    [("SBC","KSR Bengaluru","Karnataka"),("TK","Tumakuru","Karnataka"),("ASK","Arsikere","Karnataka"),("DVG","Davangere","Karnataka"),("UBL","Hubballi","Karnataka"),("GDG","Gadag","Karnataka"),("BGM","Belagavi","Karnataka"),("MRJ","Miraj","Maharashtra"),("PUNE","Pune","Maharashtra"),("BPL","Bhopal","Madhya Pradesh"),("NDLS","New Delhi","Delhi")],
    [("MAS","MGR Chennai Central","Tamil Nadu"),("KPD","Katpadi","Tamil Nadu"),("SBC","KSR Bengaluru","Karnataka"),("TK","Tumakuru","Karnataka"),("ASK","Arsikere","Karnataka"),("DVG","Davangere","Karnataka"),("UBL","Hubballi","Karnataka"),("MRJ","Miraj","Maharashtra"),("PUNE","Pune","Maharashtra"),("BPL","Bhopal","Madhya Pradesh"),("NDLS","New Delhi","Delhi")],
    [("MYS","Mysuru","Karnataka"),("SBC","KSR Bengaluru","Karnataka"),("TK","Tumakuru","Karnataka"),("ASK","Arsikere","Karnataka"),("DVG","Davangere","Karnataka"),("UBL","Hubballi","Karnataka"),("DWR","Dharwad","Karnataka"),("BGM","Belagavi","Karnataka")],
    [("PUNE","Pune","Maharashtra"),("DD","Daund","Maharashtra"),("SUR","Solapur","Maharashtra"),("GTL","Guntakal","Andhra Pradesh"),("ATP","Anantapur","Andhra Pradesh"),("SBC","KSR Bengaluru","Karnataka"),("MYS","Mysuru","Karnataka")],
    [("HYB","Hyderabad","Telangana"),("SC","Secunderabad","Telangana"),("GTL","Guntakal","Andhra Pradesh"),("ATP","Anantapur","Andhra Pradesh"),("SBC","KSR Bengaluru","Karnataka"),("TK","Tumakuru","Karnataka"),("ASK","Arsikere","Karnataka")],
    [("NDLS","New Delhi","Delhi"),("BPL","Bhopal","Madhya Pradesh"),("NGP","Nagpur","Maharashtra"),("KZJ","Kazipet","Telangana"),("SC","Secunderabad","Telangana"),("HYB","Hyderabad","Telangana")],
    [("HWH","Howrah","West Bengal"),("BBS","Bhubaneswar","Odisha"),("VSKP","Visakhapatnam","Andhra Pradesh"),("VJA","Vijayawada","Andhra Pradesh"),("GNT","Guntur","Andhra Pradesh"),("SC","Secunderabad","Telangana")],
    [("CSTM","Mumbai","Maharashtra"),("PUNE","Pune","Maharashtra"),("MRJ","Miraj","Maharashtra"),("BGM","Belagavi","Karnataka"),("DWR","Dharwad","Karnataka"),("UBL","Hubballi","Karnataka"),("GDG","Gadag","Karnataka")],
    [("AII","Ajmer","Rajasthan"),("JP","Jaipur","Rajasthan"),("KOTA","Kota","Rajasthan"),("BPL","Bhopal","Madhya Pradesh"),("NGP","Nagpur","Maharashtra"),("SC","Secunderabad","Telangana")],
    [("ERS","Ernakulam","Kerala"),("TCR","Thrissur","Kerala"),("CLT","Kozhikode","Kerala"),("MAQ","Mangaluru","Karnataka"),("UD","Udupi","Karnataka"),("UBL","Hubballi","Karnataka")],
]

# Preserve the project's primary demo train as 12627 Karnataka Express.
primary = ["12627","Karnataka Express","Express","EXPRESS","KSR Bengaluru","New Delhi"]
train_rows = [primary]
for number in range(12000, 14000):
    n = str(number)
    if n == "12627":
        continue
    pattern = STATION_SETS[(number - 12000) % len(STATION_SETS)]
    source, destination = pattern[0][1], pattern[-1][1]
    types = ["Express", "Superfast", "Intercity", "Vande Bharat", "Shatabdi-style Prototype"]
    train_type = types[(number - 12000) % len(types)]
    category = "PREMIUM" if train_type in ("Vande Bharat", "Shatabdi-style Prototype") else "EXPRESS"
    train_rows.append([n, f"RailNexus {train_type} {n}", train_type, category, source, destination])

train_rows.sort(key=lambda r: int(r[0]))
with open(DATA/"trains_master.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["train_number","train_name","train_type","category","source_station","destination_station"]); w.writerows(train_rows)

# Route records for all 2,000 simulated trains.
route_rows=[]
for idx, train in enumerate(train_rows):
    number=train[0]
    if number == "12627":
        pattern=STATION_SETS[0]
    else:
        pattern=STATION_SETS[(int(number)-12000) % len(STATION_SETS)]
    base_distance=random.randint(85,150)
    for seq,(code,name,state) in enumerate(pattern,1):
        distance=0 if seq==1 else (seq-1)*base_distance + random.randint(-12,12)
        hour=(5 + seq + idx % 8) % 24
        route_rows.append([number,seq,code,name,state,f"{hour:02d}:00",f"{hour:02d}:05",max(0,distance)])
with open(DATA/"train_routes_master.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["train_number","sequence","station_code","station_name","state","scheduled_arrival","scheduled_departure","distance_from_source_km"]); w.writerows(route_rows)

# Seat prototype is kept for the primary demo train.
coaches=[]; seats=[]; reservations=[]
for coach_num in range(1,6):
    coach=f"S{coach_num}"; coaches.append(["12627",coach,"SLEEPER",20])
    for n in range(1,21):
        sid=f"{coach}-{n}"; status="AVAILABLE" if n%3 else "OCCUPIED"
        seats.append([coach,sid,n,"LOWER" if n%2 else "UPPER",status])
        reservations.extend([
            ["12627",coach,sid,"KSR Bengaluru","Arsikere","RESERVED" if n%3==0 else "AVAILABLE"],
            ["12627",coach,sid,"Arsikere","Davangere","AVAILABLE" if n%4==0 else "RESERVED"],
            ["12627",coach,sid,"Davangere","New Delhi","RESERVED" if n%5 else "AVAILABLE"],
        ])
for fn,headers,rows in [
    ("coaches_master.csv",["train_number","coach_id","coach_type","total_seats"],coaches),
    ("seats_master.csv",["coach_id","seat_id","berth_number","berth_type","status"],seats),
    ("reservations_master.csv",["train_number","coach_id","seat_id","from_station","to_station","status"],reservations),
]:
    with open(DATA/fn,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)

with open(DATA/"operational_events.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["event_id","event_type","category","location","description","severity","affected_section","status"]); w.writerow(["E1001","SIGNAL_FAILURE","SIGNAL","Tumakuru–Arsikere","Signal issue in simulated section","HIGH","Tumakuru–Arsikere","ACTIVE"])

# 2,000-row ML training dataset. This is separate from the 2,000-train fleet.
headers=["train_number","current_station","next_station","current_delay","current_speed","distance_remaining","scheduled_remaining_time","historical_average_section_time","number_of_stops_remaining","congestion_level","rainfall","day_of_week","hour","remaining_travel_time","latitude","longitude","previous_station_delay","scheduled_arrival_time","scheduled_departure_time","actual_departure_delay","dwell_time","speed_restriction","speed_restriction_duration","signal_delay","unscheduled_halt","unscheduled_halt_duration","track_congestion","temperature","visibility","wind_speed","holiday","train_type","route_section","time_since_last_update"]
rows=[]
for _ in range(2000):
    speed=random.uniform(40,110); dist=random.uniform(20,1200); congestion=random.randint(0,3); rainfall=random.uniform(0,20); signal=random.randint(0,5); halt=random.randint(0,1); restriction=random.choice([0,0,0,60,80]); delay=random.uniform(0,30); stops=random.randint(1,12)
    scheduled=dist/max(speed,30)*60
    target=scheduled + delay*.35 + congestion*3 + rainfall*.05 + signal*1.5 + halt*8 + max(0,(speed-restriction)/max(speed,1))*scheduled*.25 + random.gauss(0,3)
    rows.append([random.randint(12000,13999),"KSR Bengaluru","Tumakuru",round(delay,2),round(speed,2),round(dist,2),round(scheduled,2),round(scheduled,2),stops,congestion,round(rainfall,2),random.randint(0,6),random.randint(0,23),round(target,2),12.97,77.59,round(delay,2),"18:00","18:05",round(delay,2),2,restriction,10,signal,halt,8 if halt else 0,random.randint(0,2),round(random.uniform(18,35),2),round(random.uniform(1,20),2),round(random.uniform(0,25),2),0,"Express","demo",10])
with open(DATA/"train_eta_dataset_clean_33_columns.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(headers); w.writerows(rows)

print(f"Generated {len(train_rows)} simulated trains and {len(route_rows)} route records.")
print("The fleet is prototype/simulated data, not official Indian Railways live data.")
