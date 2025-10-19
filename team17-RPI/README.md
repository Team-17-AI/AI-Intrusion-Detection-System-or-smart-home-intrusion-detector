# Modular Intrusion Detection System

This project is a modular intrusion detection system built with Python and Streamlit. It uses a simulated PIR motion sensor to trigger object detection (specifically for persons) using a YOLOv5 model. Upon detecting a person, the system can record event frames as JPGs, create a GIF animation of the event, and send a notification with the GIF to a specified Telegram chat.

## Features

*   **Input Flexibility**: Supports live camera feed or video file upload.
*   **Motion Detection (Simulated)**: A button simulates a PIR sensor trigger, activating object detection for a configurable duration.
*   **Object Detection**: Utilizes YOLOv5n to detect objects, focusing on 'person' class.
*   **Event Recording**:
    *   Saves a configurable number of initial frames of a detection event as JPG images.
    *   Creates a GIF animation from a configurable number of frames during the event.
*   **Telegram Notifications**:
    *   Sends the generated GIF to a specified Telegram bot and chat ID.
    *   Includes a cooldown period for notifications to prevent spam.
    *   Notifications can be globally enabled or disabled.
*   **Configuration Management**:
    *   Telegram bot token and chat ID can be configured via the UI and are saved in `config.json`.
*   **Session State Management**: Robustly handles application state using Streamlit's session state.
*   **User Interface**: Interactive web interface built with Streamlit, showing live feed/video, status, and previous detections.
*   **Previous Detections Log**: Displays a history of recent detection events with timestamps, captions, and the recorded GIF or representative image.

## Modules

The project is structured into several Python files:

*   `app.py`: The main Streamlit application. It handles the UI, video processing, state management, and orchestrates the different modules. [1]
*   `motion_detector.py`: Manages the simulated PIR motion sensor logic, including the trigger and the active detection window. [2]
*   `object_detector.py`: Handles loading the YOLO model and performing object detection on video frames. [4]
*   `telegram_notifier.py`: Responsible for sending notifications (GIF animations) to Telegram and managing notification cooldowns. [3]
*   `utils.py`: Contains utility functions for saving frames as JPGs and creating GIFs from a sequence of frames. [7]

## Setup and Installation

1.  **Clone the repository (if applicable) or download the files.**
2.  **Create a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
      # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    The project requires several Python libraries. You can install them using pip. Create a `requirements.txt` file with the following content:
    ```
    streamlit
    opencv-python-headless
    ultralytics
    Pillow
    requests
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `python-dotenv` was listed in one of the source files [5] but doesn't seem to be actively used in the provided code. You can add it if you plan to use `.env` files for configuration.)*

4.  **Download YOLOv5 model weights:**
    The application expects `yolov5n.pt` in the root directory [1]. You can usually download this from the Ultralytics YOLOv5 repository or it might be downloaded automatically by the `ultralytics` library on first run if not present.

5. **You need a PIR Motion Sesnsor on PIN 26 to run this, and a RPI Camera installed on your Raspberry Pi 5.**

## Configuration

*   **Telegram Notifications**:
    *   To use Telegram notifications, you need a Telegram Bot Token and a Chat ID.
    *   These can be entered and saved via the "Telegram Notifications" section in the application's sidebar.
    *   The configuration is saved in a `config.json` file in the root directory [1]. Example `config.json` [6]:
        ```json
        {
            "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
            "telegram_chat_id": "YOUR_CHAT_ID_HERE",
            "telegram_notifications_enabled": true
        }
        ```

## How to Run

1.  Ensure all dependencies are installed and the YOLO model file (`yolov5n.pt`) is in the project's root directory.
2.  Navigate to the project directory in your terminal.
3.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
4.  Open your web browser and go to the local URL provided by Streamlit (usually `http://localhost:8501`).
5.  Configure settings in the sidebar:
    *   Select input mode (Live Camera or Video File).
    *   If using Video File, upload a video.
    *   Set up Telegram notifications if desired.
6.  Click "Start System".
7.  To simulate motion, click the "Simulate PIR Trigger" button in the sidebar.

## Key Technologies Used

*   **Streamlit**: For the web application interface. [1]
*   **OpenCV (cv2)**: For video capture and image processing. [1, 4, 7]
*   **YOLO (Ultralytics)**: For object detection. [4]
*   **Pillow (PIL)**: For creating GIF animations. [7]
*   **Requests**: For making API calls to Telegram. [3]

## Notes

*   The system saves snapshots (JPGs) and GIFs into a `snapshots` directory created in the root of the project [7].
*   The maximum number of previous detections displayed is set by `MAX_PREVIOUS_DETECTIONS` in `app.py` [1].
*   The number of frames saved as JPGs and used for GIFs is configurable via `NUM_JPG_FRAMES_TO_SAVE` and `NUM_GIF_FRAMES` in `utils.py` [7].
*   The duration for which object detection remains active after a PIR trigger is set by `DETECTION_ACTIVE_DURATION_S` in `motion_detector.py` [2].
*   Telegram notification cooldown is managed by `NOTIFICATION_COOLDOWN_S` in `telegram_notifier.py` [3].