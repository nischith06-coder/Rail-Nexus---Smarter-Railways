import time
from app.data_loader import routes, trains
from app.state import set_train_state, add_notification, now_iso, all_train_states

COORDS={
"KSR Bengaluru":(12.9716,77.5946),"Tumakuru":(13.3392,77.1010),"Arsikere":(13.3145,76.2570),"Davangere":(14.4644,75.9218),"Hubballi":(15.3647,75.1240),"Gadag":(15.4167,75.6290),"Belagavi":(15.8497,74.4977),"Miraj":(16.8270,74.6420),"Pune":(18.5204,73.8567),"Bhopal":(23.2599,77.4126),"New Delhi":(28.6139,77.2090),"Hazrat Nizamuddin":(28.5884,77.2500),"Mysuru":(12.2958,76.6394),"MGR Chennai Central":(13.0827,80.2707),"Dharwad":(15.4589,75.0078),"Katpadi":(12.9692,79.1559),"Hyderabad":(17.3850,78.4867),"Secunderabad":(17.4399,78.4983),"Nagpur":(21.1458,79.0882),"Howrah":(22.5958,88.2636),"Bhubaneswar":(20.2961,85.8245),"Visakhapatnam":(17.6868,83.2185),"Vijayawada":(16.5062,80.6480),"Guntur":(16.3067,80.4365),"Mumbai":(19.0760,72.8777),"Daund":(18.4650,74.5830),"Solapur":(17.6599,75.9064),"Guntakal":(15.1674,77.3736),"Anantapur":(14.6819,77.6006),"Ajmer":(26.4499,74.6399),"Jaipur":(26.9124,75.7873),"Kota":(25.2138,75.8648),"Ernakulam":(9.9816,76.2999),"Thrissur":(10.5276,76.2144),"Kozhikode":(11.2588,75.7804),"Mangaluru":(12.9141,74.8560),"Udupi":(13.3409,74.7421)
}

def main():
    fleet=trains()
    print(f"RailNexus fleet simulator started: {len(fleet)} simulated trains")
    print("LIVE TELEMETRY: SIMULATED FEED. Press Ctrl+C to stop.")
    tick=0
    while True:
        tick+=1
        for idx,t in enumerate(fleet):
            n=str(t["train_number"]); rs=routes(n)
            if len(rs)<2: continue
            old=all_train_states().get(n,{})
            route_index=int(old.get("route_index",(idx*37)%max(1,len(rs)-1)))
            progress=float(old.get("route_progress",(idx%100)/100))
            cur=rs[min(route_index,len(rs)-2)]; nxt=rs[min(route_index+1,len(rs)-1)]
            phase=tick+idx
            slow=(phase//12)%7==3
            speed=55+((idx*17)%56) - (30 if slow else 0)
            delay=max(0, ((idx*7)%31) + ((phase//20)%4)-1)
            congestion=3 if slow else idx%3
            signal=4 if slow and idx%29==0 else 0
            track=2 if slow and idx%7<3 else idx%2
            a=COORDS.get(cur["station_name"],(15,78)); b=COORDS.get(nxt["station_name"],a)
            lat=a[0]+(b[0]-a[0])*progress; lon=a[1]+(b[1]-a[1])*progress
            state={**old,"train_number":n,"latitude":round(lat,6),"longitude":round(lon,6),"current_station":cur["station_name"],"next_station":nxt["station_name"],"current_speed":round(speed,1),"current_delay":round(delay,1),"congestion_level":congestion,"rainfall":0,"signal_delay":signal,"unscheduled_halt":False,"unscheduled_halt_duration":0,"track_congestion":track,"speed_restriction":60 if slow else 0,"platform":("PF3" if n=="12627" else ("PF2" if n=="20661" else "—")),"previous_station_delay":delay,"dwell_time":2,"timestamp":now_iso(),"route_index":route_index,"route_progress":progress}
            if n=="12627":
                state.update({"current_speed":95 if not slow else 45,"current_delay":5 if not slow else 11,"platform":"PF3"})
            set_train_state(n,state)
            progress += (0.018 + (speed/110)*0.018)
            if progress>=1:
                progress-=1; route_index=(route_index+1)%max(1,len(rs)-1)
            state["route_progress"]=progress; state["route_index"]=route_index; set_train_state(n,state)
        if tick%30==0:
            add_notification({"type":"FLEET_UPDATE","train_number":"NETWORK","message":f"Live telemetry refreshed for {len(fleet):,} simulated trains.","created_at":now_iso()})
        time.sleep(10)
if __name__=="__main__": main()
