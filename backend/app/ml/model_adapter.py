from pathlib import Path
import math

MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "eta_model.joblib"
FEATURE_ORDER = [
    "current_delay", "current_speed", "distance_remaining",
    "scheduled_remaining_time", "historical_average_section_time",
    "number_of_stops_remaining", "congestion_level", "rainfall",
    "previous_station_delay", "dwell_time", "speed_restriction",
    "signal_delay", "unscheduled_halt", "track_congestion", "hour"
]

_model = None
def load_model():
    global _model
    if _model is not None:
        return _model
    if MODEL_PATH.exists():
        try:
            import joblib
            _model = joblib.load(MODEL_PATH)
        except Exception:
            _model = None
    return _model

def predict_eta(features: dict) -> float:
    model = load_model()
    values = [float(features.get(k, 0)) for k in FEATURE_ORDER]
    if model is not None:
        try:
            import pandas as pd
            x = pd.DataFrame([values], columns=FEATURE_ORDER)
            return max(1.0, float(model.predict(x)[0]))
        except Exception:
            x = [values]
            return max(1.0, float(model.predict(x)[0]))

    # Safe deterministic fallback for demo operation before model training.
    speed = max(20.0, float(features.get("current_speed", 60)))
    distance = max(1.0, float(features.get("distance_remaining", 100)))
    base = distance / speed * 60
    delay = float(features.get("current_delay", 0))
    congestion = float(features.get("congestion_level", 0)) * 2.0
    signal = float(features.get("signal_delay", 0)) * 2.0
    halt = float(features.get("unscheduled_halt", 0)) * 8.0
    restriction = 0
    limit = float(features.get("speed_restriction", 0))
    if limit > 0 and limit < speed:
        restriction = (speed - limit) / max(speed, 1) * base
    return max(1.0, base + delay * 0.25 + congestion + signal + halt + restriction)

def predict_eta_batch(features_list: list[dict]) -> list[float]:
    """Predict a fleet in one model call; avoids one sklearn call per train."""
    model = load_model()
    values = [[float(f.get(k, 0)) for k in FEATURE_ORDER] for f in features_list]
    if not values:
        return []
    if model is not None:
        try:
            import pandas as pd
            x = pd.DataFrame(values, columns=FEATURE_ORDER)
            return [max(1.0, float(v)) for v in model.predict(x)]
        except Exception:
            try:
                return [max(1.0, float(v)) for v in model.predict(values)]
            except Exception:
                pass
    return [predict_eta(f) for f in features_list]
