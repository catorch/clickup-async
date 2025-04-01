"""
Checklist models for ClickUp API.

This module contains models related to checklists in ClickUp tasks.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import make_list_factory
from .user import User


class ChecklistItem(BaseModel):
    """Represents an item in a checklist"""

    id: str
    name: str
    orderindex: Optional[int] = None
    assignee: Optional[User] = None
    resolved: Optional[bool] = None
    parent: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class Checklist(BaseModel):
    """Represents a checklist in a task"""

    id: str
    task_id: Optional[str] = None
    name: str
    orderindex: Optional[int] = None
    resolved: Optional[int] = None
    unresolved: Optional[int] = None
    items: List[ChecklistItem] = Field(default_factory=make_list_factory(ChecklistItem))

    model_config = ConfigDict(populate_by_name=True)
