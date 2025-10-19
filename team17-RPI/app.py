# app.py - Raspberry Pi 5 Compatible Intrusion Detection System
import streamlit as st
import cv2
import os
os.environ["STREAMLIT_WATCHDOG"] = "false"
import time
from PIL import Image
import json
from datetime import datetime
import csv
import psutil

# Import modular components
from raspberry_motion_detector import simulate_pir_trigger_button, is_object_detection_active, init_motion_state, DETECTION_ACTIVE_DURATION_S
from raspberry_object_detector import load_yolo_model, detect_objects, draw_detections
from telegram_notifier import send_telegram_animation, init_telegram_state, can_send_notification
from utils import save_sequence_as_jpgs, create_gif_from_frames, NUM_JPG_FRAMES_TO_SAVE, NUM_GIF_FRAMES

#PICAMERA_AVAILABLE = False
# Try to import picamera2 for Raspberry Pi camera support
try:
    from picamera2 import Picamera2
    import numpy as np
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    print("Warning: picamera2 not available. Falling back to OpenCV camera.")

# --- Page Configuration ---
st.set_page_config(page_title="Intrusion Detection System", layout="wide")

# --- Constants ---
YOLO_MODEL_PATH = "yolo11n.pt"
CONFIG_FILE = "config.json"
DETECTIONS_FILE = "previous_detections.json"
MAX_PREVIOUS_DETECTIONS = 5
SNAPSHOT_DIR = "snapshots"
DETECTION_RESET_TIME = 1  # seconds
SLEEP_INTERVAL_S = 0.05  # Change this value for each test: e.g., 0.5, 0.25, etc.



# Ensure snapshots directory exists
if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

