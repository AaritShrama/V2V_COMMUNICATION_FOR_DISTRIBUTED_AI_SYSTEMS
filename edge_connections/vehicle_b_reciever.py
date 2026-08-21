import sys
import os
import json 
import requests 
import paho.mqtt.client as mqtt

# --- 1. SYSTEM PATH FIX ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.schemas.semantic_message import SemanticMessage

# --- 2. NETWORK SETUP ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 8000  # WebSockets port to bypass Wi-Fi blocks
MQTT_TOPIC = "intelligence/+/hazard"

# --- 3. MQTT CALLBACKS ---
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"\n[Vehicle B] Connected to HiveMQ Network (Code: {reason_code})")
    client.subscribe(MQTT_TOPIC)
    print(f"[Vehicle B] Listening for hazard broadcasts on: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    """Triggered instantly whenever Vehicle A broadcasts a hazard."""
    print("\n" + "!"*50)
    print("🚨 [WARNING] V2V ALERT RECEIVED 🚨")

    try:
        # Decode the raw JSON string
        payload_str = msg.payload.decode('utf-8')

        # Validate the incoming data using the backend schema
        alert = SemanticMessage.model_validate_json(payload_str)

        # Display the alert on Vehicle B's dashboard
        print(f"   From Node : {alert.vehicle_id}")
        print(f"   Event     : {alert.event_type.upper()}")
        print(f"   Risk Level: {alert.risk_level}")
        print(f"   Detail    : {alert.description}")
        print(f"   Action    : {alert.recommendation}")

        # --- DATABASE FORWARDING ---
        payload_dict = json.loads(payload_str)
        response = requests.post("http://localhost:8000/events", json=payload_dict)
        print(f"   Cloud Sync: Status {response.status_code}")
        # -------------------------------

    except Exception as e:
        print(f"[Error] Failed to parse or sync data: {e}")

    print("!"*50 + "\n")


# --- 4. START RECEIVER LOOP ---
print("[System] Booting Vehicle B Receiver Node...")

client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets") # type: ignore
client_mqtt.on_connect = on_connect
client_mqtt.on_message = on_message

client_mqtt.connect(MQTT_BROKER, MQTT_PORT)

try:
    client_mqtt.loop_forever()
except KeyboardInterrupt:
    print("\n[System] Shutting down Vehicle B.")
    client_mqtt.disconnect()