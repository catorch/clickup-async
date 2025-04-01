"""
Folder models for ClickUp API.

This module contains models related to folders in ClickUp.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from .common import Location
from .space import Status


class Folder(BaseModel):
    """
    Represents a folder within a space.

    A folder is a container that helps organize lists and tasks within a space.
    It can have its own statuses, task count, and visibility settings.
    """

    id: str
    name: str
    orderindex: Optional[int] = None
    override_statuses: Optional[bool] = None
    hidden: Optional[bool] = None
    space: Optional[Location] = None
    task_count: Optional[int] = None
    lists: Optional[List[Dict[str, Any]]] = None
    archived: Optional[bool] = None
    statuses: Optional[List[Status]] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    permission_level: Optional[str] = None
    content: Optional[str] = None
    multiple_assignees: Optional[bool] = None
    custom_fields: Optional[List[Dict[str, Any]]] = None

    # Computed properties
    @property
    def created_at(self) -> Optional[datetime]:
        """Get the creation date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(int(self.date_created) / 1000)
            if self.date_created
            else None
        )

    @property
    def updated_at(self) -> Optional[datetime]:
        """Get the last update date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(int(self.date_updated) / 1000)
            if self.date_updated
            else None
        )

    model_config = ConfigDict(populate_by_name=True)
