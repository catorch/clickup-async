"""
View models for ClickUp API.

This module contains models related to views in ClickUp.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ParentView(BaseModel):
    """Model representing a parent of a view."""

    id: str
    # API can return integer codes for parent type (e.g., 4 for list)
    type: Union[Literal["team", "space", "folder", "list"], int]


class GroupingView(BaseModel):
    """Model representing view grouping settings."""

    model_config = ConfigDict(extra="allow")


class DivideView(BaseModel):
    """Model representing view divide settings."""

    model_config = ConfigDict(extra="allow")


class SortingView(BaseModel):
    """Model representing view sorting settings."""

    model_config = ConfigDict(extra="allow")


class FiltersView(BaseModel):
    """Model representing view filter settings."""

    model_config = ConfigDict(extra="allow")


class ColumnsView(BaseModel):
    """Model representing view column settings."""

    model_config = ConfigDict(extra="allow")


class TeamSidebarView(BaseModel):
    """Model representing view team sidebar settings."""

    model_config = ConfigDict(extra="allow")


class SettingsView(BaseModel):
    """Model representing view general settings."""

    model_config = ConfigDict(extra="allow")


class View(BaseModel):
    """Model representing a ClickUp view."""

    id: Optional[str] = None
    name: str
    type: Literal[
        "list",
        "board",
        "calendar",
        "table",
        "timeline",
        "workload",
        "activity",
        "map",
        "conversation",
        "gantt",
        "location_overview",
        "doc",
    ]
    parent: Optional[ParentView] = None
    grouping: Optional[GroupingView] = None
    divide: Optional[DivideView] = None
    sorting: Optional[SortingView] = None
    filters: Optional[FiltersView] = None
    columns: Optional[ColumnsView] = None
    team_sidebar: Optional[TeamSidebarView] = None
    settings: Optional[SettingsView] = None
    protected: Optional[bool] = None
    required: Optional[bool] = None
    user: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    created: Optional[int] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "123456",
                "name": "My Board View",
                "type": "board",
                "parent": {"id": "789012", "type": "list"},
            }
        },
    )
