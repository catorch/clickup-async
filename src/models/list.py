"""
List models for ClickUp API.

This module contains models related to lists in ClickUp.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from .common import Location, PriorityObject
from .user import User


class TaskList(BaseModel):
    """Represents a list within a folder or space"""

    id: str
    name: str
    orderindex: int
    status: Optional[Dict[str, Any]] = None
    priority: Optional[PriorityObject] = None
    assignee: Optional[User] = None
    task_count: int = 0
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    folder: Optional[Location] = None
    space: Optional[Location] = None
    archived: bool = False
    override_statuses: Optional[bool] = None
    permission_level: Optional[str] = None
    content: Optional[str] = None

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

    model_config = ConfigDict(populate_by_name=True)
