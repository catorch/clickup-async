"""
Goal models for ClickUp API.

This module contains models related to goals and key results in ClickUp.
"""

from typing import List, Optional

from pydantic import BaseModel

from .base import KeyResultType


class KeyResult(BaseModel):
    """A key result (target) in a ClickUp goal"""

    id: str
    name: str
    owners: List[str] = []  # Make owners optional with empty list default
    type: KeyResultType
    steps_start: int = 0  # Make optional with default value
    steps_end: int = 0  # Make optional with default value
    steps_current: Optional[int] = None
    unit: str
    task_ids: Optional[List[str]] = None
    list_ids: Optional[List[str]] = None
    note: Optional[str] = None


class Goal(BaseModel):
    """A ClickUp goal"""

    id: str
    name: str
    team_id: str
    due_date: int
    description: str
    multiple_owners: bool
    owners: List[str]
    color: str
    key_results: Optional[List[KeyResult]] = None
    date_created: Optional[int] = None
    date_updated: Optional[int] = None
    creator: Optional[int] = None
    completed: Optional[bool] = None
