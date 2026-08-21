import cv2
import time
import h3
import paho.mqtt.client as mqtt
import os ; 
# --- 1. MODULAR IMPORTS ---
# Notice we removed the YOLO/OpenCV imports completely!
from ai_models import analyze_with_moondream as active_ai_model

# --- 2. SYSTEM SETUP ---
CURRENT_LAT = 37.7750
CURRENT_LNG = -122.4190
target_hex = h3.latlng_to_cell(CURRENT_LAT, CURRENT_LNG, res=9)
topic = f"intelligence/{target_hex}/hazard"
current_folder = os.path.dirname(os.path.abspath(__file__))
video_source = os.path.join(current_folder, "test.mp4")
# --- 3. NETWORK & SENSORS ---
# Using the WebSockets fix so the hackathon Wi-Fi doesn't block you!
client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets") # type: ignore
client_mqtt.connect("broker.hivemq.com", 8000)
client_mqtt.loop_start()

# Open the video file (or change "test.mp4" to 0 for your webcam)
cap = cv2.VideoCapture(video_source)

# --- 4. TIMER SETUP ---
last_ai_time = 0
ai_interval = 2.0  # Exactly 2 seconds between AI scans

# --- 5. MAIN VEHICLE LOOP ---
print("\n[System] Starting Time-Based Edge AI Pipeline...")

try:
    while True:
        ret, frame = cap.read()
        if not ret: 
            print("[System] Video ended. Looping back to start...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loops the video for testing
            continue
            
        current_time = time.time()
        
        # --- THE 2-SECOND TRIGGER ---
        if current_time - last_ai_time >= ai_interval:
            print(f"\n[{time.strftime('%H:%M:%S')}] ⏱️ 2 Seconds passed! Scanning frame...")
            
            # Send the current frame to Moondream (or whichever model is imported)
            intelligence = active_ai_model(frame, CURRENT_LAT, CURRENT_LNG)
            
            if intelligence:
                print(f"   -> Result: {intelligence.event_type.upper()} | Risk: {intelligence.risk_level}")
                print(f"   -> Detail: {intelligence.description}")
                
                # Broadcast only if it is an actual hazard
                if intelligence.event_type != "normal":
                    print(f"   -> [MQTT] Broadcasting threat to Hex: {target_hex}")
                    client_mqtt.publish(topic, intelligence.model_dump_json())
                else:
                    print("   -> [MQTT] Scene safe. No broadcast needed.")
                    
            last_ai_time = time.time() # Reset the timer

        # --- DISPLAY DASHBOARD ---
        # The video will continue playing smoothly while waiting for the next 2-second mark
        cv2.imshow("Vehicle A - 2-Second Interval Scan", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break
            
finally:
    cap.release()
    cv2.destroyAllWindows()
    client_mqtt.loop_stop()
    client_mqtt.disconnect()
    print("[System] Shutting down.")