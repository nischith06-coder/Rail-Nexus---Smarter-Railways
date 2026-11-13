from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/"data"/"train_eta_dataset_clean_33_columns.csv")
features=["current_delay","current_speed","distance_remaining","scheduled_remaining_time","historical_average_section_time","number_of_stops_remaining","congestion_level","rainfall","previous_station_delay","dwell_time","speed_restriction","signal_delay","unscheduled_halt","track_congestion","hour"]
X=df[features].fillna(0)
y=df["remaining_travel_time"]
model=RandomForestRegressor(n_estimators=120,max_depth=12,random_state=42,n_jobs=-1)
model.fit(X,y)
(ROOT/"models").mkdir(exist_ok=True)
joblib.dump(model,ROOT/"models"/"eta_model.joblib")
print("Saved", ROOT/"models"/"eta_model.joblib")
