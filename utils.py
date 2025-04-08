import time
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def format_date(date_str):
    """
    Format a date string for display
    
    Args:
        date_str (str): Date string in ISO format
        
    Returns:
        str: Formatted date string
    """
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y, %I:%M %p")
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        return date_str

def get_time_ago(date_str):
    """
    Get a human-readable time ago string
    
    Args:
        date_str (str): Date string in ISO format
        
    Returns:
        str: Time ago string (e.g., "2 hours ago")
    """
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - date_obj
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} {'day' if days == 1 else 'days'} ago"
        elif seconds < 2592000:
            weeks = int(seconds // 604800)
            return f"{weeks} {'week' if weeks == 1 else 'weeks'} ago"
        else:
            months = int(seconds // 2592000)
            return f"{months} {'month' if months == 1 else 'months'} ago"
    except Exception as e:
        logger.error(f"Error calculating time ago: {str(e)}")
        return "unknown time ago"
