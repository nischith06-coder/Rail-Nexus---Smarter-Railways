from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import threading
import time
import math
from app.api.routes import health, trains, eta, events, platforms, seats, notifications, websocket, network, whatif, demo, crew, station_view, operations
from app.state import now_iso, get_train_state, set_train_state, get_demo_override
from app.data_loader import trains as load_trains, routes as load_routes

app = FastAPI(title="RailNexus API", version="1.1.0", description="RailNexus — Smarter Railways")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in [
    health.router,
    trains.router,
    eta.router,
    events.router,
    platforms.router,
    seats.router,
    notifications.router,
    network.router,
    whatif.router,
    demo.router,
    crew.router,
    station_view.router,
    operations.router,
    websocket.router,
]:
  app.include_router(router)

@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(str(__import__("pathlib").Path(__file__).resolve().parents[2] / "frontend" / "static" / "index.html"))
@app.get("/debug/routes")
def get_routes():
  return [route.path for route in app.routes]
def _seed_fleet():
    # Seed all 2,000 prototype trains so the dashboard has a complete live fleet
    # immediately, even before the simulator performs its first tick.
    fleet = load_trains()
    for idx, train in enumerate(fleet):
        number=str(train["train_number"])
        if get_train_state(number) is not None:
            continue
        rs=load_routes(number)
        if len(rs)<2: continue
        pos=(idx*37)%1000/1000
        section=int(pos*(len(rs)-1))
        progress=(pos*(len(rs)-1))-section
        cur=rs[section]; nxt=rs[min(section+1,len(rs)-1)]
        speed=round(55+(idx*17)%56,1)
        delay=round((idx*7)%31/1.0,1)
        state={
            "train_number":number,"latitude":round(12.5+((idx*13)%160)/10,6),"longitude":round(72.5+((idx*29)%100)/10,6),
            "current_station":cur["station_name"],"next_station":nxt["station_name"],"current_speed":speed,"current_delay":delay,
            "congestion_level":idx%4,"rainfall":(idx*3)%12,"signal_delay":(idx%6),"unscheduled_halt":False,
            "unscheduled_halt_duration":0,"track_congestion":idx%3,"speed_restriction":0,"platform":"—",
            "previous_station_delay":delay,"dwell_time":2,"timestamp":now_iso(),"route_index":section,"route_progress":progress
        }
        # Use route coordinates where available; simulator will refine them on its first tick.
        coord_map={
            "KSR Bengaluru":(12.9716,77.5946),"Tumakuru":(13.3392,77.1010),"Arsikere":(13.3145,76.2570),"Davangere":(14.4644,75.9218),"Hubballi":(15.3647,75.1240),"Gadag":(15.4167,75.6290),"Belagavi":(15.8497,74.4977),"Miraj":(16.8270,74.6420),"Pune":(18.5204,73.8567),"Bhopal":(23.2599,77.4126),"New Delhi":(28.6139,77.2090),"Hazrat Nizamuddin":(28.5884,77.2500),"Mysuru":(12.2958,76.6394),"MGR Chennai Central":(13.0827,80.2707),"Dharwad":(15.4589,75.0078),"Katpadi":(12.9692,79.1559),"Hyderabad":(17.3850,78.4867),"Secunderabad":(17.4399,78.4983),"Nagpur":(21.1458,79.0882),"Howrah":(22.5958,88.2636),"Bhubaneswar":(20.2961,85.8245),"Visakhapatnam":(17.6868,83.2185),"Vijayawada":(16.5062,80.6480),"Guntur":(16.3067,80.4365),"Mumbai":(19.0760,72.8777),"Daund":(18.4650,74.5830),"Solapur":(17.6599,75.9064),"Guntakal":(15.1674,77.3736),"Anantapur":(14.6819,77.6006),"Ajmer":(26.4499,74.6399),"Jaipur":(26.9124,75.7873),"Kota":(25.2138,75.8648),"Ernakulam":(9.9816,76.2999),"Thrissur":(10.5276,76.2144),"Kozhikode":(11.2588,75.7804),"Mangaluru":(12.9141,74.8560),"Udupi":(13.3409,74.7421)
        }
        a=coord_map.get(cur["station_name"],(15.0,78.0)); b=coord_map.get(nxt["station_name"],a)
        state["latitude"]=round(a[0]+(b[0]-a[0])*progress,6); state["longitude"]=round(a[1]+(b[1]-a[1])*progress,6)
        if number=="12627":
            state.update({"latitude":12.9716,"longitude":77.5946,"current_station":"KSR Bengaluru","next_station":"Tumakuru","current_speed":95,"current_delay":5,"platform":"PF3","congestion_level":1,"track_congestion":1,"route_index":0,"route_progress":0})
        set_train_state(number,state)


