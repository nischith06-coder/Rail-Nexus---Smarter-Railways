from fastapi import APIRouter
from app.state import get_train_state, set_train_state, add_notification, now_iso, set_demo_override, clear_demo_override
from app.services.eta_service import predict

router = APIRouter(prefix='/api/v1/demo', tags=['demo'])

BASE = {
    'current_station': 'KSR Bengaluru', 'next_station': 'Tumakuru',
    'latitude': 12.9716, 'longitude': 77.5946, 'current_speed': 95,
    'current_delay': 5, 'congestion_level': 1, 'rainfall': 0,
    'signal_delay': 0, 'unscheduled_halt': False, 'unscheduled_halt_duration': 0,
    'track_congestion': 1, 'speed_restriction': 0, 'platform': 'PF3',
    'previous_station_delay': 5, 'dwell_time': 2,
}

SCENARIOS = {
    'normal': {'current_speed': 95, 'current_delay': 5, 'congestion_level': 1, 'signal_delay': 0, 'track_congestion': 1, 'speed_restriction': 0, 'platform': 'PF3', 'platform_conflict': False},
    'signal': {'current_speed': 45, 'current_delay': 11, 'congestion_level': 2, 'signal_delay': 15, 'track_congestion': 2, 'speed_restriction': 60, 'platform': 'PF3', 'platform_conflict': False},
    'conflict': {'current_speed': 45, 'current_delay': 11, 'congestion_level': 3, 'signal_delay': 15, 'track_congestion': 3, 'speed_restriction': 60, 'platform': 'PF3', 'platform_conflict': True},
    'recovery': {'current_speed': 80, 'current_delay': 8, 'congestion_level': 1, 'signal_delay': 4, 'track_congestion': 1, 'speed_restriction': 80, 'platform': 'PF2', 'platform_conflict': False},
}

@router.get('/scenarios')
def scenarios():
    return {'scenarios': list(SCENARIOS), 'train_number': '12627'}

@router.post('/scenario/{name}')
def apply_scenario(name: str):
    if name not in SCENARIOS:
        return {'error': 'Unknown scenario', 'available': list(SCENARIOS)}
    if name == 'normal':
        clear_demo_override('12627')
    else:
        set_demo_override('12627', SCENARIOS[name])
    current = dict(BASE)
    current.update(SCENARIOS[name])
    current['train_number'] = '12627'
    current['timestamp'] = now_iso()
    set_train_state('12627', current)
    messages = {
        'normal': 'Demo reset: normal running conditions restored.',
        'signal': 'Demo event: simulated signal issue introduced on Tumakuru–Arsikere.',
        'conflict': 'Demo conflict: simulated platform contention detected at KSR Bengaluru.',
        'recovery': 'Demo recovery: speed restored and platform plan moved to PF2.',
    }
    add_notification({'type': 'DEMO_SCENARIO', 'train_number': '12627', 'message': messages[name], 'created_at': now_iso()})
    return {'scenario': name, 'state': current, 'eta': predict('12627')}
