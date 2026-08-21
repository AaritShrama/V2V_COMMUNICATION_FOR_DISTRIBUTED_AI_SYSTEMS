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
    
    prompt = f"""Analyze this traffic camera image. Identify hazards, obstacles, or accidents.
    Location: LAT {lat}, LNG {lng}. Time: {datetime.now(timezone.utc).isoformat()}
    
    RULES:
    - vehicle_id MUST be exactly "Vehicle_A_Node".
    - If you see a person, fallen bicycle, or crash, set event_type to "emergency" and risk_level to "CRITICAL".
    - description MUST be a single short sentence explaining the hazard.
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