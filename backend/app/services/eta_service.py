from datetime import datetime, timedelta, timezone
from app.data_loader import routes
from app.state import get_train_state, all_train_states
from app.ml.model_adapter import predict_eta, predict_eta_batch

def _route_context(train_number, state):
    rs=routes(train_number); current=state.get("current_station"); nxt=state.get("next_station")
    if not rs: return 100.0, 1
    cur_idx=0
    for i,r in enumerate(rs):
        if r["station_name"]==current: cur_idx=i; break
    nxt_idx=min(cur_idx+1,len(rs)-1)
    if nxt:
        for i,r in enumerate(rs):
            if r["station_name"]==nxt: nxt_idx=i; break
    try: cur_dist=float(rs[cur_idx]["distance_from_source_km"])
    except: cur_dist=0
    try: dest_dist=float(rs[-1]["distance_from_source_km"])
    except: dest_dist=cur_dist+100
    return max(5.0,dest_dist-cur_dist), max(1,len(rs)-1-cur_idx)

def _features(number,state):
    distance,stops=_route_context(number,state); speed=float(state.get("current_speed",60)); scheduled=max(10,distance/max(speed,30)*60)
    return {"current_delay":state.get("current_delay",0),"current_speed":speed,"distance_remaining":distance,"scheduled_remaining_time":scheduled,"historical_average_section_time":scheduled,"number_of_stops_remaining":stops,"congestion_level":state.get("congestion_level",0),"rainfall":state.get("rainfall",0),"previous_station_delay":state.get("previous_station_delay",state.get("current_delay",0)),"dwell_time":state.get("dwell_time",2),"speed_restriction":state.get("speed_restriction",0),"signal_delay":state.get("signal_delay",0),"unscheduled_halt":int(bool(state.get("unscheduled_halt",False))),"track_congestion":state.get("track_congestion",0),"hour":datetime.now().hour}

def _make(number,state,features,remaining,now):
    eta=now+timedelta(minutes=remaining); scheduled=features["scheduled_remaining_time"]+float(state.get("current_delay",0)); sched_eta=now+timedelta(minutes=scheduled)
    return {"train_number":str(number),"current_station":state.get("current_station"),"next_station":state.get("next_station"),"current_speed":float(state.get("current_speed",60)),"current_delay":state.get("current_delay",0),"predicted_remaining_minutes":round(remaining,1),"predicted_eta":eta.isoformat(),"scheduled_eta":sched_eta.isoformat(),"eta_difference_minutes":round((eta-sched_eta).total_seconds()/60,1),"model_features":features,"timestamp":now.isoformat()}

def predict(train_number):
    state=get_train_state(train_number)
    if not state:return None
    features=_features(train_number,state); remaining=predict_eta(features); return _make(train_number,state,features,remaining,datetime.now(timezone.utc))

def predict_many(states=None):
    states=states if states is not None else all_train_states(); items=[]; nums=[]; features=[]
    for number,state in states.items():
        nums.append(number); features.append(_features(number,state))
    values=predict_eta_batch(features); now=datetime.now(timezone.utc)
    for n,s,f,v in zip(nums,states.values(),features,values): items.append(_make(n,s,f,v,now))
    return {str(i["train_number"]):i for i in items}
