"""
Webhook models for ClickUp API.

This module contains models related to webhooks in ClickUp.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class WebhookHealth(BaseModel):
    """Model representing the health status of a webhook."""

    status: Optional[str] = None
    fail_count: Optional[int] = None


class Webhook(BaseModel):
    """Model representing a ClickUp webhook."""

    id: str
    userid: Optional[int] = None
    team_id: Optional[int] = None
    endpoint: str
    client_id: Optional[str] = None
    events: List[str]
    task_id: Optional[str] = None
    list_id: Optional[int] = None
    folder_id: Optional[int] = None
    space_id: Optional[int] = None
    health: Optional[WebhookHealth] = None
    secret: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
