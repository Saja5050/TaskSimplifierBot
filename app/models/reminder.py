import time
import threading

def set_reminder(time_in_minutes, task, chat_id, send_message_func):
    """
    Sends a reminder after the specified time.
    """
    def remind():
        time.sleep(time_in_minutes * 60)  # Wait for the specified time
        send_message_func(chat_id, f"Reminder: {task}")
    
    threading.Thread(target=remind).start()
    return "Reminder set!"
