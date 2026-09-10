# RailNexus — 3 Minute SIH Demo Runbook

## 1. Start
Run `start_railnexus.bat` on Windows. The launcher creates the Python environment, installs backend/frontend dependencies, prepares demo data, starts FastAPI + simulator, and opens the web UI.

## 2. Normal state
Open **LIVE DASHBOARD**. Train 12627 is the selected train. Point out:
- live simulated position on the map
- current speed and delay
- dynamic ETA
- risk level
- 15-feature ETA model context

## 3. Inject disruption
Use **SIGNAL** under DEMO SCENARIO or click **Inject Signal Issue**.
Explain that the simulated signal event increases operational friction, lowers speed and changes ETA.

## 4. Show operations
Open **OPERATIONS** and show the active signal event. This demonstrates human/staff event intake rather than relying only on historical data.

## 5. Resolve platform conflict
Open **PLATFORM CONTROL** and click **Evaluate 12627**. Show the KEEP / WAIT / MOVE alternatives and the simulated recommendation.

## 6. Passenger impact
Open **STATION VIEW** to show the platform display. Then open **SEAT AVAILABILITY** to show coach/seat status and reservation segments.

## 7. Network view
Open **NETWORK INTELLIGENCE** and explain the cascade: train delay → platform occupancy → another train affected → downstream network risk.

## 8. Recovery
Return to dashboard and select **RECOVER**. Explain how improved speed and a changed platform plan reduce the simulated operational impact.

## 9. What-if
Open **WHAT-IF SIMULATOR**, increase signal delay or track congestion, and click **Simulate Impact**. Compare baseline vs scenario ETA.

### Important wording for judges
Say **"AI-driven operational decision support in a simulated environment"**, not "AI directly controls railway signalling." The included telemetry, reservations and route/timetable records are prototype/demo data unless an authorized live source is connected.
