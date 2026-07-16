from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional

def calculate_baby_age(birth_date: str) -> dict:
    """
    Calculate baby's age from birth date string (ISO format).
    Returns a dict with 'months', 'days', and 'display' string.
    """
    try:
        bd = datetime.fromisoformat(birth_date).date()
    except Exception:
        return {"months": 0, "days": 0, "display": "Không xác định"}
    
    today = date.today()
    delta = relativedelta(today, bd)
    total_months = delta.years * 12 + delta.months
    display = f"{delta.years} tuổi {delta.months} tháng {delta.days} ngày" if delta.years >= 1 else \
              f"{total_months} tháng {delta.days} ngày" if total_months >= 1 else \
              f"{(today - bd).days} ngày tuổi"
    
    return {"months": total_months, "days": (today - bd).days, "display": display}


def format_agent_response(content: str, next_step: Optional[str] = None) -> dict:
    """Format a standard agent response payload."""
    return {"response": content, "next_step": next_step}


def sanitize_baby_id(baby_id: Optional[str]) -> Optional[str]:
    """Remove whitespace and return None if empty."""
    if not baby_id:
        return None
    sanitized = baby_id.strip()
    return sanitized if sanitized else None
