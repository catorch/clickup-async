"""
Workspace models for ClickUp API.

This module contains models related to workspaces (teams) in ClickUp.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Workspace(BaseModel):
    """A ClickUp workspace."""

    id: str
    name: str
    color: Optional[str] = None
    avatar: Optional[str] = None
    members: List[Dict[str, Any]] = Field(default_factory=list)
    private: bool = False
    statuses: List[Dict[str, Any]] = Field(default_factory=list)
    multiple_assignees: bool = False
    features: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(None, alias="date_joined")
    updated_at: Optional[datetime] = Field(None, alias="date_joined")

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, arbitrary_types_allowed=True
    )


class CustomItemAvatar(BaseModel):
    """Represents an avatar for a custom task type"""

    source: Optional[str] = None
    value: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class CustomItem(BaseModel):
    """Represents a custom task type in a workspace"""

    id: int
    name: str
    name_plural: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[CustomItemAvatar] = None

    model_config = ConfigDict(populate_by_name=True)
