"""
Task models for ClickUp API.

This module contains models related to tasks in ClickUp.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .base import Priority
from .common import Location, PriorityObject
from .user import User


class Task(BaseModel):
    """A ClickUp task"""

    id: str
    name: str
    description: Optional[str] = None
    status: Optional[Any] = None  # Status can be a string or a Status object
    orderindex: Optional[str] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    date_closed: Optional[str] = None
    date_done: Optional[str] = None
    creator: Optional[User] = None
    assignees: List[User] = []
    checklists: List[Any] = []
    tags: List[str] = []
    parent: Optional[str] = None
    priority: Optional[PriorityObject] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    time_estimate: Optional[str] = None
    time_spent: Optional[Union[str, int]] = None  # Allow both string and integer
    custom_fields: List[Any] = []
    list: Optional[Location] = None
    folder: Optional[Location] = None
    space: Optional[Location] = None
    url: Optional[str] = None
    attachments: Optional[List[Any]] = None
    custom_id: Optional[str] = None
    text_content: Optional[str] = None
    archived: bool = False
    markdown_content: Optional[str] = None
    points: Optional[float] = None
    group_assignees: Optional[List[str]] = None
    watchers: Optional[List[Union[str, Dict[str, Any]]]] = (
        None  # Allow both string and user object
    )
    links_to: Optional[str] = None
    custom_item_id: Optional[int] = None
    custom_task_ids: bool = False
    team_id: Optional[str] = None

    @property
    def priority_value(self) -> Optional[Priority]:
        """Get the priority as an enum value"""
        if not self.priority:
            return None
        try:
            if isinstance(self.priority.priority, str):
                return Priority(int(self.priority.priority))
            return Priority(self.priority.priority)
        except (ValueError, TypeError):
            return None

    def model_post_init(self, __context: Any) -> None:
        """Post initialization hook to ensure status is properly set"""
        if isinstance(self.status, dict):
            # Import here to avoid circular import
            from .space import Status

            self.status = Status.model_validate(self.status)
        # Convert time_spent to string if it's an integer
        if isinstance(self.time_spent, int):
            self.time_spent = str(self.time_spent)
        # Convert watchers to list of strings if they're user objects
        if self.watchers and isinstance(self.watchers[0], dict):
            self.watchers = [
                str(w.get("id", "")) for w in self.watchers if isinstance(w, dict)
            ]

    # Computed properties
    @property
    def due_date_timestamp(self) -> Optional[int]:
        """Get the due date as a timestamp (if available)"""
        return int(self.due_date) if self.due_date and self.due_date.isdigit() else None

    @property
    def start_date_timestamp(self) -> Optional[int]:
        """Get the start date as a timestamp (if available)"""
        return (
            int(self.start_date)
            if self.start_date and self.start_date.isdigit()
            else None
        )

    @property
    def created_at(self) -> Optional[datetime]:
        """Get the creation date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(
                int(self.date_created) / 1000, tz=timezone.utc
            ).replace(tzinfo=None)
            if self.date_created
            else None
        )

    @property
    def updated_at(self) -> Optional[datetime]:
        """Get the last update date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(
                int(self.date_updated) / 1000, tz=timezone.utc
            ).replace(tzinfo=None)
            if self.date_updated
            else None
        )

    @property
    def closed_at(self) -> Optional[datetime]:
        """Get the closing date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(
                int(self.date_closed) / 1000, tz=timezone.utc
            ).replace(tzinfo=None)
            if self.date_closed
            else None
        )

    @property
    def done_at(self) -> Optional[datetime]:
        """Get the completion date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(int(self.date_done) / 1000, tz=timezone.utc).replace(
                tzinfo=None
            )
            if self.date_done
            else None
        )

    model_config = ConfigDict(populate_by_name=True)


class TimeInStatus(BaseModel):
    """Represents time spent in a status for a task"""

    status: str
    time_in_status: int  # Time in milliseconds
    total_time: int  # Total time in milliseconds

    model_config = ConfigDict(populate_by_name=True)


class TaskTimeInStatus(BaseModel):
    """Represents time in status information for a task"""

    task_id: str
    times: List[TimeInStatus] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class BulkTimeInStatus(BaseModel):
    """Represents time in status information for multiple tasks"""

    tasks: List[TaskTimeInStatus] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)
