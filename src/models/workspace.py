"""
Workspace models for ClickUp API.

This module contains models related to workspaces (teams) in ClickUp.
"""

from datetime import datetime
from enum import Enum
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


class AuditLogApplicability(str, Enum):
    """Type of logs to filter by."""

    AUTH_AND_SECURITY = "auth-and-security"
    USER_ACTIVITY = "user-activity"


class AuditLogEventStatus(str, Enum):
    """Status of events to filter by."""

    SUCCESS = "success"
    FAILED = "failed"
    STARTED = "started"
    COMPLETED = "completed"
    ERROR = "error"
    SYSTEM_ERROR = "system_error"


class AuditLogPageDirection(str, Enum):
    """Pagination direction."""

    BEFORE = "before"
    AFTER = "after"


class AuditLogFilter(BaseModel):
    """Filter criteria for retrieving audit logs."""

    workspace_id: str = Field(..., alias="workspaceId")
    user_id: Optional[List[str]] = Field(None, alias="userId")
    user_email: Optional[List[str]] = Field(None, alias="userEmail")
    event_type: Optional[List[str]] = Field(None, alias="eventType")
    event_status: Optional[AuditLogEventStatus] = Field(None, alias="eventStatus")
    start_time: Optional[int] = Field(None, alias="startTime")  # Unix timestamp ms
    end_time: Optional[int] = Field(None, alias="endTime")  # Unix timestamp ms
    applicability: AuditLogApplicability

    model_config = ConfigDict(
        populate_by_name=True, use_enum_values=True, arbitrary_types_allowed=True
    )


class AuditLogPagination(BaseModel):
    """Pagination settings for retrieving audit logs."""

    page_rows: Optional[int] = Field(None, alias="pageRows")
    page_timestamp: Optional[int] = Field(
        None, alias="pageTimestamp"
    )  # Unix timestamp ms
    page_direction: Optional[AuditLogPageDirection] = Field(None, alias="pageDirection")

    model_config = ConfigDict(
        populate_by_name=True, use_enum_values=True, arbitrary_types_allowed=True
    )


class GetAuditLogsRequest(BaseModel):
    """Request body model for retrieving audit logs."""

    filter: AuditLogFilter
    pagination: AuditLogPagination

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


# Assuming AuditLogEntry is a dictionary for now as the response structure isn't fully defined
# Define a more specific model if the response structure becomes clear.
AuditLogEntry = Dict[str, Any]
