"""
User models for ClickUp API.

This module contains models related to users and members in ClickUp.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """User model for ClickUp API."""

    id: int
    username: str
    email: Optional[str] = None
    color: Optional[str] = None
    profilePicture: Optional[str] = None
    initials: Optional[str] = None
    role: Optional[int] = None
    custom_role: Optional[str] = None
    last_active: Optional[str] = None
    date_joined: Optional[str] = None
    date_invited: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class Member(BaseModel):
    """Member model for ClickUp API."""

    user: User

    model_config = ConfigDict(extra="allow")
