def send_alert(risk_score: float, location="Sector A3"):
    pct = risk_score * 100
    if risk_score >= 0.7:
        print(f"🚨 HIGH Risk {pct:.1f}% at {location} — Evacuate immediately!")
    elif risk_score >= 0.4:
        print(f"⚠️ Moderate Risk {pct:.1f}% at {location} — Monitor closely.")
    else:
        print(f"✅ Low Risk {pct:.1f}% at {location} — Safe operations.")

if __name__ == "__main__":
    send_alert(0.82, "Sector B1")
