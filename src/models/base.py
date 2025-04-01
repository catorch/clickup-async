"""
Base models for ClickUp API.

This module contains base models and common types used across the ClickUp API client.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, IntEnum
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


class KeyResultType(str, Enum):
    """Types of key results (targets) in ClickUp goals"""

    NUMBER = "number"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    AUTOMATIC = "automatic"


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
        items = []
        for item in response.get("tasks", []):
            # Use the class of the first item to create new items
            item_class = self._items[0].__class__
            items.append(item_class.model_validate(item))

        next_page_params = None
        if response.get("has_more"):
            next_page_params = dict(self._next_page_params)
            next_page_params["page"] = self._next_page_params["page"] + 1

        return PaginatedResponse(items, self._client, next_page_params)
