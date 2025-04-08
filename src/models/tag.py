"""
Tag models for ClickUp API.

This module contains models related to task tags in ClickUp.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Tag(BaseModel):
    """Model representing a ClickUp task tag."""

    name: str
    tag_fg: Optional[str] = None
    tag_bg: Optional[str] = None
    creator: Optional[int] = None  # User ID of the creator

    model_config = ConfigDict(populate_by_name=True)
