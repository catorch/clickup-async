"""
Attachment models for ClickUp API.

This module contains models related to attachments in ClickUp.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class Attachment(BaseModel):
    """Represents a file attachment"""

    id: str
    date: str
    title: str
    extension: str
    thumbnail_small: Optional[str] = None
    thumbnail_large: Optional[str] = None
    url: str
    version: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)
