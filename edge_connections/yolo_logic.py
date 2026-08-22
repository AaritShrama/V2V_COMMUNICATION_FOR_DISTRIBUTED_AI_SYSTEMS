import cv2
from ultralytics import YOLO

class HazardDetector:
    def __init__(self):
        print("\n[System] Loading YOLOv8 Reflex Engine...")
        self.yolo_model = YOLO('yolov8n.pt') 
    def scan_for_hazards(self, frame):
        """Scans frame for people/bikes. Returns the drawn frame and a boolean."""
        results = self.yolo_model(frame, stream=True, verbose=False)
        hazard_detected = False
        for result in results:
            for box in result.boxes: # type: ignore
                class_id = int(box.cls[0])
                # Class 0 = Person, Class 1 = Bicycle
                if class_id in [0, 1]: 
                    hazard_detected = True
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Draw warning box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, "HAZARD DETECTED", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        return frame, hazard_detected