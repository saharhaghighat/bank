from utills.db_connection import db
from datetime import datetime, timezone


def log_message(medium, recipient, message, status):
    try:

        log_entry = {
            'medium': medium,
            'recipient': recipient,
            'message': message,
            'status': status,
            'created_at': datetime.now(timezone.utc)
        }

        db.log.insert_one(log_entry)
        print("Message logged successfully")

    except Exception as e:
        print(f"Error logging message: {e}")
