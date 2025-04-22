from typing import List, Dict, Any
from datetime import datetime

# In-memory notification store
notification_db: List[Dict[str, Any]] = []

def create_notification(user_id: int, message: str, type_: str = "info", related_task: int = None):
    notification = {
        "id": len(notification_db) + 1,
        "user_id": user_id,
        "message": message,
        "type": type_,
        "timestamp": datetime.utcnow().isoformat(),
        "related_task": related_task
    }
    notification_db.append(notification)
    return notification

def get_notifications_for_user(user_id: int) -> List[Dict[str, Any]]:
    return [n for n in notification_db if n["user_id"] == user_id]