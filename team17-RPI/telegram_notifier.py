# telegram_notifier.py
import requests
import streamlit as st
import time

NOTIFICATION_COOLDOWN_S = 60

def init_telegram_state():
    if 'last_notification_time' not in st.session_state:
        st.session_state.last_notification_time = 0
    # 'telegram_notifications_enabled' is initialized and managed in app.py

def can_send_notification():
    init_telegram_state() # Ensures last_notification_time is initialized
    if time.time() - st.session_state.last_notification_time > NOTIFICATION_COOLDOWN_S:
        return True
    return False

def update_last_notification_time():
    st.session_state.last_notification_time = time.time()

# Keep send_telegram_message_with_photo for flexibility, or remove if only GIFs are sent
def send_telegram_message_with_photo(bot_token, chat_id, caption, image_path):
    """Sends a message with a photo to a Telegram chat."""
    # ... (implementation from previous version, can be kept or removed) ...
    # For this exercise, we'll focus on the GIF sender.
    # If you want to keep both, ensure no conflicts.
    # For now, let's assume we will replace its usage with send_telegram_animation.
    if not bot_token or not chat_id:
        st.warning("Telegram Bot Token or Chat ID is not configured for photo.")
        return False
    # ... rest of the photo sending logic ...
    pass # Placeholder if you comment out the actual logic



def send_telegram_animation(bot_token, chat_id, caption, gif_path):
    """Sends an animation (GIF) to a Telegram chat."""
    # Check if notifications are globally enabled (from app.py's session state)
    if not st.session_state.get('telegram_notifications_enabled', True): # Default to True if key missing
        st.info("Telegram notifications are currently disabled in settings.")
        print("Telegram send_telegram_animation: Notifications disabled by user setting.")
        return False # Do not proceed

    if not bot_token or not chat_id:
        st.warning("Telegram Bot Token or Chat ID is not configured.")
        return False

    if not can_send_notification():
        st.info("Telegram notification skipped due to cooldown.")
        print("Notification cooldown active. Skipping Telegram animation.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendAnimation"
    try:
        with open(gif_path, 'rb') as animation_file:
            files = {'animation': animation_file}
            data = {'chat_id': chat_id, 'caption': caption}
            response = requests.post(url, files=files, data=data, timeout=20) 
        response.raise_for_status()
        if response.json().get("ok"):
            st.success(f"Intrusion alert GIF sent to Telegram Chat ID {chat_id}!")
            update_last_notification_time()
            return True
        else:
            st.error(f"Telegram API Error (Animation): {response.json().get('description')}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send Telegram animation: {e}")
        return False
    except FileNotFoundError:
        st.error(f"Animation GIF not found at {gif_path}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during Telegram animation sending: {e}")
        return False