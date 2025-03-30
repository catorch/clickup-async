"""
ClickUp API Models

This module contains Pydantic models for the ClickUp API.
"""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, Generic, List, Optional, Sequence, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)
TList = TypeVar("TList")


def make_list_factory(t: type) -> Any:
    """Create a type-safe list factory"""
    return lambda: []


class Priority(IntEnum):
    """Task priority levels"""

    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


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


class Status(BaseModel):
    """Status configuration for a Space."""

    id: str
    status: str
    type: str
    orderindex: Union[int, str]
    color: str

    model_config = ConfigDict(extra="allow")


class Location(BaseModel):
    """Represents a location reference (folder/space) in a task or list"""

    id: str
    name: Optional[str] = None
    hidden: Optional[bool] = None
    access: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class CustomField(BaseModel):
    """Represents a custom field"""

    id: str
    name: str
    type: str
    value: Optional[Any] = None
    type_config: Optional[Dict[str, Any]] = Field(None, alias="type_config")
    date_created: Optional[str] = None
    hide_from_guests: Optional[bool] = None
    required: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class PriorityObject(BaseModel):
    """Represents a priority object as returned by the API"""

    id: Optional[int] = None
    priority: Optional[int] = None
    color: Optional[str] = None
    orderindex: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


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

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )


class Folder(BaseModel):
    """
    Represents a folder within a space.

    A folder is a container that helps organize lists and tasks within a space.
    It can have its own statuses, task count, and visibility settings.
    """

    id: str
    name: str
    orderindex: Optional[int] = None
    override_statuses: Optional[bool] = None
    hidden: Optional[bool] = None
    space: Optional[Location] = None
    task_count: Optional[int] = None
    lists: Optional[List[Dict[str, Any]]] = None
    archived: Optional[bool] = None
    statuses: Optional[List[Status]] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    permission_level: Optional[str] = None
    content: Optional[str] = None
    multiple_assignees: Optional[bool] = None
    override_statuses: Optional[bool] = None
    custom_fields: Optional[List[Dict[str, Any]]] = None

    # Computed properties
    @property
    def created_at(self) -> Optional[datetime]:
        """Get the creation date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(int(self.date_created) / 1000)
            if self.date_created
            else None
        )

    @property
    def updated_at(self) -> Optional[datetime]:
        """Get the last update date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(int(self.date_updated) / 1000)
            if self.date_updated
            else None
        )

    model_config = ConfigDict(populate_by_name=True)


class TaskList(BaseModel):
    """Represents a list within a folder or space"""

    id: str
    name: str
    orderindex: int
    status: Optional[Dict[str, Any]] = None
    priority: Optional[PriorityObject] = None
    assignee: Optional[User] = None
    task_count: int = 0
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    folder: Optional[Location] = None
    space: Optional[Location] = None
    archived: bool = False
    override_statuses: Optional[bool] = None
    permission_level: Optional[str] = None
    content: Optional[str] = None

    # Computed properties
    @property
    def due_date_timestamp(self) -> Optional[int]:
        """Get the due date as a timestamp (if available)"""
        return int(self.due_date) if self.due_date and self.due_date.isdigit() else None

    @property
    def start_date_timestamp(self) -> Optional[int]:
        """Get the start date as a timestamp (if available)"""
        return (
            int(self.start_date)
            if self.start_date and self.start_date.isdigit()
            else None
        )

    model_config = ConfigDict(populate_by_name=True)


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


class CommentText(BaseModel):
    """Represents the text content of a comment"""

    text: str

    model_config = ConfigDict(populate_by_name=True)


class Comment(BaseModel):
    """Represents a comment on a task or list"""

    id: str
    comment: Optional[List[CommentText]] = None
    comment_text: Optional[str] = None
    user: Optional[User] = None
    resolved: Optional[bool] = None
    assignee: Optional[User] = None
    assigned_by: Optional[User] = None
    reactions: Optional[List[Dict[str, Any]]] = None
    date: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @property
    def text(self) -> str:
        """Get the comment text, handling different API response formats"""
        if self.comment_text:
            return self.comment_text
        elif isinstance(self.comment, list) and self.comment:
            return " ".join(
                item.text for item in self.comment if isinstance(item, CommentText)
            )
        return ""


class Task(BaseModel):
    """Represents a task in ClickUp"""

    id: str
    name: str
    description: Optional[str] = ""
    status: Optional[Status] = None
    orderindex: Optional[str] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    date_closed: Optional[str] = None
    date_done: Optional[str] = None
    creator: Optional[User] = None
    assignees: List[User] = Field(default_factory=make_list_factory(User))
    checklists: List[Checklist] = Field(default_factory=make_list_factory(Checklist))
    tags: List[str] = Field(default_factory=make_list_factory(str))
    parent: Optional[str] = None
    priority: Optional[PriorityObject] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    time_estimate: Optional[str] = None
    time_spent: Optional[str] = None
    custom_fields: List[CustomField] = Field(
        default_factory=make_list_factory(CustomField)
    )
    list: Optional[Location] = None
    folder: Optional[Location] = None
    space: Optional[Location] = None
    url: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    custom_id: Optional[str] = None
    text_content: Optional[str] = None
    archived: Optional[bool] = None

    # Computed properties
    @property
    def due_date_timestamp(self) -> Optional[int]:
        """Get the due date as a timestamp (if available)"""
        return int(self.due_date) if self.due_date and self.due_date.isdigit() else None

    @property
    def start_date_timestamp(self) -> Optional[int]:
        """Get the start date as a timestamp (if available)"""
        return (
            int(self.start_date)
            if self.start_date and self.start_date.isdigit()
            else None
        )

    @property
    def priority_value(self) -> Optional[Priority]:
        """Get the priority as an enum value (if available)"""
        if self.priority and self.priority.priority is not None:
            try:
                return Priority(self.priority.priority)
            except ValueError:
                return None
        return None

    model_config = ConfigDict(populate_by_name=True)


class TimeEntry(BaseModel):
    """Represents a time tracking entry"""

    id: str
    task: Optional[Task] = None
    wid: str
    user: Optional[User] = None
    billable: Optional[bool] = False
    start: Optional[str] = None
    end: Optional[str] = None
    duration: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    at: Optional[str] = None

    # Computed properties
    @property
    def start_datetime(self) -> Optional[datetime]:
        """Get the start time as a datetime object (if available)"""
        return datetime.fromtimestamp(int(self.start) / 1000) if self.start else None

    @property
    def end_datetime(self) -> Optional[datetime]:
        """Get the end time as a datetime object (if available)"""
        return datetime.fromtimestamp(int(self.end) / 1000) if self.end else None

    model_config = ConfigDict(populate_by_name=True)


class PaginatedResponse(Generic[T]):
    """Generic container for paginated API responses"""

    def __init__(
        self,
        items: Sequence[T],
        client: Any,
        next_page_params: Optional[Dict[str, Any]] = None,
    ):
        self.items: Sequence[T] = items
        self._client = client
        self._next_page_params = next_page_params
        self._has_more = next_page_params is not None

    def __iter__(self):
        yield from self.items

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> T:
        return self.items[index]

    @property
    def has_more(self) -> bool:
        """Check if there are more pages available"""
        return self._has_more

    async def next_page(self) -> Optional["PaginatedResponse[T]"]:
        """Retrieve the next page of results if available"""
        if not self._has_more or not self._next_page_params:
            return None

        # We need to recreate the API call with updated page parameter
        # The actual implementation depends on which endpoint was originally called
        # This is handled internally by the client
        return None  # This will be implemented in the client class
