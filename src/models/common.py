"""
Common models for ClickUp API.

This module contains common models used across different ClickUp entities.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    """Represents a location reference (folder/space) in a task or list"""

    id: str
    name: Optional[str] = None
    hidden: Optional[bool] = None
    access: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class PriorityObject(BaseModel):
    """Represents a priority object as returned by the API"""

    id: Optional[int] = None
    priority: Optional[Union[int, str]] = None  # Allow both integer and string
    color: Optional[str] = None
    orderindex: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        """Convert string priority to integer if needed"""
        if isinstance(self.priority, str):
            priority_map = {
                "urgent": 1,
                "high": 2,
                "normal": 3,
                "low": 4,
            }
            self.priority = priority_map.get(
                self.priority.lower(), 3
            )  # Default to normal

    model_config = ConfigDict(populate_by_name=True)


class CustomField(BaseModel):
    """Represents a custom field"""

    id: str
    name: str
    type: str
    value: Optional[Any] = None
    type_config: Optional[Dict[str, Any]] = Field(None, alias="type_config")
    date_created: Optional[str] = None
    hide_from_guests: Optional[bool] = None
    required: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)
