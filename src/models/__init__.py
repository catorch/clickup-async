"""
ClickUp API Models.

This module contains Pydantic models for the ClickUp API.
"""

from .attachment import Attachment
from .base import KeyResultType, PaginatedResponse, Priority, make_list_factory
from .checklist import Checklist, ChecklistItem
from .comment import Comment, CommentText
from .common import CustomField, Location, PriorityObject
from .doc import Doc, DocPage, DocPageListing
from .folder import Folder
from .goal import Goal, KeyResult
from .list import TaskList
from .space import FeatureConfig, Features, Space, Status
from .task import BulkTimeInStatus, Task, TaskTimeInStatus, TimeInStatus
from .time import TimeEntry
from .user import Member, User
from .workspace import CustomItem, CustomItemAvatar, Workspace

__all__ = [
    # Base
    "KeyResultType",
    "PaginatedResponse",
    "Priority",
    "make_list_factory",
    # User
    "Member",
    "User",
    # Workspace
    "CustomItem",
    "CustomItemAvatar",
    "Workspace",
    # Space
    "Features",
    "FeatureConfig",
    "Space",
    "Status",
    # Common
    "CustomField",
    "Location",
    "PriorityObject",
    # Folder
    "Folder",
    # List
    "TaskList",
    # Task
    "BulkTimeInStatus",
    "Task",
    "TaskTimeInStatus",
    "TimeInStatus",
    # Checklist
    "Checklist",
    "ChecklistItem",
    # Comment
    "Comment",
    "CommentText",
    # Attachment
    "Attachment",
    # Time
    "TimeEntry",
    # Goal
    "Goal",
    "KeyResult",
    # Doc
    "Doc",
    "DocPage",
    "DocPageListing",
]
