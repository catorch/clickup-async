"""
List resources for ClickUp API.

This module contains resource classes for interacting with list-related endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..models import Priority, TaskList
from ..utils import convert_to_timestamp
from .base import BaseResource


class ListResource(BaseResource):
    """List-related API endpoints."""

    async def get_all(
        self,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
        archived: bool = False,
    ) -> List[TaskList]:
        """
        Get all lists in a folder or space.

        Args:
            folder_id: ID of the folder (uses the one set in the client context if not provided)
            space_id: ID of the space for folderless lists (uses the one set in the client context if not provided)
            archived: Whether to include archived lists

        Returns:
            List of TaskList objects

        Raises:
            ValueError: If neither folder_id nor space_id is provided or set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder or space doesn't exist
            ClickUpError: For other API errors
        """
        params = {"archived": str(archived).lower()}

        # First, check for folder_id
        folder_id = self._get_context_id("_folder_id", folder_id)
        if folder_id:
            response = await self._request(
                "GET", f"folder/{folder_id}/list", params=params
            )
            return [TaskList.model_validate(lst) for lst in response.get("lists", [])]

        # If no folder_id, try space_id
        space_id = self._get_context_id("_space_id", space_id)
        if space_id:
            response = await self._request(
                "GET", f"space/{space_id}/list", params=params
            )
            return [TaskList.model_validate(lst) for lst in response.get("lists", [])]

        # Neither were provided
        raise ValueError("Either folder_id or space_id must be provided")

    async def get(self, list_id: Optional[str] = None) -> TaskList:
        """
        Get details for a specific list.

        Args:
            list_id: ID of the list to fetch (uses the one set in the client context if not provided)

        Returns:
            TaskList object

        Raises:
            ValueError: If list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = self._get_context_id("_list_id", list_id)
        if not list_id:
            raise ValueError("List ID must be provided")

        response = await self._request("GET", f"list/{list_id}")
        return TaskList.model_validate(response)

    async def create(
        self,
        name: str,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
        content: Optional[str] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        priority: Optional[Union[int, Priority]] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
    ) -> TaskList:
        """
        Create a new list in a folder or space.

        Args:
            name: Name of the new list
            folder_id: ID of the folder (uses the one set in the client context if not provided)
            space_id: ID of the space for folderless lists (uses the one set in the client context if not provided)
            content: Description of the list
            due_date: Due date (string, timestamp, or datetime)
            priority: Priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            assignee: Default assignee ID
            status: Default status

        Returns:
            The created TaskList object

        Raises:
            ValueError: If neither folder_id nor space_id is provided or set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the folder or space doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {"name": name}

        if content is not None:
            data["content"] = content
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = str(priority.value)
            else:
                data["priority"] = str(priority)
        if assignee is not None:
            data["assignee"] = assignee
        if status is not None:
            data["status"] = status

        # First, check for folder_id
        folder_id = self._get_context_id("_folder_id", folder_id)
        if folder_id:
            response = await self._request(
                "POST", f"folder/{folder_id}/list", data=data
            )
            return TaskList.model_validate(response)

        # If no folder_id, try space_id
        space_id = self._get_context_id("_space_id", space_id)
        if space_id:
            response = await self._request("POST", f"space/{space_id}/list", data=data)
            return TaskList.model_validate(response)

        # Neither were provided
        raise ValueError("Either folder_id or space_id must be provided")

    async def update(
        self,
        list_id: Optional[str] = None,
        name: Optional[str] = None,
        content: Optional[str] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        due_date_time: Optional[bool] = None,
        priority: Optional[Union[int, Priority]] = None,
        assignee: Optional[str] = None,
        unset_status: Optional[bool] = None,
    ) -> TaskList:
        """
        Update an existing list.

        Args:
            list_id: ID of the list to update (uses the one set in the client context if not provided)
            name: New name for the list
            content: New description for the list
            due_date: New due date (string, timestamp, or datetime)
            due_date_time: Whether the due date includes time
            priority: New priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            assignee: New default assignee ID
            unset_status: Whether to unset the default status

        Returns:
            The updated TaskList object

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

        data = {}
        if name is not None:
            data["name"] = name
        if content is not None:
            data["content"] = content
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if due_date_time is not None:
            data["due_date_time"] = str(due_date_time).lower()
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = str(priority.value)
            else:
                data["priority"] = str(priority)
        if assignee is not None:
            data["assignee"] = assignee
        if unset_status is not None:
            data["unset_status"] = str(unset_status).lower()

        response = await self._request("PUT", f"list/{list_id}", data=data)
        return TaskList.model_validate(response)

    async def delete(self, list_id: Optional[str] = None) -> bool:
        """
        Delete a list.

        Args:
            list_id: ID of the list to delete (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = self._get_context_id("_list_id", list_id)
        if not list_id:
            raise ValueError("List ID must be provided")

        await self._request("DELETE", f"list/{list_id}")
        return True

    async def add_task(
        self,
        task_id: Optional[str] = None,
        list_id: Optional[str] = None,
    ) -> bool:
        """
        Add a task to an additional list.
        Note: This endpoint requires the Tasks in Multiple List ClickApp to be enabled.

        Args:
            task_id: ID of the task to add (uses the one set in the client context if not provided)
            list_id: ID of the list to add the task to (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If task_id or list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task or list doesn't exist
            ClickUpError: If the Tasks in Multiple List ClickApp is not enabled or for other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        list_id = self._get_context_id("_list_id", list_id)

        if not task_id:
            raise ValueError("Task ID must be provided")
        if not list_id:
            raise ValueError("List ID must be provided")

        await self._request("POST", f"list/{list_id}/task/{task_id}")
        return True

    async def remove_task(
        self,
        task_id: Optional[str] = None,
        list_id: Optional[str] = None,
    ) -> bool:
        """
        Remove a task from an additional list.
        Note: You cannot remove a task from its home list.
        This endpoint requires the Tasks in Multiple List ClickApp to be enabled.

        Args:
            task_id: ID of the task to remove (uses the one set in the client context if not provided)
            list_id: ID of the list to remove the task from (uses the one set in the client context if not provided)

        Returns:
            True if successful

        Raises:
            ValueError: If task_id or list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task or list doesn't exist
            ClickUpError: If the Tasks in Multiple List ClickApp is not enabled or for other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        list_id = self._get_context_id("_list_id", list_id)

        if not task_id:
            raise ValueError("Task ID must be provided")
        if not list_id:
            raise ValueError("List ID must be provided")

        await self._request("DELETE", f"list/{list_id}/task/{task_id}")
        return True

    async def create_from_template(
        self,
        name: str,
        folder_id: Optional[str] = None,
        space_id: Optional[str] = None,
        template_id: Optional[str] = None,
        return_immediately: bool = True,
        options: Optional[Dict[str, Any]] = None,
    ) -> TaskList:
        """
        Create a new list using a list template in a folder or space.
        This request runs synchronously by default with return_immediately=true.
        The request returns the future List ID immediately, but the List might not be created
        at the time of the request returning.

        Args:
            name: Name of the new list
            folder_id: ID of the folder (uses the one set in the client context if not provided)
            space_id: ID of the space (uses the one set in the client context if not provided)
            template_id: ID of the template (uses the one set in the client context if not provided)
            return_immediately: Whether to return immediately without waiting for all assets to be created
            options: Additional options for creating the list from template

        Returns:
            The created TaskList object

        Raises:
            ValueError: If neither folder_id nor space_id is provided/set in context, or if template_id is missing
            AuthenticationError: If authentication fails
            ResourceNotFound: If the template, folder, or space doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        template_id = self._get_context_id("_template_id", template_id)
        if not template_id:
            raise ValueError("Template ID must be provided")

        data = {
            "name": name,
            "return_immediately": return_immediately,
        }

        if options:
            data["options"] = options

        # First, check for folder_id
        folder_id = self._get_context_id("_folder_id", folder_id)
        if folder_id:
            response = await self._request(
                "POST",
                f"folder/{folder_id}/list_template/{template_id}",
                data=data,
            )
            return TaskList.model_validate(response)

        # If no folder_id, try space_id
        space_id = self._get_context_id("_space_id", space_id)
        if space_id:
            response = await self._request(
                "POST",
                f"space/{space_id}/list_template/{template_id}",
                data=data,
            )
            return TaskList.model_validate(response)

        # Neither were provided
        raise ValueError("Either folder_id or space_id must be provided")

    async def get_with_markdown(
        self,
        list_id: Optional[str] = None,
        include_markdown_description: bool = True,
    ) -> TaskList:
        """
        Get details for a specific list with markdown support.

        Args:
            list_id: ID of the list to fetch (uses the one set in the client context if not provided)
            include_markdown_description: Whether to return list descriptions in Markdown format

        Returns:
            TaskList object with markdown content if requested

        Raises:
            ValueError: If list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        list_id = self._get_context_id("_list_id", list_id)
        if not list_id:
            raise ValueError("List ID must be provided")

        params = {
            "include_markdown_description": str(include_markdown_description).lower()
        }
        response = await self._request("GET", f"list/{list_id}", params=params)
        return TaskList.model_validate(response)
