"""
Event Bus for DFlow - Simple pub/sub system for observability.
RFC-0006: Event System
"""

from datetime import datetime
from db.connection import get_connection
import json

# In-memory subscriber registry
_subscribers = {}

# Event types
EVENT_TYPES = [
    "DO_CREATED",
    "STATE_CHANGED",
    "PIPELINE_STARTED",
    "PIPELINE_FINISHED",
    "TRANSFORM_APPLIED",
    "VALIDATION_FAILED",
    "INGEST_STARTED",
    "INGEST_COMPLETED"
]


def subscribe(event_type, callback):
    """Subscribe a callback function to an event type."""
    if event_type not in _subscribers:
        _subscribers[event_type] = []
    _subscribers[event_type].append(callback)


def unsubscribe(event_type, callback):
    """Unsubscribe a callback function from an event type."""
    if event_type in _subscribers:
        if callback in _subscribers[event_type]:
            _subscribers[event_type].remove(callback)


def emit(event_type, payload=None):
    """
    Emit an event to all subscribers.
    Also logs the event to the database.
    """
    if event_type not in EVENT_TYPES:
        print(f"[WARN] Unknown event type: {event_type}")
    
    timestamp = datetime.utcnow().isoformat()
    
    # Log to database
    _log_event_to_db(event_type, payload, timestamp)
    
    # Notify subscribers
    if event_type in _subscribers:
        for callback in _subscribers[event_type]:
            try:
                callback({
                    "event": event_type,
                    "payload": payload,
                    "timestamp": timestamp
                })
            except Exception as e:
                print(f"[ERROR] Event callback failed for {event_type}: {e}")


def _log_event_to_db(event_type, payload, timestamp):
    """Persist event to the events table."""
    conn = get_connection()
    cur = conn.cursor()
    
    do_id = None
    if payload and isinstance(payload, dict):
        do_id = payload.get("do_id")
    
    try:
        cur.execute("""
            INSERT INTO events (do_id, event, timestamp)
            VALUES (?, ?, ?)
        """, (do_id, event_type, timestamp))
        conn.commit()
    except Exception as e:
        print(f"[WARN] Failed to log event to DB: {e}")
    finally:
        conn.close()


# Built-in logger subscriber
def default_logger(event_data):
    """Default logger that prints events to console."""
    event = event_data["event"]
    ts = event_data["timestamp"]
    payload = event_data.get("payload", {})
    
    do_id = payload.get("do_id", "N/A") if isinstance(payload, dict) else "N/A"
    
    print(f"[EVENT] {ts} | {event} | DO: {do_id}")


# Auto-subscribe default logger
subscribe("DO_CREATED", default_logger)
subscribe("STATE_CHANGED", default_logger)
subscribe("PIPELINE_STARTED", default_logger)
subscribe("PIPELINE_FINISHED", default_logger)
subscribe("INGEST_STARTED", default_logger)
subscribe("INGEST_COMPLETED", default_logger)