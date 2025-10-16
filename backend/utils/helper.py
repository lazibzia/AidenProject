# ===== UTILITIES =====
# utils/helpers.py
from typing import Dict, Any, Optional
import json
from datetime import datetime, timedelta


def format_currency(amount: float) -> str:
    """Format currency values"""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.1f}K"
    else:
        return f"${amount:.2f}"


def format_date(date_str: str) -> str:
    """Format date strings"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d, %Y')
    except:
        return date_str


def calculate_date_range(mode: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> tuple:
    """Calculate date range based on mode"""
    today = datetime.today().date()

    if mode == "daily":
        return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
    elif mode == "weekly":
        start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        return start, today.strftime('%Y-%m-%d')
    elif mode == "monthly":
        start = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        return start, today.strftime('%Y-%m-%d')
    elif mode == "custom":
        if not start_date or not end_date:
            raise ValueError("Custom mode requires start_date and end_date")
        return start_date, end_date
    else:
        raise ValueError(f"Invalid mode: {mode}")


def validate_city(city: str) -> bool:
    """Validate if city is supported"""
    from config.cities import CITY_CONFIGS
    return city in CITY_CONFIGS