_SIM_THREAD = None
_SIM_STOP = threading.Event()

_COORDS = {
    "KSR Bengaluru": (12.9716,77.5946), "Tumakuru": (13.3392,77.1010),
    "Arsikere": (13.3145,76.2570), "Davangere": (14.4644,75.9218),
    "Hubballi": (15.3647,75.1240), "Gadag": (15.4167,75.6290),
    "Belagavi": (15.8497,74.4977), "Miraj": (16.8270,74.6420),
    "Pune": (18.5204,73.8567), "Bhopal": (23.2599,77.4126),
    "New Delhi": (28.6139,77.2090), "Hazrat Nizamuddin": (28.5884,77.2500),
    "Mysuru": (12.2958,76.6394), "MGR Chennai Central": (13.0827,80.2707),
    "Dharwad": (15.4589,75.0078), "Katpadi": (12.9692,79.1559),
    "Hyderabad": (17.3850,78.4867), "Secunderabad": (17.4399,78.4983),
    "Nagpur": (21.1458,79.0882), "Howrah": (22.5958,88.2636),
    "Bhubaneswar": (20.2961,85.8245), "Visakhapatnam": (17.6868,83.2185),
    "Vijayawada": (16.5062,80.6480), "Guntur": (16.3067,80.4365),
    "Mumbai": (19.0760,72.8777), "Daund": (18.4650,74.5830),
    "Solapur": (17.6599,75.9064), "Guntakal": (15.1674,77.3736),
    "Anantapur": (14.6819,77.6006), "Ajmer": (26.4499,74.6399),
    "Jaipur": (26.9124,75.7873), "Kota": (25.2138,75.8648),
    "Ernakulam": (9.9816,76.2999), "Thrissur": (10.5276,76.2144),
    "Kozhikode": (11.2588,75.7804), "Mangaluru": (12.9141,74.8560),
    "Udupi": (13.3409,74.7421)
}

