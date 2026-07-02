"""Lemma Function: Notifier — sends workflow event notifications."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger("aegis.fn.notifier")

# In-memory notification bus (replace with WebSocket/SSE in production)
_notification_store: List[Dict] = []


def send_notification(
    event_type: str,
    title: str,
    message: str,
    pod_id: Optional[str] = None,
    severity: str = "info",
    metadata: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Emit a workflow event notification.
    Stored in memory + logged. Frontend polls via SSE.
    """
    notification = {
        "id": f"notif_{len(_notification_store) + 1:04d}",
        "event_type": event_type,
        "title": title,
        "message": message,
        "pod_id": pod_id,
        "severity": severity,  # info | success | warning | error
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }
    _notification_store.append(notification)
    logger.info(f"NOTIFICATION [{severity.upper()}] {event_type}: {title}")
    return notification


def get_notifications(pod_id: Optional[str] = None, last_n: int = 50) -> List[Dict]:
    """Get recent notifications, optionally filtered by pod."""
    store = _notification_store
    if pod_id:
        store = [n for n in store if n.get("pod_id") == pod_id]
    return store[-last_n:]


def clear_notifications(pod_id: Optional[str] = None) -> int:
    """Clear notifications. Returns count cleared."""
    global _notification_store
    if pod_id:
        before = len(_notification_store)
        _notification_store = [n for n in _notification_store if n.get("pod_id") != pod_id]
        return before - len(_notification_store)
    count = len(_notification_store)
    _notification_store = []
    return count
