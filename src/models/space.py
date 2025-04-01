"""
Space models for ClickUp API.

This module contains models related to spaces in ClickUp.
"""

from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .user import Member


class Status(BaseModel):
    """Status configuration for a Space."""

    id: str
    status: str
    type: str
    orderindex: Union[int, str]
    color: str

    model_config = ConfigDict(extra="allow")


class FeatureConfig(BaseModel):
    """Configuration for a feature."""

    enabled: bool = True

    model_config = ConfigDict(extra="allow")


class Features(BaseModel):
    """Features configuration for a Space."""

    due_dates: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    time_tracking: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    tags: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    time_estimates: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    checklists: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    custom_fields: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    remap_dependencies: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    dependency_warning: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )
    portfolios: Optional[FeatureConfig] = Field(
        default_factory=lambda: FeatureConfig(enabled=True)
    )

    model_config = ConfigDict(extra="allow")


class Space(BaseModel):
    """
    Space model for ClickUp API.

    A Space is a high-level container that helps organize your work. Each Space can have its own
    set of features, privacy settings, and member access controls.
    """

    id: str
    name: str
    color: Optional[str] = None
    private: bool = False
    admin_can_manage: Optional[bool] = True
    avatar: Optional[str] = None
    members: List[Member] = Field(default_factory=list)
    statuses: List[Status] = Field(default_factory=list)
    multiple_assignees: bool = False
    features: Features = Field(default_factory=Features)
    archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    team_id: Optional[str] = None

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )
