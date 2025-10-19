# motion_detector.py
import streamlit as st
import time
from gpiozero import MotionSensor

# Duration for which object detection remains active after PIR trigger
DETECTION_ACTIVE_DURATION_S = 10  # seconds

# --- use MotionSensor on BCM 21 ---
pir = MotionSensor(21)

def init_motion_state():
    if 'pir_triggered_time' not in st.session_state:
        st.session_state.pir_triggered_time = 0
    if 'object_detection_active' not in st.session_state:
        st.session_state.object_detection_active = False

def simulate_pir_trigger_button():
    """
    Checks the PIR sensor state via gpiozero and manages the detection window.
    Returns True if the detection window should be active.
    """
    init_motion_state()

    # gpiozero gives .is_active = True while motion is detected
    if pir.is_active:
        st.session_state.pir_triggered_time = time.time()
        st.session_state.object_detection_active = True
        st.toast("Motion Detected! Activating Object Detection...")
        
    if st.session_state.object_detection_active:
        elapsed = time.time() - st.session_state.pir_triggered_time
        if elapsed < DETECTION_ACTIVE_DURATION_S:
            return True
        else:
            st.session_state.object_detection_active = False
            st.toast("Object detection window closed.")
            return False

    return False

def is_object_detection_active():
    """Checks if object detection should currently be running."""
    init_motion_state()
    return st.session_state.object_detection_active

def cleanup():
    """Cleanup gpiozero sensor on exit."""
    pir.close()
