from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4
from app.state import add_event, add_notification, get_train_state, set_train_state, now_iso, get_demo_override, set_demo_override

router = APIRouter(prefix='/api/v1/operations', tags=['operations'])

OPERATIONS = [
    ('MAINTENANCE','TRACK / MAINTENANCE','Planned track maintenance / engineering work','HIGH',10),
    ('SIGNAL_CHANGE','SIGNALLING','Signal aspect change, signal failure or route setting delay','HIGH',8),
    ('PLATFORM_CHANGE','STATION OPERATIONS','Platform reassignment / platform change','MEDIUM',6),
    ('CREW_RELIEF','CREW OPERATIONS','Crew relief, meal/rest break or crew availability delay','MEDIUM',5),
    ('LOCO_INSPECTION','LOCOMOTIVE','Locomotive inspection / minor technical check','HIGH',12),
    ('SHUNTING','YARD OPERATIONS','Shunting, coupling or rake positioning movement','MEDIUM',7),
    ('BOARDING_DWELL','PASSENGER OPERATIONS','Extended boarding, alighting or passenger dwell','MEDIUM',5),
    ('TRACK_CONGESTION','NETWORK OPERATIONS','Track section congestion / conflicting train movement','HIGH',9),
    ('SPEED_RESTRICTION','TRACK / SAFETY','Temporary speed restriction for safety or engineering work','HIGH',8),
    ('UNSCHEDULED_HALT','TRAIN OPERATIONS','Unscheduled halt / operational stop','HIGH',10),
    ('LEVEL_CROSSING','FIELD OPERATIONS','Level crossing clearance / road-rail coordination delay','MEDIUM',4),
    ('POWER_ISSUE','TRACTION / POWER','Traction power or electrical operational issue','HIGH',12),
    ('WEATHER_DISRUPTION','WEATHER','Heavy rain, visibility or weather-related operating restriction','HIGH',10),
    ('SAFETY_CHECK','SAFETY OPERATIONS','Safety inspection / precautionary operational check','MEDIUM',6),
    ('YARD_CONGESTION','YARD OPERATIONS','Yard congestion affecting train departure or routing','MEDIUM',7),
]

class OperationIn(BaseModel):
    train_number: str = '12627'
    operation_type: str
    location: str = ''
    duration_minutes: int | None = None
    description: str | None = None
    severity: str | None = None
    status: str = 'ACTIVE'

@router.get('/types')
def operation_types():
    return {'operations':[{'event_type':a,'category':b,'description':c,'default_severity':d,'default_minutes':m} for a,b,c,d,m in OPERATIONS]}

@router.post('/apply')
def apply_operation(item: OperationIn):
    lookup={x[0]:x for x in OPERATIONS}
    if item.operation_type not in lookup:
        return {'error':'Unknown operation type','available':list(lookup)}
    typ,cat,default_desc,default_sev,default_min=lookup[item.operation_type]
    minutes=max(1,int(item.duration_minutes or default_min))
    st=dict(get_train_state(item.train_number) or {})
    old_delay=float(st.get('current_delay',0) or 0)
    st['current_delay']=round(old_delay+minutes,1)
    if typ in ('SIGNAL_CHANGE','TRACK_CONGESTION','SPEED_RESTRICTION'):
        st['signal_delay']=minutes if typ=='SIGNAL_CHANGE' else st.get('signal_delay',0)
        st['track_congestion']=max(int(st.get('track_congestion',0) or 0),2)
    if typ=='SPEED_RESTRICTION': st['speed_restriction']=60
    if typ=='UNSCHEDULED_HALT':
        st['unscheduled_halt']=True; st['unscheduled_halt_duration']=minutes; st['current_speed']=0
    if typ=='PLATFORM_CHANGE':
        current=st.get('platform','—'); st['platform']='PF2' if current!='PF2' else 'PF3'
    if typ in ('WEATHER_DISRUPTION',): st['rainfall']=35
    # Keep the operational impact active across the live telemetry ticks.
    persistent = get_demo_override(item.train_number)
    persistent.update({k: st[k] for k in ('current_delay','signal_delay','track_congestion','speed_restriction','unscheduled_halt','unscheduled_halt_duration','platform','rainfall') if k in st})
    if typ == 'UNSCHEDULED_HALT': persistent['current_speed'] = 0
    set_demo_override(item.train_number, persistent)
    set_train_state(item.train_number, st)
    location=item.location or f"{st.get('current_station','Current route')} → {st.get('next_station','Next section')}"
    event={'event_id':str(uuid4())[:8],'event_type':typ,'category':cat,'location':location,'description':item.description or default_desc,'severity':item.severity or default_sev,'affected_section':f"{st.get('current_station','')}–{st.get('next_station','')}",'start_time':now_iso(),'end_time':'','status':item.status,'train_number':item.train_number,'delay_minutes':minutes,'created_at':now_iso()}
    add_event(event)
    add_notification({'type':'OPERATIONAL_EVENT','train_number':item.train_number,'event_id':event['event_id'],'severity':event['severity'],'message':f"{typ.replace('_',' ')}: +{minutes} min impact at {location}",'created_at':now_iso()})
    return {'operation':event,'state':st}
