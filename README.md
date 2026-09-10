# RailNexus — Smarter Railways

SIH26028 prototype for Dynamic Forecast of Expected Time of Arrival (ETA) for Coaching Trains.

## One-click Windows demo

1. Install Python 3.10+.
2. Double-click `start_railnexus.bat`.
3. The launcher creates the environment, installs backend packages, prepares the 2,000-train prototype fleet, starts FastAPI, starts the simulator, and opens the dashboard.
4. Dashboard: `http://127.0.0.1:8000/`

Node.js, npm, Cursor and Vite are **not required** for this one-click version. The production-style React source remains under `frontend/src/` for future development, while `frontend/static/index.html` is the zero-dependency demo dashboard served directly by FastAPI.

## What is included
- 2,000 synthetic/prototype trains with live simulated telemetry
- ML ETA model using the defined 15 ETA features
- Dynamic ETA, delay, speed, risk and operational factors
- Live fleet table with search and pagination
- Network map with many moving simulated train markers
- Signal disruption, platform conflict and recovery scenarios
- Platform decision support
- Operational events and notifications
- Seat/coach prototype intelligence
- Network summary and cascade intelligence
- FastAPI REST API + WebSocket endpoints

## Data honesty
All 2,000-train telemetry, reservations and operational inputs in this package are synthetic/prototype data unless an authorized live source is configured. The system is decision support and does not directly control railway signalling, points, interlocking or physical trains.
