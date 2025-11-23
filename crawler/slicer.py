# FILE: crawler/slicer.py

from datetime import datetime

def split_date_range(start_iso: str, end_iso: str):
    """
    Split a date range into two halves to avoid exceeding GitHub API limits.
    
    Args:
        start_iso (str): Start date in ISO format, e.g. '2020-01-01'
        end_iso (str): End date in ISO format, e.g. '2020-12-31'

    Returns:
        tuple: ((start1, end1), (start2, end2)) or None if cannot split further
    """
    s = datetime.fromisoformat(start_iso)
    e = datetime.fromisoformat(end_iso)
    mid = s + (e - s) / 2
    mid_date = mid.date().isoformat()
    
    # If mid_date equals start or end, cannot split further
    if mid_date == start_iso or mid_date == end_iso:
        return None
    
    return (start_iso, mid_date), (mid_date, end_iso)
