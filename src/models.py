"""
ClickUp API Models

This module contains Pydantic models for the ClickUp API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Sequence, TypeVar, Union, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    priority: Optional[Union[int, str]] = None  # Allow both integer and string
    color: Optional[str] = None
    orderindex: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        """Convert string priority to integer if needed"""
        if isinstance(self.priority, str):
            priority_map = {
                "urgent": 1,
                "high": 2,
                "normal": 3,
                "low": 4,
            }
            self.priority = priority_map.get(
                self.priority.lower(), 3
            )  # Default to normal

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
    team_id: Optional[str] = None

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
    """A comment on a task or list."""

    id: Optional[Union[str, int]] = None
    text: Optional[str] = None
    comment_text: Optional[str] = None
    comment_content: Optional[str] = Field(None, alias="comment_text")
    user: Optional[Dict[str, Any]] = None
    resolved: bool = False
    assignee: Optional[Union[str, Dict[str, Any]]] = None
    assigned_by: Optional[Dict[str, Any]] = None
    date: Optional[Union[str, int]] = None
    parent: Optional[str] = None
    reactions: Optional[List[Dict[str, Any]]] = None
    attributes: Optional[Dict[str, Any]] = None
    comment: Optional[List[Dict[str, Any]]] = None
    original_comment_text: Optional[str] = None
    original_assignee: Optional[str] = None
    hist_id: Optional[str] = None
    reply_count: Optional[int] = None
    group_assignee: Optional[Any] = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        """Convert id to string if it's an integer."""
        if v is None:
            return None
        return str(v)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        """Convert date to string if it's an integer."""
        if v is None:
            return None
        return str(v)

    def model_post_init(self, __context: Any) -> None:
        """Handle comment text from API response."""
        # Handle nested comment structure
        if self.comment and isinstance(self.comment, list) and len(self.comment) > 0:
            comment_data = self.comment[0]
            if "text" in comment_data:
                self.text = comment_data["text"]
            if "comment_text" in comment_data:
                self.comment_text = comment_data["comment_text"]

        # Handle text/comment_text synchronization
        if self.comment_text is None and self.text is not None:
            self.comment_text = self.text
        elif self.text is None and self.comment_text is not None:
            self.text = self.comment_text

        # Use original values if current ones are None
        if self.assignee is None and self.original_assignee is not None:
            self.assignee = self.original_assignee

        if not self.text and not self.comment_text and self.original_comment_text:
            self.text = self.original_comment_text
            self.comment_text = self.original_comment_text

        # Ensure at least one text field is set
        if not self.text and not self.comment_text and not self.original_comment_text:
            self.text = ""
            self.comment_text = ""

        # Handle resolved value
        if isinstance(self.resolved, str):
            self.resolved = self.resolved.lower() == "true"

    @property
    def content(self) -> str:
        """Get the comment text content."""
        if self.text:
            return self.text
        if self.comment_text:
            return self.comment_text
        if self.comment_content:
            return self.comment_content

        if self.comment and isinstance(self.comment, list) and len(self.comment) > 0:
            comment_data = self.comment[0]
            if "text" in comment_data:
                return comment_data["text"]
            if "comment_text" in comment_data:
                return comment_data["comment_text"]

        if self.attributes and isinstance(self.attributes, dict):
            if "text" in self.attributes:
                return self.attributes["text"]

        if self.original_comment_text:
            return self.original_comment_text

        return ""

    @property
    def effective_assignee(self) -> Optional[Union[str, Dict[str, Any]]]:
        """Get the effective assignee of the comment."""
        if self.assignee is not None:
            return self.assignee
        return getattr(self, "original_assignee", None)

    model_config = ConfigDict(
        populate_by_name=True, extra="allow", validate_assignment=True
    )