def load_config():
    """Load configuration from config file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.warning("Config file is corrupted. Using default values.")
            return {}
    return {}

def save_config(data):
    """Save configuration to config file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_previous_detections():
    """Load previous detections from file."""
    if os.path.exists(DETECTIONS_FILE):
        try:
            with open(DETECTIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_previous_detections(detections):
    """Save previous detections to file."""
    try:
        with open(DETECTIONS_FILE, 'w') as f:
            json.dump(detections, f, indent=4)
    except Exception as e:
        print(f"Error saving detections: {e}")

class RaspberryPiCamera:
    """Wrapper class for Raspberry Pi camera using picamera2"""
    def __init__(self):
        if not PICAMERA_AVAILABLE:
            raise ImportError("picamera2 not available")
        
        self.picam = Picamera2()
        # Configure camera for video capture
        config = self.picam.create_video_configuration(
            main={"size": (640, 480)},
            lores={"size": (320, 240)},
            display="lores"
        )
        self.picam.configure(config)
        self.is_opened = False
    
    def start(self):
        """Start the camera"""
        try:
            self.picam.start()
            self.is_opened = True
            return True
        except Exception as e:
            print(f"Error starting Raspberry Pi camera: {e}")
            return False
    
    def read(self):
        """Read a frame from the camera"""
        if not self.is_opened:
            return False, None
        
        try:
            # Capture frame as numpy array
            frame = self.picam.capture_array()
            # Convert from RGB to BGR for OpenCV compatibility
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return True, frame_bgr
        except Exception as e:
            print(f"Error reading from Raspberry Pi camera: {e}")
            return False, None
    
    def release(self):
        """Release the camera completely."""
        if self.is_opened:
            try:
                # Stop the stream
                self.picam.stop()
            except Exception as e:
                print(f"Error stopping camera: {e}")
            try:
                # Close & de-configure the device
                self.picam.close()
            except Exception as e:
                print(f"Error closing camera: {e}")
            # give the driver a moment
            time.sleep(0.5)
            self.is_opened = False
    
    def isOpened(self):
        """Check if camera is opened"""
        return self.is_opened

def initialize_camera():
    """Initialize camera - try Raspberry Pi camera first, then fallback to USB/webcam"""
    camera = None
    camera_type = "Unknown"
    
    # Try Raspberry Pi camera first
    if PICAMERA_AVAILABLE:
        try:
            camera = RaspberryPiCamera()
            if camera.start():
                camera_type = "Raspberry Pi Camera"
                st.success("✅ Raspberry Pi camera initialized successfully!")
            else:
                camera = None
        except Exception as e:
            print(f"Failed to initialize Raspberry Pi camera: {e}")
            camera = None
    
    # Fallback to USB/webcam
    if camera is None:
        try:
            camera = cv2.VideoCapture(0)
            if camera.isOpened():
                camera_type = "USB/Webcam"
                st.info("📹 Using USB/Webcam camera")
            else:
                camera.release()
                camera = None
        except Exception as e:
            print(f"Failed to initialize USB camera: {e}")
    
    return camera, camera_type

# --- Initialize Session State ---
config = load_config()

# System State
if 'system_running' not in st.session_state:
    st.session_state.system_running = False
if 'camera' not in st.session_state:
    st.session_state.camera = None
if 'camera_type' not in st.session_state:
    st.session_state.camera_type = "Unknown"

# Model
if 'yolo_model' not in st.session_state:
    st.session_state.yolo_model = load_yolo_model(YOLO_MODEL_PATH)

# Telegram Config
if 'telegram_bot_token' not in st.session_state:
    st.session_state.telegram_bot_token = config.get("telegram_bot_token", "")
if 'telegram_chat_id' not in st.session_state:
    st.session_state.telegram_chat_id = config.get("telegram_chat_id", "")
if 'telegram_notifications_enabled' not in st.session_state:
    st.session_state.telegram_notifications_enabled = config.get("telegram_notifications_enabled", True)

# Detections History & Frame Collection
if 'previous_detections' not in st.session_state:
    st.session_state.previous_detections = load_previous_detections()
if 'collecting_frames_for_event' not in st.session_state:
    st.session_state.collecting_frames_for_event = False
if 'current_event_frames' not in st.session_state:
    st.session_state.current_event_frames = []
if 'detection_event_processed' not in st.session_state:
    st.session_state.detection_event_processed = False

init_motion_state()
init_telegram_state()

# --- UI Elements ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

col1, col2 = st.columns([4, 1])

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Camera info
    st.subheader("📹 Camera")
    if PICAMERA_AVAILABLE:
        st.success("✅ Raspberry Pi Camera Support Available")
    else:
        st.warning("⚠️ Raspberry Pi Camera not available - using USB/Webcam")

    st.subheader("🚦 System Control")
    if not st.session_state.system_running:
        if st.button("🚀 Start System", use_container_width=True):
            if st.session_state.yolo_model is None:
                st.error("YOLO Model not loaded. Cannot start.")
            else:
                st.session_state.system_running = True
                st.session_state.detection_event_processed = False
                st.session_state.collecting_frames_for_event = False
                st.session_state.current_event_frames = []
                st.rerun()
    else:
        if st.button("🛑 Stop System", use_container_width=True):
            st.session_state.system_running = False
            st.rerun()

    st.subheader("🔔 Telegram Notifications")
    st.session_state.telegram_notifications_enabled = st.toggle(
        "Enable Telegram Notifications",
        value=st.session_state.telegram_notifications_enabled,
        help="Turn Telegram notifications on or off."
    )
    st.session_state.telegram_bot_token = st.text_input(
        "Bot Token", 
        value=st.session_state.telegram_bot_token, 
        type="password", 
        disabled=not st.session_state.telegram_notifications_enabled
    )
    st.session_state.telegram_chat_id = st.text_input(
        "Chat ID", 
        value=st.session_state.telegram_chat_id, 
        disabled=not st.session_state.telegram_notifications_enabled
    )
    
    if st.button("💾 Save Telegram Config", use_container_width=True):
        save_config({
            "telegram_bot_token": st.session_state.telegram_bot_token,
            "telegram_chat_id": st.session_state.telegram_chat_id,
            "telegram_notifications_enabled": st.session_state.telegram_notifications_enabled
        })
        st.success("Telegram configuration saved!")

# reset once the detection window closes
    if not is_object_detection_active() and st.session_state.detection_event_processed:
        st.session_state.detection_event_processed = False
        st.session_state.collecting_frames_for_event = False
        st.session_state.current_event_frames = []

    st.markdown("---")
    with st.expander("📜 Previous Detections", expanded=True):
        if not st.session_state.previous_detections:
            st.caption("No detections recorded yet.")
        else:
            for i, det_event in enumerate(st.session_state.previous_detections):
                st.markdown(f"**Event {len(st.session_state.previous_detections) - i}: {det_event['timestamp']}**")
                st.markdown(f"*{det_event['caption']}*")
                if det_event.get("gif_path") and os.path.exists(det_event["gif_path"]):
                    st.image(det_event["gif_path"], caption="Detected Event GIF") 
                elif det_event.get("representative_jpg_path") and os.path.exists(det_event["representative_jpg_path"]):
                    st.image(det_event["representative_jpg_path"], caption="Representative Frame")
                else:
                    st.caption("Media not found.")
                if i < len(st.session_state.previous_detections) - 1:
                    st.markdown("---")

# --- Main Application Logic ---
frame_placeholder = col1.empty()
status_placeholder = col2.empty()

if st.session_state.yolo_model is None:
    status_placeholder.error("YOLOv5 Model could not be loaded. Check path and dependencies.")
    st.stop()

if st.session_state.system_running:
    # Initialize camera if not already done
    if not st.session_state.camera or not st.session_state.camera.isOpened():
        if st.session_state.camera:
            st.session_state.camera.release()
        
        st.session_state.camera, st.session_state.camera_type = initialize_camera()
        
        if not st.session_state.camera or not st.session_state.camera.isOpened():
            status_placeholder.error("Could not initialize camera.")
            st.session_state.system_running = False
            st.rerun()

    camera = st.session_state.camera
    
    frame_time_prev = time.time()

    while st.session_state.system_running and camera and camera.isOpened():
        loop_start_time = time.time()
        
        # Reset detection state after cooldown
        if "last_detection_time" in st.session_state:
            if time.time() - st.session_state.last_detection_time > DETECTION_RESET_TIME:
                st.session_state.detection_event_processed = False

        
        # you only read the PIR once in the sidebar, so nothing happens here
        # 1) Poll the PIR sensor right here so it fires continuously
        
        pir_triggered = simulate_pir_trigger_button()

        ret, frame_bgr = camera.read()
        if not ret:
            status_placeholder.error("Cannot read frame from camera. Stopping system.")
            st.session_state.system_running = False
            break

        # 2) Update your status based on the fresh PIR reading
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        display_frame = frame_rgb.copy()
        # … rest of your object-detection code …

        status_message_main = "👀 Monitoring..."
        detection_active_status_main = "Inactive"
        pir_is_currently_active = is_object_detection_active()

        if pir_is_currently_active:
            detection_active_status_main = f"Active ({DETECTION_ACTIVE_DURATION_S}s)"
            
            if not st.session_state.detection_event_processed:
                status_message_main = "🔍 Detecting Objects..."
                detections, person_found = detect_objects(frame_bgr, st.session_state.yolo_model)
                
                #===Baseline Profiling Logging ===
                log_path = "project_test_enhanced.csv"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                inference_time = loop_start_time - frame_time_prev
                frame_time_prev = loop_start_time
                fps = 1 / inference_time if inference_time > 0 else 0
                cpu_percent = psutil.cpu_percent(interval=None)
                ram_percent = psutil.virtual_memory().percent
                
                
                try:
                    temp_output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
                    temperature = float(temp_output.replace("temp=", "").replace("'C\n", ""))
                except Exception:
                    temperature = None

                # Extract detections safely
                try:
                    detection_classes = []
                    if detections:
                        for det in detections:
                            class_name = det.get("class_name", "unknown")
                            detection_classes.append(class_name)
                except Exception as outer:
                    print(f"[!] Error in detection_classes loop: {outer}")
                    detection_classes = []

                person_detected = "person" in detection_classes
                num_detections = len(detection_classes)

                log_row = [
                    timestamp, inference_time, fps,
                    cpu_percent, ram_percent, temperature,
                    person_detected, num_detections, SLEEP_INTERVAL_S
                ]


                try:
                    file_exists = os.path.exists(log_path)
                    with open(log_path, "a", newline="") as f:
                        writer = csv.writer(f)
                        if not file_exists:
                            writer.writerow([
                                "timestamp", "inference_time", "fps",
                                "cpu_percent", "ram_percent", "temperature",
                                "person_detected", "num_detections", "sleep_interval"
                            ])
                        writer.writerow(log_row)
                    print(f"[+] Logged: {log_row}")
                except Exception as write_error:
                    print(f"[!] Logging failed: {write_error}")
                
                # Analyze detections
                detected_classes = {det["class_name"] for det in detections}
                
                if person_found:
                    status_message_main = "👤 PERSON DETECTED!"
                    st.session_state.last_detection_time = time.time()

                elif "dog" in detected_classes or "cat" in detected_classes:
                    status_message_main = "🐾 Pet detected (dog/cat) - No security concern"
                    person_found = False  # Ensure we don't trigger alerts for pets
                
                # Always show detections in the frame
                display_frame = draw_detections(frame_rgb, detections)
                
                if person_found:
                    if not st.session_state.collecting_frames_for_event:
                        st.session_state.collecting_frames_for_event = True
                        st.session_state.current_event_frames = []
 
             
                
                elif st.session_state.collecting_frames_for_event:
                    status_message_main = "👤 Person momentarily lost, continuing frame collection..."
                else:
                    if detected_classes:
                        status_message_main = f"👁️ Detected: {', '.join(detected_classes)}"
                    else:
                        status_message_main = "👁️ Motion detected, no objects of interest found"
            else:
                status_message_main = "✅ Event processed, awaiting next PIR trigger."

            if st.session_state.collecting_frames_for_event:
                st.session_state.current_event_frames.append(frame_bgr.copy())
                status_message_main += f" (Collecting frame {len(st.session_state.current_event_frames)}/{NUM_GIF_FRAMES})"
                if len(st.session_state.current_event_frames) >= NUM_GIF_FRAMES:
                    st.session_state.collecting_frames_for_event = False
                    st.session_state.detection_event_processed = True
                    
                    first_event_frame_detections = detections if 'detections' in locals() and detections else []

                    jpg_paths = save_sequence_as_jpgs(
                        [draw_detections(f.copy(), first_event_frame_detections) for f in st.session_state.current_event_frames[:NUM_JPG_FRAMES_TO_SAVE]],
                        base_filename=""
                    )
                    frames_for_gif_with_detections = [
                        draw_detections(f.copy(), first_event_frame_detections) for f in st.session_state.current_event_frames
                    ]
                    gif_path = create_gif_from_frames(
                        frames_for_gif_with_detections,
                        base_filename="gif"
                    )
                    st.session_state.current_event_frames = []
                    
                    # Check if notifications are enabled before attempting to send
                    if st.session_state.telegram_notifications_enabled and gif_path and can_send_notification():
                        caption = "🚨 Intrusion Alert: Person Detected!"
                        if send_telegram_animation(
                            st.session_state.telegram_bot_token,
                            st.session_state.telegram_chat_id,
                            caption,
                            gif_path
                        ):
                            detection_info = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "gif_path": gif_path,
                                "representative_jpg_path": jpg_paths[0] if jpg_paths else None,
                                "all_jpg_paths": jpg_paths,
                                "caption": caption
                            }
                            st.session_state.previous_detections.insert(0, detection_info)
                            if len(st.session_state.previous_detections) > MAX_PREVIOUS_DETECTIONS:
                                st.session_state.previous_detections.pop()
                            save_previous_detections(st.session_state.previous_detections)
                            status_message_main = "👤 PERSON DETECTED! GIF sent."
                    elif not st.session_state.telegram_notifications_enabled and gif_path:
                        detection_info = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "gif_path": gif_path,
                            "representative_jpg_path": jpg_paths[0] if jpg_paths else None,
                            "all_jpg_paths": jpg_paths,
                            "caption": "Intrusion Alert: Person Detected (Notification Disabled)"
                        }
                        st.session_state.previous_detections.insert(0, detection_info)
                        if len(st.session_state.previous_detections) > MAX_PREVIOUS_DETECTIONS:
                            st.session_state.previous_detections.pop()
                        save_previous_detections(st.session_state.previous_detections)
                        status_message_main = "👤 PERSON DETECTED! GIF created (Notifications disabled)."
                    elif gif_path:  # Notifications enabled, but cooldown active
                        detection_info = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "gif_path": gif_path,
                            "representative_jpg_path": jpg_paths[0] if jpg_paths else None,
                            "all_jpg_paths": jpg_paths,
                            "caption": "Intrusion Alert: Person Detected (Cooldown)"
                        }
                        st.session_state.previous_detections.insert(0, detection_info)
                        if len(st.session_state.previous_detections) > MAX_PREVIOUS_DETECTIONS:
                            st.session_state.previous_detections.pop()
                        save_previous_detections(st.session_state.previous_detections)
                        status_message_main = "👤 PERSON DETECTED! GIF created (Notification cooldown)."
                    else:  # GIF creation failed
                        status_message_main = "👤 PERSON DETECTED! Error creating GIF."
        else:
            if st.session_state.collecting_frames_for_event:
                st.session_state.collecting_frames_for_event = False
                st.session_state.current_event_frames = []
            if st.session_state.detection_event_processed:
                st.session_state.detection_event_processed = False

        frame_placeholder.image(display_frame, channels="RGB") 
        
        with status_placeholder:
            st.subheader("📊 Status")
            st.info(f"**System Status:** {'Running' if st.session_state.system_running else 'Stopped'}")
            st.write(f"**Camera:** {st.session_state.camera_type}")
            st.write(f"**Motion Sensor:** {'TRIGGERED' if pir_is_currently_active else 'Idle'}")
            st.write(f"**Object Detection:** {detection_active_status_main}")
            if st.session_state.collecting_frames_for_event:
                st.write(f"**Frames Collected:** {len(st.session_state.current_event_frames)}/{NUM_GIF_FRAMES}")
            st.info(f"**Last Event:** {status_message_main}")
            if pir_is_currently_active:
                time_left = DETECTION_ACTIVE_DURATION_S - (time.time() - st.session_state.pir_triggered_time)
                st.progress(max(0, time_left) / DETECTION_ACTIVE_DURATION_S)
                st.caption(f"Detection active for: {max(0, int(time_left))}s more")

        # Small delay to prevent overwhelming the system
        time.sleep(0.05)

    if not st.session_state.system_running:
        if st.session_state.camera:
            st.session_state.camera.release()
            st.session_state.camera = None
        st.session_state.collecting_frames_for_event = False
        st.session_state.current_event_frames = []
        st.session_state.detection_event_processed = False
        st.rerun()

elif not st.session_state.system_running:
    if st.session_state.camera:
        st.session_state.camera.release()
        st.session_state.camera = None
    st.session_state.collecting_frames_for_event = False
    st.session_state.current_event_frames = []
    st.session_state.detection_event_processed = False

    # Create a placeholder image if it doesn't exist
    placeholder_img_path = os.path.join(os.path.dirname(__file__), "placeholder_cam.jpg")
    if not os.path.exists(placeholder_img_path):
        try:
            # Create a simple black 640x480 image
            img = Image.new('RGB', (640, 480), color='black')
            img.save(placeholder_img_path)
        except Exception as e:
            print(f"Could not create placeholder_cam.jpg: {e}")

    try:
        if os.path.exists(placeholder_img_path):
            img = Image.open(placeholder_img_path)
            frame_placeholder.image(img, caption="System Offline - Ready to Start") 
        else:
            frame_placeholder.warning("System Offline - Ready to Start")
    except Exception as e:
        frame_placeholder.error(f"Error loading placeholder image: {e}")
    
    with status_placeholder:
        st.subheader("📊 Status")
        st.info("**System Status:** Stopped")
        st.write("**Camera:** Ready")
        st.write("Configure settings and click 'Start System'.")
