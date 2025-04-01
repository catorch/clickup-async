"""
Time tracking models for ClickUp API.

This module contains models related to time tracking in ClickUp.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict


class TimeEntry(BaseModel):
    """Model representing a time entry."""

    id: Optional[Union[str, int]] = None
    wid: Optional[Union[str, int]] = None
    task_id: Optional[Union[str, int]] = None
    start: Optional[Union[str, int]] = None
    end: Optional[Union[str, int]] = None
    duration: Optional[str] = None
    billable: Optional[bool] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    at: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None
    task: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        """Convert integer IDs and timestamps to strings."""
        if isinstance(self.id, int):
            self.id = str(self.id)
        if isinstance(self.wid, int):
            self.wid = str(self.wid)
        if isinstance(self.task_id, int):
            self.task_id = str(self.task_id)
        if isinstance(self.start, int):
            self.start = str(self.start)
        if isinstance(self.end, int):
            self.end = str(self.end)
        if isinstance(self.duration, int):
            self.duration = str(self.duration)
        # Extract task_id from task if available
        if self.task and isinstance(self.task, dict) and "id" in self.task:
            self.task_id = str(self.task["id"])

    @property
    def start_datetime(self) -> Optional[datetime]:
        """Convert start timestamp to datetime."""
        if not self.start:
            return None
        try:
            return datetime.fromtimestamp(int(self.start) / 1000)
        except (ValueError, TypeError):
            return None

    @property
    def end_datetime(self) -> Optional[datetime]:
        """Convert end timestamp to datetime."""
        if not self.end:
            return None
        try:
            return datetime.fromtimestamp(int(self.end) / 1000)
        except (ValueError, TypeError):
            return None

    @classmethod
    def from_timestamp(cls, timestamp: int, **kwargs: Any) -> "TimeEntry":
        """Create a TimeEntry from a timestamp."""
        return cls(start=str(timestamp), **kwargs)

    model_config = ConfigDict(populate_by_name=True)
