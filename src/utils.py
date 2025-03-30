"""
Utility functions for the ClickUp API client.
"""

import re
from datetime import datetime, timedelta
from typing import Union


def convert_to_timestamp(date_input: Union[str, int, datetime]) -> int:
    """
    Convert various date formats to a Unix timestamp in milliseconds.

    Args:
        date_input: Date in string, timestamp, or datetime format

    Returns:
        Unix timestamp in milliseconds
    """
    if isinstance(date_input, int):
        # Check if it's already in milliseconds (13 digits) or seconds (10 digits)
        if len(str(date_input)) >= 13:
            return date_input
        else:
            return date_input * 1000

    elif isinstance(date_input, datetime):
        # Convert datetime to milliseconds
        return int(date_input.timestamp() * 1000)

    elif isinstance(date_input, str):
        # Check if it's a numeric string (timestamp)
        if date_input.isdigit():
            return int(date_input)

        # Try to parse as ISO format date
        try:
            dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except ValueError:
            # Try some common date formats
            for fmt in [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%b %d, %Y",
                "%B %d, %Y",
                "%d %b %Y",
                "%d %B %Y",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
            ]:
                try:
                    dt = datetime.strptime(date_input, fmt)
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    continue

            # Try to handle natural language (simplified)
            date_input = date_input.lower().strip()
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Handle relative dates
            if date_input == "today":
                return int(today.timestamp() * 1000)

            if date_input == "tomorrow":
                tomorrow = today + timedelta(days=1)
                return int(tomorrow.timestamp() * 1000)

            if date_input == "yesterday":
                yesterday = today - timedelta(days=1)
                return int(yesterday.timestamp() * 1000)

            # Handle "next" and "last" prefixes
            next_match = re.match(r"next\s+(\w+)", date_input)
            last_match = re.match(r"last\s+(\w+)", date_input)

            if next_match:
                time_unit = next_match.group(1).lower()
                if time_unit == "week":
                    days_to_add = (
                        7 - today.weekday() or 7
                    )  # If today is Monday, go to next Monday
                    next_week = today + timedelta(days=days_to_add)
                    return int(next_week.timestamp() * 1000)
                elif time_unit == "month":
                    if today.month == 12:
                        next_month = today.replace(year=today.year + 1, month=1, day=1)
                    else:
                        next_month = today.replace(month=today.month + 1, day=1)
                    return int(next_month.timestamp() * 1000)
                elif time_unit in [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]:
                    days = {
                        "monday": 0,
                        "tuesday": 1,
                        "wednesday": 2,
                        "thursday": 3,
                        "friday": 4,
                        "saturday": 5,
                        "sunday": 6,
                    }
                    target_day = days[time_unit]
                    days_ahead = (target_day - today.weekday()) % 7
                    if days_ahead == 0:  # today is target day, so we want next week
                        days_ahead = 7
                    next_day = today + timedelta(days=days_ahead)
                    return int(next_day.timestamp() * 1000)

            if last_match:
                time_unit = last_match.group(1).lower()
                if time_unit == "week":
                    days_to_subtract = today.weekday() + 1  # Go to last Monday
                    last_week = today - timedelta(days=days_to_subtract)
                    return int(last_week.timestamp() * 1000)
                elif time_unit == "month":
                    if today.month == 1:
                        last_month = today.replace(year=today.year - 1, month=12, day=1)
                    else:
                        last_month = today.replace(month=today.month - 1, day=1)
                    return int(last_month.timestamp() * 1000)
                elif time_unit in [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]:
                    days = {
                        "monday": 0,
                        "tuesday": 1,
                        "wednesday": 2,
                        "thursday": 3,
                        "friday": 4,
                        "saturday": 5,
                        "sunday": 6,
                    }
                    target_day = days[time_unit]
                    days_ago = (today.weekday() - target_day) % 7
                    if days_ago == 0:  # today is target day, so we want last week
                        days_ago = 7
                    last_day = today - timedelta(days=days_ago)
                    return int(last_day.timestamp() * 1000)

            # If all else fails, raise an error
            raise ValueError(f"Could not parse date: {date_input}")

    raise TypeError(f"Unsupported date type: {type(date_input)}")


def human_readable_time(milliseconds: int) -> str:
    """
    Convert milliseconds to a human-readable time string.

    Args:
        milliseconds: Time in milliseconds

    Returns:
        Human-readable time string (e.g., "2h 30m")
    """
    seconds = milliseconds // 1000
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    if days > 0:
        return f"{days}d {hours % 24}h"
    elif hours > 0:
        return f"{hours}h {minutes % 60}m"
    elif minutes > 0:
        return f"{minutes}m {seconds % 60}s"
    else:
        return f"{seconds}s"


def parse_time_to_milliseconds(time_str: str) -> int:
    """
    Parse a human-readable time string to milliseconds.

    Supported formats:
    - "1h 30m"
    - "90m"
    - "1d 6h"
    - "1.5h"

    Args:
        time_str: Time string to parse

    Returns:
        Time in milliseconds
    """
    time_str = time_str.lower().strip()
    milliseconds = 0

    # Handle decimal hours/minutes
    if re.match(r"^\d+(\.\d+)?[hm]$", time_str):
        value = float(time_str[:-1])
        unit = time_str[-1]

        if unit == "h":
            milliseconds = int(value * 3600 * 1000)
        elif unit == "m":
            milliseconds = int(value * 60 * 1000)

        return milliseconds

    # Handle complex time strings like "1h 30m" or "2d 4h 30m"
    parts = re.findall(r"(\d+)([dhms])", time_str)

    for value, unit in parts:
        value = int(value)
        if unit == "d":
            milliseconds += value * 24 * 3600 * 1000
        elif unit == "h":
            milliseconds += value * 3600 * 1000
        elif unit == "m":
            milliseconds += value * 60 * 1000
        elif unit == "s":
            milliseconds += value * 1000

    return milliseconds
