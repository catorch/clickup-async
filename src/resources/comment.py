"""
Comment resources for ClickUp API.

This module contains resource classes for interacting with comment-related endpoints.
"""

from typing import List, Optional

from ..models import Comment
from .base import BaseResource


class CommentResource(BaseResource):
    """Comment-related API endpoints."""

    async def get_task_comments(
        self,
        task_id: Optional[str] = None,
        start: Optional[int] = None,
        start_id: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> List[Comment]:
        """
        Get comments for a task.

        Args:
            task_id: ID of the task (uses the one set in the client context if not provided)
            start: Unix timestamp in milliseconds to get comments from
            start_id: Comment ID to start from
            custom_task_ids: Whether to use custom task IDs
            team_id: Team ID (required if using custom task IDs)

        Returns:
            List of Comment objects

        Raises:
            ValueError: If task_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task doesn't exist
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        params = {}
        if start is not None:
            params["start"] = str(start)
        if start_id is not None:
            params["start_id"] = start_id
        if custom_task_ids:
            params["custom_task_ids"] = str(custom_task_ids).lower()
            if team_id:
                params["team_id"] = team_id

        response = await self._request("GET", f"task/{task_id}/comment", params=params)
        return [
            Comment.model_validate(comment) for comment in response.get("comments", [])
        ]

    async def create_task_comment(
        self,
        comment_text: str,
        task_id: Optional[str] = None,
        assignee: Optional[str] = None,
        group_assignee: Optional[str] = None,
        notify_all: bool = True,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> Comment:
        """
        Add a comment to a task.

        Args:
            comment_text: Text content of the comment
            task_id: ID of the task (uses the one set in the client context if not provided)
            assignee: User ID to assign the comment to
            group_assignee: Group ID to assign the comment to
            notify_all: Whether to notify everyone
            custom_task_ids: Whether to use custom task IDs
            team_id: Team ID (required if using custom task IDs)

        Returns:
            The created Comment object

        Raises:
            ValueError: If task_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        data = {
            "comment_text": comment_text,
            "notify_all": str(notify_all).lower(),
        }

        if assignee:
            data["assignee"] = assignee
        if group_assignee:
            data["group_assignee"] = group_assignee

        params = {}
        if custom_task_ids:
            params["custom_task_ids"] = str(custom_task_ids).lower()
            if team_id:
                params["team_id"] = team_id

        response = await self._request(
            "POST", f"task/{task_id}/comment", data=data, params=params
        )

        # Add the original values to the response before validation
        response["original_comment_text"] = comment_text
        if assignee:
            response["original_assignee"] = assignee

        # Make sure comment data is correctly structured for model validation
        if (
            "id" in response
            and "text" not in response
            and "comment_text" not in response
        ):
            response["text"] = comment_text
            response["comment_text"] = comment_text

        return Comment.model_validate(response)

    async def get_chat_view_comments(
        self,
        view_id: str,
        start: Optional[int] = None,
        start_id: Optional[str] = None,
    ) -> List[Comment]:
        """
        Get comments from a Chat view.

        Args:
            view_id: ID of the Chat view
            start: Unix timestamp in milliseconds to get comments from
            start_id: Comment ID to start from

        Returns:
            List of Comment objects

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the view doesn't exist
            ClickUpError: For other API errors
        """
        params = {}
        if start is not None:
            params["start"] = str(start)
        if start_id is not None:
            params["start_id"] = start_id

        response = await self._request("GET", f"view/{view_id}/comment", params=params)
        return [
            Comment.model_validate(comment) for comment in response.get("comments", [])
        ]

    async def create_chat_view_comment(
        self,
        view_id: str,
        comment_text: str,
        notify_all: bool = True,
    ) -> Comment:
        """
        Add a comment to a Chat view.

        Args:
            view_id: ID of the Chat view
            comment_text: Text content of the comment
            notify_all: Whether to notify everyone

        Returns:
            The created Comment object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the view doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {
            "comment_text": comment_text,
            "notify_all": str(notify_all).lower(),
        }

        response = await self._request("POST", f"view/{view_id}/comment", data=data)
        return Comment.model_validate(response)

    async def get_list_comments(
        self,
        list_id: Optional[str] = None,
        start: Optional[int] = None,
        start_id: Optional[str] = None,
    ) -> List[Comment]:
        """
        Get comments from a List.

        Args:
            list_id: ID of the List (uses the one set in the client context if not provided)
            start: Unix timestamp in milliseconds to get comments from
            start_id: Comment ID to start from

        Returns:
            List of Comment objects

        Raises:
            ValueError: If list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = self._get_context_id("_list_id", list_id)
        if not list_id:
            raise ValueError("List ID must be provided")

        params = {}
        if start is not None:
            params["start"] = str(start)
        if start_id is not None:
            params["start_id"] = start_id

        response = await self._request("GET", f"list/{list_id}/comment", params=params)
        return [
            Comment.model_validate(comment) for comment in response.get("comments", [])
        ]

    async def create_list_comment(
        self,
        comment_text: str,
        list_id: Optional[str] = None,
        assignee: Optional[str] = None,
        group_assignee: Optional[str] = None,
        notify_all: bool = True,
    ) -> Comment:
        """
        Add a comment to a list.

        Args:
            comment_text: Text content of the comment
            list_id: ID of the list (uses the one set in the client context if not provided)
            assignee: User ID to assign the comment to
            group_assignee: Group ID to assign the comment to
            notify_all: Whether to notify everyone

        Returns:
            The created Comment object

        Raises:
            ValueError: If list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        list_id = self._get_context_id("_list_id", list_id)
        if not list_id:
            raise ValueError("List ID must be provided")

        data = {
            "comment_text": comment_text,
            "notify_all": str(notify_all).lower(),
        }

        if assignee:
            data["assignee"] = assignee
        if group_assignee:
            data["group_assignee"] = group_assignee

        response = await self._request("POST", f"list/{list_id}/comment", data=data)

        # Add the original values to the response before validation
        response["original_comment_text"] = comment_text
        if assignee:
            response["original_assignee"] = assignee

        # Make sure comment data is correctly structured for model validation
        if (
            "id" in response
            and "text" not in response
            and "comment_text" not in response
        ):
            response["text"] = comment_text
            response["comment_text"] = comment_text

        return Comment.model_validate(response)

    async def update(
        self,
        comment_id: str,
        comment_text: str,
        assignee: Optional[str] = None,
        group_assignee: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> Comment:
        """
        Update a comment.

        Args:
            comment_id: ID of the comment to update
            comment_text: New text content for the comment
            assignee: User ID to assign the comment to
            group_assignee: Group ID to assign the comment to
            resolved: Whether the comment is resolved

        Returns:
            The updated Comment object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the comment doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {"comment_text": comment_text}

        if assignee is not None:
            data["assignee"] = assignee
        if group_assignee is not None:
            data["group_assignee"] = group_assignee
        if resolved is not None:
            data["resolved"] = str(resolved).lower()

        response = await self._request("PUT", f"comment/{comment_id}", data=data)

        # Add the original values to the response before validation
        response["original_comment_text"] = comment_text
        if assignee:
            response["original_assignee"] = assignee

        # The ClickUp API returns an empty response for successful comment updates
        # So we need to manually set the values
        if "text" not in response:
            response["text"] = comment_text
        if "comment_text" not in response:
            response["comment_text"] = comment_text
        if resolved is not None:
            response["resolved"] = resolved

        return Comment.model_validate(response)

    async def delete(self, comment_id: str) -> bool:
        """
        Delete a comment.

        Args:
            comment_id: ID of the comment to delete

        Returns:
            True if successful

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the comment doesn't exist
            ClickUpError: For other API errors
        """
        await self._request("DELETE", f"comment/{comment_id}")
        return True

    async def get_threaded_comments(self, comment_id: str) -> List[Comment]:
        """
        Get threaded comments (replies) for a comment.

        Args:
            comment_id: ID of the parent comment

        Returns:
            List of Comment objects (excluding the parent comment)

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the comment doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request("GET", f"comment/{comment_id}/reply")
        return [
            Comment.model_validate(comment) for comment in response.get("comments", [])
        ]

    async def create_threaded_comment(
        self,
        comment_id: str,
        comment_text: str,
        assignee: Optional[str] = None,
        group_assignee: Optional[str] = None,
        notify_all: bool = True,
    ) -> Comment:
        """
        Add a threaded comment (reply) to an existing comment.

        Args:
            comment_id: ID of the parent comment
            comment_text: Text content of the comment
            assignee: User ID to assign the comment to
            group_assignee: Group ID to assign the comment to
            notify_all: Whether to notify everyone

        Returns:
            The created Comment object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the comment doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {
            "comment_text": comment_text,
            "notify_all": str(notify_all).lower(),
        }

        if assignee:
            data["assignee"] = assignee
        if group_assignee:
            data["group_assignee"] = group_assignee

        response = await self._request("POST", f"comment/{comment_id}/reply", data=data)

        # Add the original values to the response before validation
        response["original_comment_text"] = comment_text
        if assignee:
            response["original_assignee"] = assignee

        # Make sure comment data is correctly structured for model validation
        if (
            "id" in response
            and "text" not in response
            and "comment_text" not in response
        ):
            response["text"] = comment_text
            response["comment_text"] = comment_text

        return Comment.model_validate(response)
