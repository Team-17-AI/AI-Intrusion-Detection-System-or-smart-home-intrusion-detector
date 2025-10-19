# utils.py
import cv2
import os
from datetime import datetime
from PIL import Image # For GIF creation

SNAPSHOT_DIR = "snapshots" # We can keep this name, it will now store JPGs and GIFs
if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

NUM_JPG_FRAMES_TO_SAVE = 4
NUM_GIF_FRAMES = 10
GIF_FRAME_DURATION_MS = 150 # Milliseconds per frame in GIF (approx 6.7 FPS)

def save_individual_frame_as_jpg(frame, base_filename="frame"):
    """Saves a single frame as a JPG image with a unique timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f") # Added microseconds for uniqueness
    filename = f"{base_filename}_{timestamp}.jpg"
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    try:
        cv2.imwrite(filepath, frame)
        print(f"Snapshot saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving snapshot: {e}")
        return None

def save_sequence_as_jpgs(frames_bgr, base_filename="detection_event"):
    """Saves the first NUM_JPG_FRAMES_TO_SAVE from a list of BGR frames as JPG images."""
    saved_jpg_paths = []
    timestamp_prefix = datetime.now().strftime("%m%d_%H%M%S")
    for i, frame in enumerate(frames_bgr):
        if i >= NUM_JPG_FRAMES_TO_SAVE:
            break
        filename = f"{base_filename}_{timestamp_prefix}_frame_{i+1}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        try:
            cv2.imwrite(filepath, frame)
            saved_jpg_paths.append(filepath)
            print(f"Saved JPG: {filepath}")
        except Exception as e:
            print(f"Error saving JPG {filepath}: {e}")
    return saved_jpg_paths

def create_gif_from_frames(frames_bgr, base_filename="detection_event_animation"):
    """Creates a GIF from a list of BGR frames."""
    if not frames_bgr:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gif_filename = f"{base_filename}_{timestamp}.gif"
    gif_filepath = os.path.join(SNAPSHOT_DIR, gif_filename)

    pil_frames = []
    for frame_bgr in frames_bgr:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_frames.append(Image.fromarray(frame_rgb))

    if not pil_frames:
        return None

    try:
        pil_frames[0].save(
            gif_filepath,
            save_all=True,
            append_images=pil_frames[1:],
            duration=GIF_FRAME_DURATION_MS,
            loop=0  # 0 means loop indefinitely
        )
        print(f"GIF saved to {gif_filepath}")
        return gif_filepath
    except Exception as e:
        print(f"Error creating GIF: {e}")
        return None

class EnergyMonitor:
    """Class to monitor and calculate energy usage of the system."""
    
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        """Reset all energy monitoring statistics."""
        self.start_time = datetime.now()
        self.total_energy = 0.0
        self.detection_active_time = 0.0
        self.last_update = datetime.now()
        
        # Power consumption estimates (in Watts)
        self.CAMERA_POWER = 0.3  # USB camera
        self.PIR_POWER = 0.07     # PIR sensor
        self.CPU_POWER_IDLE = 0.35  # CPU in idle state
        self.CPU_POWER_DETECTION = 5.0  # CPU during object detection
    
    def update(self, pir_active=False, camera_active=False, detection_active=False):
        """Update energy calculations based on current component states."""
        current_time = datetime.now()
        time_delta = (current_time - self.last_update).total_seconds()
        
        # Calculate power consumption for this interval
        power = 0.0
        if camera_active:
            power += self.CAMERA_POWER
        if pir_active:
            power += self.PIR_POWER
        
        # Add CPU power consumption
        if detection_active:
            power += self.CPU_POWER_DETECTION
            self.detection_active_time += time_delta
        else:
            power += self.CPU_POWER_IDLE
        
        # Calculate energy used in this interval (Power * Time)
        energy_interval = power * time_delta
        self.total_energy += energy_interval
        
        self.last_update = current_time
    
    def get_stats(self):
        """Get current energy monitoring statistics."""
        current_time = datetime.now()
        total_time = (current_time - self.start_time).total_seconds()
        
        return {
            "total_energy": self.total_energy,
            "total_time": total_time,
            "detection_active_time": self.detection_active_time,
            "average_power": self.total_energy / total_time if total_time > 0 else 0
        }