def _simulation_tick(tick):
    fleet = load_trains()
    from app.state import all_train_states
    states = all_train_states()
    for idx, train in enumerate(fleet):
        n = str(train["train_number"])
        rs = load_routes(n)
        if len(rs) < 2:
            continue
        old = states.get(n, {})
        route_index = int(old.get("route_index", 0))
        progress = float(old.get("route_progress", 0.0))
        route_index = max(0, min(route_index, len(rs)-2))

        # Vary speed slowly so the UI visibly demonstrates live telemetry.
        base = 72 + ((idx * 19) % 37)
        wave = 8 * math.sin((tick + idx) / 5.0)
        speed = max(35, min(125, base + wave))
        if n == "12627":
            speed = max(45, min(105, 78 + 17 * math.sin(tick / 6.0)))
        slow = ((tick + idx) // 12) % 7 == 3
        if slow:
            speed = max(35, speed - 22)

        delay = max(0, ((idx * 7) % 25) + int((tick + idx) / 30) % 5)
        signal = 3 if slow and idx % 29 == 0 else 0
        track = 2 if slow and idx % 7 < 3 else idx % 2
        if n == "12627":
            delay = 5 if not slow else 11
            signal = 0 if not slow else 3

        cur = rs[route_index]
        nxt = rs[min(route_index + 1, len(rs)-1)]
        a = _COORDS.get(cur["station_name"], (15.0, 78.0))
        b = _COORDS.get(nxt["station_name"], a)
        lat = a[0] + (b[0] - a[0]) * progress
        lon = a[1] + (b[1] - a[1]) * progress
        state = {
            **old, "train_number": n, "latitude": round(lat, 6), "longitude": round(lon, 6),
            "current_station": cur["station_name"], "next_station": nxt["station_name"],
            "current_speed": round(speed, 1), "current_delay": round(delay, 1),
            "congestion_level": 3 if slow else idx % 3, "rainfall": 0,
            "signal_delay": signal, "unscheduled_halt": False, "unscheduled_halt_duration": 0,
            "track_congestion": track, "speed_restriction": 60 if slow else 0,
            "platform": "PF3" if n == "12627" else ("PF2" if n == "20661" else "—"),
            "previous_station_delay": delay, "dwell_time": 2,
            "timestamp": now_iso(), "route_index": route_index, "route_progress": progress,
            "sim_tick": tick
        }
        # Demo scenarios persist across telemetry ticks. The simulator still moves the train
        # while the selected operational conditions remain applied.
        override = get_demo_override(n)
        if override:
            state.update(override)
        set_train_state(n, state)

        # Progress is deliberately tied to simulated speed. One tick = one second.
        progress += (speed / 100.0) * 0.006
        if progress >= 1.0:
            progress -= 1.0
            route_index = (route_index + 1) % max(1, len(rs)-1)
        state["route_progress"] = progress
        state["route_index"] = route_index
        set_train_state(n, state)


def _simulation_loop():
    print("RailNexus live telemetry engine started: 2,000 trains")
    print("LIVE TELEMETRY: SIMULATED FEED · updates every 1 second")
    tick = 0
    while not _SIM_STOP.is_set():
        tick += 1
        try:
            _simulation_tick(tick)
        except Exception as exc:
            print(f"Telemetry tick error: {exc}")
        _SIM_STOP.wait(1.0)


@app.get("/api/v1/weather/forecast")
def weather_forecast(train_number: str = "12627"):
    """Prototype route-weather forecast used for SIH demonstration.
    Values are deterministic simulated conditions, not live railway weather telemetry.
    """
    from app.data_loader import routes as load_route
    rs = load_route(str(train_number))
    st = get_train_state(str(train_number)) or {}
    idx = int(st.get("route_index", 0))
    points = rs[idx:idx+5] if rs else []
    if not points:
        points = [{"station_name": st.get("next_station", "Route section"), "station_code": "—"}]
    conditions = [
        (28, 32, 20, "Partly cloudy"), (27, 31, 35, "Light rain possible"),
        (29, 34, 15, "Clear intervals"), (25, 30, 55, "Scattered showers"),
        (30, 35, 10, "Mostly clear")
    ]
    forecast=[]
    for i,r in enumerate(points[:5]):
        lo,hi,rain,desc=conditions[(idx+i)%len(conditions)]
        forecast.append({"station":r.get("station_name"),"station_code":r.get("station_code"),"temperature_c":lo+(i%3),"rain_probability":rain,"condition":desc,"wind_kmh":10+(i*4)%18})
    return {"train_number":str(train_number),"source":"SIMULATED ROUTE WEATHER FORECAST","current_station":st.get("current_station"),"forecast":forecast,"disclaimer":"Prototype forecast for demonstration; replace with an authorized weather API for live deployment."}

@app.on_event("startup")
def seed_demo_state():
    global _SIM_THREAD
    _seed_fleet()
    if _SIM_THREAD is None or not _SIM_THREAD.is_alive():
        _SIM_STOP.clear()
        _SIM_THREAD = threading.Thread(target=_simulation_loop, name="railnexus-telemetry", daemon=True)
        _SIM_THREAD.start()