class Task(BaseModel):
    """A ClickUp task"""

    id: str
    name: str
    description: Optional[str] = None
    status: Optional[Status] = None
    orderindex: Optional[str] = None
    date_created: Optional[str] = None
    date_updated: Optional[str] = None
    date_closed: Optional[str] = None
    date_done: Optional[str] = None
    creator: Optional[User] = None
    assignees: List[User] = []
    checklists: List[Any] = []
    tags: List[str] = []
    parent: Optional[str] = None
    priority: Optional[PriorityObject] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    time_estimate: Optional[str] = None
    time_spent: Optional[Union[str, int]] = None  # Allow both string and integer
    custom_fields: List[Any] = []
    list: Optional[Location] = None
    folder: Optional[Location] = None
    space: Optional[Location] = None
    url: Optional[str] = None
    attachments: Optional[List[Any]] = None
    custom_id: Optional[str] = None
    text_content: Optional[str] = None
    archived: bool = False
    markdown_content: Optional[str] = None
    points: Optional[float] = None
    group_assignees: Optional[List[str]] = None
    watchers: Optional[List[Union[str, Dict[str, Any]]]] = (
        None  # Allow both string and user object
    )
    links_to: Optional[str] = None
    custom_item_id: Optional[int] = None
    custom_task_ids: bool = False
    team_id: Optional[str] = None

    @property
    def priority_value(self) -> Optional[Priority]:
        """Get the priority as an enum value"""
        if not self.priority:
            return None
        try:
            if isinstance(self.priority.priority, str):
                return Priority(int(self.priority.priority))
            return Priority(self.priority.priority)
        except (ValueError, TypeError):
            return None

    def model_post_init(self, __context: Any) -> None:
        """Post initialization hook to ensure status is properly set"""
        if isinstance(self.status, dict):
            self.status = Status.model_validate(self.status)
        # Convert time_spent to string if it's an integer
        if isinstance(self.time_spent, int):
            self.time_spent = str(self.time_spent)
        # Convert watchers to list of strings if they're user objects
        if self.watchers and isinstance(self.watchers[0], dict):
            self.watchers = [
                str(w.get("id", "")) for w in self.watchers if isinstance(w, dict)
            ]

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
    def created_at(self) -> Optional[datetime]:
        """Get the creation date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(
                int(self.date_created) / 1000, tz=timezone.utc
            ).replace(tzinfo=None)
            if self.date_created
            else None
        )

    @property
    def updated_at(self) -> Optional[datetime]:
        """Get the last update date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(
                int(self.date_updated) / 1000, tz=timezone.utc
            ).replace(tzinfo=None)
            if self.date_updated
            else None
        )

    @property
    def closed_at(self) -> Optional[datetime]:
        """Get the closing date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(
                int(self.date_closed) / 1000, tz=timezone.utc
            ).replace(tzinfo=None)
            if self.date_closed
            else None
        )

    @property
    def done_at(self) -> Optional[datetime]:
        """Get the completion date as a datetime object (if available)"""
        return (
            datetime.fromtimestamp(int(self.date_done) / 1000, tz=timezone.utc).replace(
                tzinfo=None
            )
            if self.date_done
            else None
        )

    model_config = ConfigDict(populate_by_name=True)


class TimeEntry(BaseModel):
    """Model representing a time entry."""

    id: Optional[Union[str, int]] = None
    wid: Optional[Union[str, int]] = None
    task_id: Optional[Union[str, int]] = None
    start: Optional[Union[str, int]] = None
    end: Optional[Union[str, int]] = None
    duration: Optional[str] = None
    billable: Optional[bool] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    at: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None
    task: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        """Convert integer IDs and timestamps to strings."""
        if isinstance(self.id, int):
            self.id = str(self.id)
        if isinstance(self.wid, int):
            self.wid = str(self.wid)
        if isinstance(self.task_id, int):
            self.task_id = str(self.task_id)
        if isinstance(self.start, int):
            self.start = str(self.start)
        if isinstance(self.end, int):
            self.end = str(self.end)
        if isinstance(self.duration, int):
            self.duration = str(self.duration)
        # Extract task_id from task if available
        if self.task and isinstance(self.task, dict) and "id" in self.task:
            self.task_id = str(self.task["id"])

    @property
    def start_datetime(self) -> Optional[datetime]:
        """Convert start timestamp to datetime."""
        if not self.start:
            return None
        try:
            return datetime.fromtimestamp(int(self.start) / 1000)
        except (ValueError, TypeError):
            return None

    @property
    def end_datetime(self) -> Optional[datetime]:
        """Convert end timestamp to datetime."""
        if not self.end:
            return None
        try:
            return datetime.fromtimestamp(int(self.end) / 1000)
        except (ValueError, TypeError):
            return None

    @classmethod
    def from_timestamp(cls, timestamp: int, **kwargs: Any) -> "TimeEntry":
        """Create a TimeEntry from a timestamp."""
        return cls(start=str(timestamp), **kwargs)

    model_config = ConfigDict(populate_by_name=True)


class TimeInStatus(BaseModel):
    """Represents time spent in a status for a task"""

    status: str
    time_in_status: int  # Time in milliseconds
    total_time: int  # Total time in milliseconds

    model_config = ConfigDict(populate_by_name=True)


class TaskTimeInStatus(BaseModel):
    """Represents time in status information for a task"""

    task_id: str
    times: List[TimeInStatus] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class BulkTimeInStatus(BaseModel):
    """Represents time in status information for multiple tasks"""

    tasks: List[TaskTimeInStatus] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class PaginatedResponse(Sequence[T]):
    """A paginated response that acts like a sequence but can fetch more pages."""

    def __init__(
        self,
        items: List[T],
        client: Any,
        next_page_params: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the paginated response.

        Args:
            items: The items in the current page
            client: The ClickUp client instance
            next_page_params: Parameters for fetching the next page
        """
        self._items = items
        self._client = client
        self._next_page_params = next_page_params

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        return self._items[index]

    @property
    def has_more(self) -> bool:
        """Whether there are more pages available."""
        return self._next_page_params is not None

    async def next_page(self) -> Optional["PaginatedResponse[T]"]:
        """Retrieve the next page of results if available"""
        if not self.has_more or not self._next_page_params:
            return None

        # Get the list_id from the parameters
        list_id = self._next_page_params.get("list_id")
        if not list_id:
            return None

        # Make the request using the same endpoint
        response = await self._client._request(
            "GET",
            f"list/{list_id}/task",
            params=self._next_page_params,
        )

        # Create a new paginated response
        items = [
            cast(T, self._items[0].__class__.model_validate(item))
            for item in response.get("tasks", [])
        ]
        next_page_params = None
        if response.get("has_more"):
            next_page_params = dict(self._next_page_params)
            next_page_params["page"] = self._next_page_params["page"] + 1

        return PaginatedResponse(items, self._client, next_page_params)


class KeyResultType(str, Enum):
    """Types of key results (targets) in ClickUp goals"""

    NUMBER = "number"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    AUTOMATIC = "automatic"


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
