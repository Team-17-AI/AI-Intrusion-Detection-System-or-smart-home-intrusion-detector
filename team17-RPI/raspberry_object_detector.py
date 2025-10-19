import cv2
import torch
import torch.nn.modules.container as container

from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel

import streamlit as st
from picamera2 import Picamera2

# allowlist for safe weights-only loading
torch.serialization.add_safe_globals([
    DetectionModel,
    container.Sequential,
])

# how long (s) to keep object detection “active” after a PIR trigger
DETECTION_ACTIVE_DURATION_S = 10

@st.cache_resource
def load_yolo_model(model_path: str = "./yolo11n_ncnn_model") -> YOLO:
    """Ensure we have an NCNN‐exported model, then load it."""
    try:
        # now load the NCNN version
        ncnn_model = YOLO(model_path)
        st.success(f"🔋 Loaded NCNN model from {model_path}")
        return ncnn_model

    except Exception as e:
        st.error(f"Error loading NCNN YOLO model: {e}")
        return None

def init_camera():
    """Set up the PiCamera2 at a smaller resolution for speed."""
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.set_controls({"FrameRate": 5})
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()
    return picam2

def detect_objects(frame, model, confidence_threshold: float = 0.50):
    """
    Run inference on `frame` with the NCNN-backed YOLO model.
    Returns list of detections and a flag if a person was seen.
    """
    if model is None:
        return [], False

    # this will run via NCNN runtime
    results = model(frame)
    detections = []
    person_found = False

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            name = model.names[cls]
            if conf >= confidence_threshold:
                detections.append({
                    "class_name": name,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2]
                })
                if name == "person":
                    person_found = True

    if detections:
        classes = {d["class_name"] for d in detections}
        print(f"Detected: {', '.join(classes)} (≥{confidence_threshold})")
    return detections, person_found

def draw_detections(frame, detections):
    """Draw boxes & labels on the image."""
    img = frame.copy()
    color_map = {
        'person': (0,255,0),
        'dog':    (255,165,0),
        'cat':    (255,0,255),
        'default':(0,255,255),
    }

    for det in detections:
        x1,y1,x2,y2 = det["bbox"]
        cls = det["class_name"]
        color = color_map.get(cls, color_map['default'])
        label = f"{cls}: {det['confidence']:.2f}"
        cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
        (w,h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(img, (x1, y1-h-10), (x1+w, y1), color, -1)
        cv2.putText(img, label, (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
    return img
