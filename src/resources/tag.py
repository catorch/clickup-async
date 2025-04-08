"""
Tag resources for ClickUp API.

This module contains resource classes for interacting with tag-related endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from ..exceptions import ResourceNotFound, ValidationError
from ..models.tag import Tag
from .base import BaseResource

logger = logging.getLogger("clickup")


class TagResource(BaseResource):
    """Tag-related API endpoints (primarily Space Tags)."""

    async def get_space_tags(self, space_id: str) -> List[Tag]:
        """
        Get all tags for a specific Space.

        Args:
            space_id: ID of the Space.

        Returns:
            List of Tag objects.

        Raises:
            AuthenticationError: If authentication fails.
            ResourceNotFound: If the Space doesn't exist.
            ClickUpError: For other API errors.
        """
        response = await self._request("GET", f"space/{space_id}/tag")
        # API returns tags in a list under the "tags" key
        tags_data = response.get("tags", [])
        return [Tag.model_validate(tag) for tag in tags_data]

    async def create_space_tag(
        self,
        space_id: str,
        name: str,
        tag_fg: Optional[str] = None,
        tag_bg: Optional[str] = None,
    ) -> None:
        """
        Create a new tag within a Space.

        Note: The API returns a 200 OK with an empty body on success.

        Args:
            space_id: ID of the Space.
            name: Name of the new tag.
            tag_fg: Optional foreground color hex code.
            tag_bg: Optional background color hex code.

        Raises:
            AuthenticationError: If authentication fails.
            ResourceNotFound: If the Space doesn't exist.
            ValidationError: If the request data is invalid (e.g., duplicate name).
            ClickUpError: For other API errors.
        """
        tag_data: Dict[str, Any] = {"name": name}
        if tag_fg:
            tag_data["tag_fg"] = tag_fg
        if tag_bg:
            tag_data["tag_bg"] = tag_bg

        await self._request("POST", f"space/{space_id}/tag", data={"tag": tag_data})
        # No return value as API gives empty body on success

    async def edit_space_tag(
        self,
        space_id: str,
        original_tag_name: str,
        new_name: Optional[str] = None,
        new_tag_fg: Optional[str] = None,
        new_tag_bg: Optional[str] = None,
    ) -> None:
        """
        Edit an existing tag within a Space.

        Note: The API returns a 200 OK with an empty body on success.

        Args:
            space_id: ID of the Space.
            original_tag_name: The current name of the tag to edit.
            new_name: The new name for the tag.
            new_tag_fg: The new foreground color hex code.
            new_tag_bg: The new background color hex code.

        Raises:
            ValueError: If no new values are provided for update.
            AuthenticationError: If authentication fails.
            ResourceNotFound: If the Space or tag doesn't exist.
            ValidationError: If the request data is invalid.
            ClickUpError: For other API errors.
        """
        tag_data: Dict[str, Any] = {}
        if new_name is not None:
            tag_data["name"] = new_name
        if new_tag_fg is not None:
            tag_data["tag_fg"] = new_tag_fg
        if new_tag_bg is not None:
            tag_data["tag_bg"] = new_tag_bg

        if not tag_data:
            raise ValueError(
                "At least one new value (name, fg, bg) must be provided for editing."
            )

        await self._request(
            "PUT", f"space/{space_id}/tag/{original_tag_name}", data={"tag": tag_data}
        )
        # No return value as API gives empty body on success

    async def delete_space_tag(self, space_id: str, tag_name: str) -> None:
        """
        Delete a tag from a Space.

        Note: The API returns a 200 OK with an empty body on success.

        Args:
            space_id: ID of the Space.
            tag_name: The name of the tag to delete.

        Raises:
            AuthenticationError: If authentication fails.
            ResourceNotFound: If the Space or tag doesn't exist.
            ClickUpError: For other API errors.
        """
        # The API docs incorrectly show a body param for DELETE; it should have no body.
        await self._request("DELETE", f"space/{space_id}/tag/{tag_name}")
        # No return value as API gives empty body on success
