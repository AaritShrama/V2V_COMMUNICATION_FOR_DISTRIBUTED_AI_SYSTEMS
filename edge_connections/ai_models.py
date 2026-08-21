import sys
import os
import cv2
from datetime import datetime, timezone
from typing import Optional
import ollama

# System Path Fix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.schemas.semantic_message import SemanticMessage

def _run_local_vision_model(frame, lat: float, lng: float, model_name: str) -> Optional[SemanticMessage]:
    """Helper function to run any Ollama model with the strict JSON schema."""
    small_frame = cv2.resize(frame, (512, 512))
    _, buffer = cv2.imencode('.jpg', small_frame)
    image_bytes = buffer.tobytes()
    
    prompt = f"""
You are the perception and hazard-assessment AI of an autonomous vehicle.

Analyze the provided traffic-camera image carefully.

Your task is to identify ONLY hazards, obstacles, accidents, or situations
that could affect the safe movement of a vehicle.

CURRENT VEHICLE:
vehicle_id = "Vehicle_A_Node"

CURRENT LOCATION:
latitude = {lat}
longitude = {lng}

CURRENT UTC TIME:
{datetime.now(timezone.utc).isoformat()}

FOLLOW THESE RULES STRICTLY:

1. VEHICLE ID
- vehicle_id MUST be exactly "Vehicle_A_Node".

2. VISUAL EVIDENCE
- Base your answer ONLY on what is visibly supported by the image.
- Do not invent objects, people, vehicles, road conditions, or events.
- Do not assume something is dangerous merely because it is unusual.
- If an object is partially visible, only report it if there is sufficient visual evidence.

3. HAZARD DETECTION
Look specifically for:
- pedestrians in or near the vehicle's path
- fallen pedestrians
- cyclists or fallen bicycles
- motorcycles in dangerous positions
- vehicle crashes or collisions
- overturned vehicles
- stopped or stranded vehicles
- vehicles blocking lanes
- road debris
- large objects on the road
- potholes or severe road damage
- road obstacles
- unusual lane blockage
- dangerous traffic situations
- fire, smoke, or visible accident aftermath

4. EMERGENCY CLASSIFICATION
Set event_type to "emergency" AND risk_level to "CRITICAL"
when the image clearly shows:
- a crash
- an overturned vehicle
- a fallen person
- a person apparently injured or lying in the roadway
- a fallen bicycle/cyclist creating an immediate hazard
- fire or another clearly life-threatening road situation

5. RISK LEVEL
Evaluate the immediate danger to another approaching vehicle.

Use:
- "CRITICAL" = immediate severe danger or possible life-threatening situation
- "HIGH" = serious hazard requiring immediate caution or avoidance
- "MEDIUM" = noticeable hazard but not immediately life-threatening
- "LOW" = minor obstacle or low-risk abnormal situation

6. RECOMMENDATION
Give a short, practical action for the receiving vehicle.

Examples:
- "slow_down"
- "stop_if_necessary"
- "change_lane_if_safe"
- "avoid_obstacle"
- "maintain_caution"
- "prepare_to_stop"

Do NOT recommend an action that cannot be reasonably inferred from the image.

7. DESCRIPTION
- description MUST be exactly ONE short sentence.
- Clearly state the visible hazard.
- Do not include speculation.
- Do not include unnecessary visual details.

GOOD:
"An overturned truck is blocking the right lane."

BAD:
"I think there may have been an accident involving a truck."

8. LOCATION
Use the provided latitude and longitude exactly:
latitude = {lat}
longitude = {lng}

9. CONFIDENCE
Set confidence between 0.0 and 1.0 based on visual certainty.

Use:
- 0.90–1.00 = hazard is clearly visible
- 0.75–0.89 = hazard is likely and reasonably clear
- 0.50–0.74 = uncertain visual evidence
- below 0.50 = insufficient evidence

10. CONSERVATIVE BEHAVIOR
False positives are dangerous.
Do not classify normal traffic, parked vehicles, shadows,
road markings, advertisements, or ordinary pedestrians
as hazards unless they create a clear safety risk.

11. OUTPUT
Return ONLY the JSON object required by the SemanticMessage schema.
Do not return Markdown.
Do not return explanations.
Do not return code fences.
Do not add extra fields.
"""
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt, 'images': [image_bytes]}],
            options={"temperature": 0.1,
                     "num_predict":256},
            format=SemanticMessage.model_json_schema() 
        )
        output = response['message']['content']
        return SemanticMessage.model_validate_json(output)
    except Exception as e:
        print(f"\n[AI Error] {model_name} failed: {e}")
        return None

# --- YOUR SWAPPABLE AI MODELS ---

def analyze_with_moondream(frame, lat, lng):
    return _run_local_vision_model(frame, lat, lng, "moondream")

def analyze_with_llava(frame, lat, lng):
    return _run_local_vision_model(frame, lat, lng, "llava")

def analyze_with_paligemma(frame, lat, lng):
    return _run_local_vision_model(frame, lat, lng, "paligemma")