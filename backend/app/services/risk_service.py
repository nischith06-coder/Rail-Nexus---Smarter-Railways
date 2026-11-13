def risk(state):
    score = 0
    score += min(30, max(0, float(state.get("current_delay", 0))) * 1.5)
    score += min(20, float(state.get("congestion_level", 0)) * 6)
    score += min(20, float(state.get("track_congestion", 0)) * 5)
    score += min(15, float(state.get("signal_delay", 0)) * 3)
    if state.get("unscheduled_halt"):
        score += 15
    if float(state.get("speed_restriction", 0)) > 0:
        score += 8
    if score >= 60: level = "CRITICAL"
    elif score >= 40: level = "HIGH"
    elif score >= 20: level = "MEDIUM"
    else: level = "LOW"
    return {"level": level, "score": round(score, 1)}
