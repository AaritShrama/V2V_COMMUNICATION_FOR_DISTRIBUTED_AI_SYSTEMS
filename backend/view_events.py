from backend.app.db.session import SessionLocal
from backend.app.models.event import Event


db = SessionLocal()

try:
    events = db.query(Event).order_by(Event.id.desc()).all()

    if not events:
        print("No events found.")
    else:
        print("\n========== EVENTS ==========\n")

        for event in events:
            print(f"ID            : {event.id}")
            print(f"Vehicle       : {event.vehicle_id}")
            print(f"Event Type    : {event.event_type}")
            print(f"Object        : {event.object_type}")
            print(f"Confidence    : {event.confidence}")
            print(f"Risk          : {event.risk_level}")
            print(f"Location      : {event.latitude}, {event.longitude}")
            print(f"Description   : {event.description}")
            print(f"Recommendation: {event.recommendation}")
            print(f"Timestamp     : {event.timestamp}")
            print("-" * 50)

finally:
    db.close()