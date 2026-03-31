from fastapi import HTTPException
from datetime import datetime
from app.api.v1.driver.order_routes import ALLOWED_TRANSITIONS

def validate_transition(current_status: str, next_status: str):
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if next_status not in allowed:
        raise HTTPException(
            409,
            f"Invalid transition: {current_status} → {next_status}"
        )

def build_timeline_entry(status: str):
    return {
        "status": status,
        "at": datetime.utcnow()
    }
