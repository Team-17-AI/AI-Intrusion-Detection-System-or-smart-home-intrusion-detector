# AI-Powered Smart Home Intrusion Detection System

A Raspberry Pi-based security system that uses computer vision and motion detection to identify real threats while eliminating false alarms—achieving **0% false positive rate** and **97.8% reduction in computational workload** compared to traditional motion sensors.

## 🎯 Why This Matters

Traditional home security systems have a critical flaw: they can't tell the difference between a burglar and your cat. This leads to:
- Constant false alarms from pets, shadows, and moving objects
- User fatigue and system deactivation
- Wasted energy from continuous processing

Our system solves this by combining **PIR motion sensing** with **YOLOv11-powered computer vision** to detect only human intrusions, sending real-time Telegram notifications with visual evidence.

## ✨ Key Features

- **Zero False Positives**: Accurately distinguishes humans from pets, shadows, and environmental movement
- **Energy Efficient**: Motion-triggered processing reduces CPU usage by 67% and processes 97.8% fewer frames
- **Real-Time Alerts**: Instant Telegram notifications with GIF captures of detected intrusions
- **Flexible Input**: Works with live camera feed or pre-recorded video
- **User-Friendly Interface**: Web-based Streamlit dashboard for easy configuration and monitoring
- **Modular Architecture**: Clean, extensible codebase for easy customization

## 🚀 Performance Highlights

| Metric | Traditional PIR | Our System |
|--------|----------------|------------|
| False Positive Rate | 60% (9/15 scenarios) | **0%** (0/15 scenarios) |
| Human Detection Accuracy | 100% | **100%** |
| Frames Processed (1 hour) | 7,708 | **171** |
| Average CPU Usage | 81.4% | **25.9%** |
| Energy Reduction | Baseline | **67.2%** |

## 🎥 Demo

https://github.com/user-attachments/assets/8bbbb58d-54ea-41c9-8d21-b560de2b8d6e

https://github.com/user-attachments/assets/91a01513-0dd9-449c-

https://github.com/user-attachments/assets/f4f966f9-ec80-46f0-8d61-d8f3c69ed0d0

b844-cccbfcd8651c




## 🏗️ System Architecture

```
PIR Motion Sensor → Raspberry Pi Camera → YOLOv11 Object Detection → Telegram Alert
                                    ↓
                              Streamlit Dashboard
```

**Hardware:**
- Raspberry Pi 5
- PIR Motion Sensor (HC-SR501)
- Raspberry Pi Camera Module 3

**Software Stack:**
- Python 3.9+
- YOLOv11n (pre-trained on COCO dataset)
- OpenCV for video processing
- Streamlit for web interface
- Telegram Bot API for notifications

## 📦 Installation

### Prerequisites
```bash
# Hardware setup
- Raspberry Pi 5
- PIR sensor connected to GPIO PIN 26
- Raspberry Pi Camera Module installed
```

### Software Setup
```bash
# Clone the repository
git clone https://github.com/Team-17-AI/AI-Intrusion-Detection-System-or-smart-home-intrusion-detector.git
cd AI-Intrusion-Detection-System-or-smart-home-intrusion-detector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Telegram Bot Configuration

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your bot token and chat ID
3. Configure in the Streamlit sidebar or create `config.json`:

```json
{
    "telegram_bot_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID",
    "telegram_notifications_enabled": true
}
```

## 🎮 Usage

```bash
# Start the system
streamlit run app.py
```

Open your browser to `http://localhost:8501`

**Configuration Options:**
- Choose between live camera or video file input
- Adjust detection sensitivity
- Configure notification cooldown period
- Enable/disable Telegram alerts

## 📊 Experimental Validation

Our system was rigorously tested across 15 scenarios including:
- Normal/fast/low movement patterns
- Partial visibility and obstruction
- Multiple people
- Clothing variations (hooded, masked)
- Environmental false triggers (shadows, objects, pets)

**Full research paper**: [View PDF Report](./17-FinalReport-1.pdf)

### Energy Optimization Results

We tested multiple optimization strategies:
- **PIR-Triggered Detection**: 67.2% reduction in CPU usage
- **Frame Skipping**: Configurable sampling rates (0.05s to 1s intervals)
- **Idle Scheduling**: Minimal resource usage during inactivity

See our [detailed experimental results](./17-FinalReport-1.pdf) for complete performance analysis.

## 📁 Project Structure

```
├── app.py                    # Main Streamlit application
├── motion_detector.py        # PIR sensor logic
├── object_detector.py        # YOLO model inference
├── telegram_notifier.py      # Notification system
├── utils.py                  # Frame saving & GIF creation
├── config.json              # Configuration file
├── requirements.txt         # Python dependencies
├── yolov5n.pt              # YOLO model weights
└── snapshots/              # Saved detection events
```

## 🛠️ Customization

**Adjust Detection Parameters:**
```python
# motion_detector.py
DETECTION_ACTIVE_DURATION_S = 30  # Detection window after PIR trigger

# utils.py
NUM_JPG_FRAMES_TO_SAVE = 5       # Frames saved as images
NUM_GIF_FRAMES = 10              # Frames in notification GIF
```

**Change Notification Settings:**
```python
# telegram_notifier.py
NOTIFICATION_COOLDOWN_S = 60     # Minimum time between alerts
```

## 🔬 Technical Deep Dive

### Why YOLOv11?
- Single-pass detection architecture (faster than R-CNN)
- Optimized for edge devices like Raspberry Pi
- Pre-trained on 80+ object classes (COCO dataset)
- Configurable confidence thresholds

### Energy Efficiency Strategy
1. PIR sensor acts as first-stage filter (low power)
2. Camera and AI activate only on motion detection
3. Frame skipping reduces unnecessary processing
4. Configurable sleep intervals during idle periods

### False Positive Elimination
Traditional PIR sensors trigger on any thermal change. Our system adds a second verification layer using computer vision to confirm human presence, filtering out:
- Pet movement
- Shadow changes
- Object displacement
- Environmental factors (wind, light changes)

## 🤝 Contributing

This project was developed as part of an IoT systems course at Maastricht University. Contributions, issues, and feature requests are welcome!

**Team Members**: Deniz Derviş, John Fourlas, Tadiwanashe Matara, Cristian Nițu, Stefani Parvina, Melodie Prudhomme, Raman Yousefi Avarzaman

## 📄 License

MIT License - feel free to use this project for learning or commercial purposes.

## 📚 References

Based on research in AI-powered home security systems. See our [full academic report](./17-FinalReport-1.pdf) for citations and detailed methodology.

## 📧 Contact

**Tadiwanashe Matara**
- GitHub: [@Tadiwa-M](https://github.com/Tadiwa-M)
- LinkedIn: [[Connect with me](https://linkedin.com/in/your-profile](https://www.linkedin.com/in/tadiwanashe-matara-a3479a19a?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app))
- Email: Tkl.matara@student.maastrichtuniversity.nl

---

⭐ If you find this project useful, please consider starring it!
