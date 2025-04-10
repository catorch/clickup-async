"""
Guest models for ClickUp API.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class Guest(BaseModel):
    """Model representing a ClickUp guest user.
    Note: Most fields are based on the User model, with added guest-specific permissions.
    """

    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    color: Optional[str] = None
    initials: Optional[str] = None
    profilePicture: Optional[str] = None
    # Guest specific permissions (as returned by Get/Edit)
    can_edit_tags: Optional[bool] = None
    can_see_time_spent: Optional[bool] = None
    can_see_time_estimated: Optional[bool] = None
    can_create_views: Optional[bool] = None
    custom_role_id: Optional[int] = None
    # Other potential user fields (optional)
    role: Optional[int] = None
    last_active: Optional[str] = None
    date_joined: Optional[str] = None
    date_invited: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
