# RailNexus ETA Model Card

## Purpose
RailNexus uses a Random Forest regression model to estimate **remaining travel time** for the selected train from operational telemetry.

## Runtime features
The predictor consumes exactly 15 features:
1. current_delay
2. current_speed
3. distance_remaining
4. scheduled_remaining_time
5. historical_average_section_time
6. number_of_stops_remaining
7. congestion_level
8. rainfall
9. previous_station_delay
10. dwell_time
11. speed_restriction
12. signal_delay
13. unscheduled_halt
14. track_congestion
15. hour

## Training data
The included ETA dataset is synthetic/demo data generated for the hackathon prototype. It is **not official railway operational data**.

## Limitations
- The model is a prototype and has not been validated on production railway telemetry.
- Weather, signalling, track and timetable inputs are simulated unless an authorized live integration is configured.
- Historical data is used for training; it is not injected into each runtime prediction as raw rows.
- The prediction should be treated as decision support, not a safety-critical control command.

## Operational framing
Platform recommendations and network decisions are simulated operational decision support. RailNexus does not directly control signalling, points, interlocking or physical trains.
