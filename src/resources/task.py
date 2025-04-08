"""
Task resources for ClickUp API.

This module contains resource classes for interacting with task-related endpoints.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx

from ..exceptions import ClickUpError, ResourceNotFound, ValidationError
from ..models import PaginatedResponse, Priority, Task, TaskTimeInStatus
from ..utils import convert_to_timestamp
from .base import BaseResource


class TaskResource(BaseResource):
    """Task-related API endpoints."""

    async def get_all(
        self,
        list_id: Optional[str] = None,
        archived: bool = False,
        page: int = 0,
        order_by: str = "created",
        reverse: bool = False,
        subtasks: bool = False,
        statuses: Optional[List[str]] = None,
        include_closed: bool = False,
        assignees: Optional[List[str]] = None,
        watchers: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        due_date_gt: Optional[Union[str, int, datetime]] = None,
        due_date_lt: Optional[Union[str, int, datetime]] = None,
        date_created_gt: Optional[Union[str, int, datetime]] = None,
        date_created_lt: Optional[Union[str, int, datetime]] = None,
        date_updated_gt: Optional[Union[str, int, datetime]] = None,
        date_updated_lt: Optional[Union[str, int, datetime]] = None,
        date_done_gt: Optional[Union[str, int, datetime]] = None,
        date_done_lt: Optional[Union[str, int, datetime]] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        custom_field: Optional[List[Dict[str, Any]]] = None,
        custom_items: Optional[List[int]] = None,
        include_markdown_description: bool = False,
        priority: Optional[Union[int, Priority]] = None,
    ) -> PaginatedResponse[Task]:
        """
        Get tasks from a list with pagination.

        Args:
            list_id: ID of the list (uses the one set in the client context if not provided)
            archived: Include archived tasks
            page: Page number (starting from 0)
            order_by: Field to order by (id, created, updated, due_date)
            reverse: Reverse the order
            subtasks: Include subtasks
            statuses: Filter by status names
            include_closed: Include closed tasks
            assignees: Filter by assignee IDs
            watchers: Filter by watcher IDs
            tags: Filter by tags
            due_date_gt: Tasks due after this date
            due_date_lt: Tasks due before this date
            date_created_gt: Tasks created after this date
            date_created_lt: Tasks created before this date
            date_updated_gt: Tasks updated after this date
            date_updated_lt: Tasks updated before this date
            date_done_gt: Tasks completed after this date
            date_done_lt: Tasks completed before this date
            custom_fields: Filter by custom field values
            custom_field: Filter by a single custom field value
            custom_items: Filter by custom task types (0=Task, 1=Milestone)
            include_markdown_description: Return task descriptions in Markdown format
            priority: Filter by priority level (1=Urgent, 2=High, 3=Normal, 4=Low)

        Returns:
            PaginatedResponse containing Task objects

        Raises:
            ValueError: If list_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list doesn't exist
            ClickUpError: For other API errors
        """
        # Set the current method for pagination
        self.client._current_method = "tasks.get_all"

        try:
            list_id = self._get_context_id("_list_id", list_id)
            if not list_id:
                raise ValueError("List ID must be provided")

            params = {
                "archived": str(archived).lower(),
                "page": page,
                "order_by": order_by,
                "reverse": str(reverse).lower(),
                "subtasks": str(subtasks).lower(),
                "include_closed": str(include_closed).lower(),
                "include_markdown_description": str(
                    include_markdown_description
                ).lower(),
            }

            if statuses:
                params["statuses[]"] = statuses
            if assignees:
                params["assignees[]"] = assignees
            if watchers:
                params["watchers[]"] = watchers
            if tags:
                params["tags[]"] = tags
            if custom_fields:
                params["custom_fields"] = json.dumps(custom_fields)
            if custom_field:
                params["custom_field"] = json.dumps(custom_field)
            if custom_items:
                params["custom_items[]"] = custom_items
            if priority is not None:
                if isinstance(priority, Priority):
                    params["priority"] = str(priority.value)
                else:
                    params["priority"] = str(priority)

            # Handle date filters
            date_filters = {
                "due_date": (due_date_gt, due_date_lt),
                "date_created": (date_created_gt, date_created_lt),
                "date_updated": (date_updated_gt, date_updated_lt),
                "date_done": (date_done_gt, date_done_lt),
            }

            for prefix, (gt, lt) in date_filters.items():
                if gt:
                    params[f"{prefix}_gt"] = str(convert_to_timestamp(gt))
                if lt:
                    params[f"{prefix}_lt"] = str(convert_to_timestamp(lt))

            response = await self._request("GET", f"list/{list_id}/task", params=params)
            tasks = [Task.model_validate(task) for task in response.get("tasks", [])]

            # Determine if there are more pages and prepare next page params
            next_page_params = None
            if response.get("has_more"):
                next_page_params = dict(params)
                next_page_params["page"] = page + 1
                next_page_params["list_id"] = list_id

            return PaginatedResponse(tasks, self.client, next_page_params)
        finally:
            self.client._current_method = None

    async def get(self, task_id: Optional[str] = None) -> Task:
        """
        Get a task by ID.

        Args:
            task_id: ID of the task (uses the one set in the client context if not provided)

        Returns:
            Task object

        Raises:
            ValueError: If task_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task doesn't exist
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        response = await self._request("GET", f"task/{task_id}")
        return Task.model_validate(response)

    async def create(
        self,
        name: str,
        list_id: Optional[str] = None,
        description: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        priority: Optional[Union[int, Priority]] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        due_date_time: Optional[bool] = None,
        time_estimate: Optional[int] = None,
        start_date: Optional[Union[str, int, datetime]] = None,
        start_date_time: Optional[bool] = None,
        notify_all: bool = True,
        parent: Optional[str] = None,
        links_to: Optional[str] = None,
        check_required_custom_fields: bool = True,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
        points: Optional[float] = None,
        group_assignees: Optional[List[str]] = None,
        markdown_content: Optional[str] = None,
        custom_item_id: Optional[int] = None,
    ) -> Task:
        """
        Create a new task.

        Args:
            name: Task name
            list_id: ID of the list (uses the one set in the client context if not provided)
            description: Task description
            assignees: List of assignee IDs
            tags: List of tags
            status: Task status
            priority: Priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            due_date: Due date (string, timestamp, or datetime)
            due_date_time: Whether the due date includes time
            time_estimate: Time estimate in milliseconds
            start_date: Start date (string, timestamp, or datetime)
            start_date_time: Whether the start date includes time
            notify_all: Notify all assignees
            parent: Parent task ID for subtasks
            links_to: Task ID to link this task to
            check_required_custom_fields: Check if required custom fields are filled
            custom_fields: List of custom field values
            custom_task_ids: Use custom task IDs
            team_id: Team ID when using custom task IDs
            points: Sprint points for the task
            group_assignees: List of group assignee IDs
            markdown_content: Markdown formatted description
            custom_item_id: Custom task type ID

        Returns:
            The created Task object

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

        data: Dict[str, Any] = {"name": name}

        if description is not None:
            data["description"] = description
        if assignees is not None:
            data["assignees"] = [str(a) for a in assignees]
        if tags is not None:
            data["tags"] = [str(t) for t in tags]
        if status is not None:
            data["status"] = status
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = str(priority.value)
            else:
                data["priority"] = str(priority)
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if due_date_time is not None:
            data["due_date_time"] = str(due_date_time).lower()
        if time_estimate is not None:
            data["time_estimate"] = str(time_estimate)
        if start_date is not None:
            data["start_date"] = str(convert_to_timestamp(start_date))
        if start_date_time is not None:
            data["start_date_time"] = str(start_date_time).lower()
        if notify_all is not None:
            data["notify_all"] = str(notify_all).lower()
        if parent is not None:
            data["parent"] = parent
        if links_to is not None:
            data["links_to"] = links_to
        if check_required_custom_fields is not None:
            data["check_required_custom_fields"] = str(
                check_required_custom_fields
            ).lower()
        if custom_fields is not None:
            data["custom_fields"] = custom_fields
        if custom_task_ids is not None:
            data["custom_task_ids"] = str(custom_task_ids).lower()
        if team_id is not None:
            data["team_id"] = team_id
        if points is not None:
            data["points"] = str(points)
        if group_assignees is not None:
            data["group_assignees"] = group_assignees
        if markdown_content is not None:
            data["markdown_content"] = markdown_content
        if custom_item_id is not None:
            data["custom_item_id"] = custom_item_id

        response = await self._request("POST", f"list/{list_id}/task", data=data)
        return Task.model_validate(response)

    async def update(
        self,
        task_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[Union[int, Priority]] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        due_date_time: Optional[bool] = None,
        time_estimate: Optional[int] = None,
        start_date: Optional[Union[str, int, datetime]] = None,
        start_date_time: Optional[bool] = None,
        assignees: Optional[List[str]] = None,
        add_assignees: Optional[List[str]] = None,
        remove_assignees: Optional[List[str]] = None,
        group_assignees: Optional[Dict[str, List[str]]] = None,
        watchers: Optional[Dict[str, List[str]]] = None,
        archived: Optional[bool] = None,
        points: Optional[float] = None,
        markdown_content: Optional[str] = None,
        custom_item_id: Optional[int] = None,
    ) -> Task:
        """
        Update an existing task.

        Args:
            task_id: ID of the task to update (uses the one set in the client context if not provided)
            name: New task name
            description: New task description
            status: New task status
            priority: New priority level (1=Urgent, 2=High, 3=Normal, 4=Low)
            due_date: New due date (string, timestamp, or datetime)
            due_date_time: Whether the due date includes time
            time_estimate: New time estimate in milliseconds
            start_date: New start date (string, timestamp, or datetime)
            start_date_time: Whether the start date includes time
            assignees: Complete list of assignee IDs (replaces existing)
            add_assignees: List of assignee IDs to add
            remove_assignees: List of assignee IDs to remove
            group_assignees: Dict with 'add' and 'rem' lists for group assignees
            watchers: Dict with 'add' and 'rem' lists for watchers
            archived: Whether to archive the task
            points: New sprint points
            markdown_content: New markdown formatted description
            custom_item_id: New custom task type ID

        Returns:
            The updated Task object

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

        data = {}

        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status
        if priority is not None:
            if isinstance(priority, Priority):
                data["priority"] = priority.value
            else:
                data["priority"] = priority
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if due_date_time is not None:
            data["due_date_time"] = str(due_date_time).lower()
        if time_estimate is not None:
            data["time_estimate"] = str(time_estimate)
        if start_date is not None:
            data["start_date"] = str(convert_to_timestamp(start_date))
        if start_date_time is not None:
            data["start_date_time"] = str(start_date_time).lower()
        if archived is not None:
            data["archived"] = str(archived).lower()
        if points is not None:
            data["points"] = str(points)
        if markdown_content is not None:
            data["markdown_content"] = markdown_content
        if custom_item_id is not None:
            data["custom_item_id"] = custom_item_id

        # Handle assignees
        if assignees is not None:
            data["assignees"] = assignees
        elif add_assignees or remove_assignees:
            data["assignees"] = {}
            if add_assignees:
                data["assignees"]["add"] = add_assignees
            if remove_assignees:
                data["assignees"]["rem"] = remove_assignees

        # Handle group assignees
        if group_assignees is not None:
            data["group_assignees"] = group_assignees

        # Handle watchers
        if watchers is not None:
            data["watchers"] = watchers

        response = await self._request("PUT", f"task/{task_id}", data=data)
        return Task.model_validate(response)

    async def delete(self, task_id: Optional[str] = None) -> bool:
        """
        Delete a task.

        Args:
            task_id: ID of the task to delete (uses the one set in the client context if not provided)

        Returns:
            True if successful

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

        await self._request("DELETE", f"task/{task_id}")
        return True

    async def create_from_template(
        self,
        name: str,
        list_id: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> Task:
        """
        Create a new task using a task template.

        Args:
            name: Name for the new task
            list_id: ID of the list (uses the one set in the client context if not provided)
            template_id: ID of the template (uses the one set in the client context if not provided)

        Returns:
            The created Task object

        Raises:
            ValueError: If list_id or template_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the list or template doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        list_id = self._get_context_id("_list_id", list_id)
        if not list_id:
            raise ValueError("List ID must be provided")

        template_id = self._get_context_id("_template_id", template_id)
        if not template_id:
            raise ValueError("Template ID must be provided")

        data = {"name": name}
        response = await self._request(
            "POST", f"list/{list_id}/taskTemplate/{template_id}", data=data
        )
        return Task.model_validate(response)

    async def get_time_in_status(
        self,
        task_id: str,
        status: str,
        start_date: Optional[Union[str, int, datetime]] = None,
        end_date: Optional[Union[str, int, datetime]] = None,
    ) -> TaskTimeInStatus:
        """
        Get time spent in a specific status for a task.

        Args:
            task_id: ID of the task
            status: Status to get time for
            start_date: Start date filter (string, timestamp, or datetime)
            end_date: End date filter (string, timestamp, or datetime)

        Returns:
            TaskTimeInStatus object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        params = {"status": status}

        if start_date:
            params["start_date"] = str(convert_to_timestamp(start_date))

        if end_date:
            params["end_date"] = str(convert_to_timestamp(end_date))

        response = await self._request(
            "GET", f"task/{task_id}/time_in_status", params=params
        )
        return TaskTimeInStatus.model_validate(response.get("data", {}))

    async def create_attachment(
        self,
        task_id: Optional[str] = None,
        file_path: Optional[Union[str, Path]] = None,
        file_data: Optional[bytes] = None,
        file_name: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file as an attachment to a task.

        Args:
            task_id: ID of the task to attach the file to (uses the one set in the client context if not provided)
            file_path: Path to the file to upload (mutually exclusive with file_data)
            file_data: Raw file data to upload (mutually exclusive with file_path)
            file_name: Name to give the file in ClickUp (required if using file_data)
            custom_task_ids: Whether to use custom task IDs
            team_id: Team ID when using custom task IDs

        Returns:
            Dict containing the attachment details

        Raises:
            ValueError: If task_id is not provided and not set in context
                      If neither file_path nor file_data is provided
                      If file_name is missing when using file_data
            AuthenticationError: If authentication fails
            ResourceNotFound: If the task doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        task_id = self._get_context_id("_task_id", task_id)
        if not task_id:
            raise ValueError("Task ID must be provided")

        if file_path is None and file_data is None:
            raise ValueError("Either file_path or file_data must be provided")
        if file_path is not None and file_data is not None:
            raise ValueError("Cannot provide both file_path and file_data")
        if file_data is not None and not file_name:
            raise ValueError("file_name is required when using file_data")

        # Prepare the file data
        if file_path is not None:
            file_path = Path(file_path)
            if not file_path.exists():
                raise ValueError(f"File not found: {file_path}")
            file_name = file_path.name
            with open(file_path, "rb") as f:
                file_data = f.read()

        if not file_name:
            raise ValueError("file_name must be provided")

        # Prepare the request URL
        url = f"{self.client.base_url.rstrip('/')}/task/{task_id}/attachment"

        # Set up query parameters
        params = {}
        if custom_task_ids:
            params["custom_task_ids"] = str(custom_task_ids).lower()
            if team_id:
                params["team_id"] = team_id

        # Prepare the multipart form data
        files = {"attachment": (file_name, file_data or b"")}

        try:
            response = await self.client._client.post(
                url,
                params=params,
                files=files,
                headers=self.client._get_upload_headers(),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ResourceNotFound(f"Task {task_id} not found")
            elif e.response.status_code == 400:
                raise ValidationError(str(e), 400, {})
            else:
                raise ClickUpError(str(e), e.response.status_code, {})

    # --- Task Relationships --- #

    async def add_dependency(
        self,
        task_id: str,
        depends_on: Optional[str] = None,
        dependency_of: Optional[str] = None,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> bool:
        """
        Set a task as waiting on or blocking another task.

        Args:
            task_id: ID of the task which is waiting on or blocking another.
            depends_on: ID of the task that must be completed first.
            dependency_of: ID of the task that is waiting for the task_id task.
            custom_task_ids: Set to True to use custom task IDs.
            team_id: Required workspace ID if custom_task_ids is True.

        Returns:
            True if successful.

        Raises:
            ValueError: If neither or both depends_on and dependency_of are provided.
            ValueError: If custom_task_ids is True but team_id is not provided.
            AuthenticationError: If authentication fails.
            ResourceNotFound: If a task doesn't exist.
            ClickUpError: For other API errors.
        """
        if not (depends_on is None) ^ (dependency_of is None):
            raise ValueError(
                "Exactly one of 'depends_on' or 'dependency_of' must be provided."
            )

        params = {}
        if custom_task_ids:
            if not team_id:
                raise ValueError("team_id is required when custom_task_ids is True.")
            params["custom_task_ids"] = "true"
            params["team_id"] = team_id

        data = {}
        if depends_on:
            data["depends_on"] = depends_on
        if dependency_of:
            data["dependency_of"] = dependency_of

        await self._request(
            "POST", f"task/{task_id}/dependency", params=params, data=data
        )
        return True

    async def delete_dependency(
        self,
        task_id: str,
        depends_on: str,
        dependency_of: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> bool:
        """
        Remove the dependency relationship between two tasks.

        Args:
            task_id: ID of the task in the relationship.
            depends_on: ID of the task that must be completed first.
            dependency_of: ID of the task that is waiting.
            custom_task_ids: Set to True to use custom task IDs.
            team_id: Required workspace ID if custom_task_ids is True.

        Returns:
            True if successful.

        Raises:
            ValueError: If custom_task_ids is True but team_id is not provided.
            AuthenticationError: If authentication fails.
            ResourceNotFound: If a task doesn't exist.
            ClickUpError: For other API errors.
        """
        params = {
            "depends_on": depends_on,
            "dependency_of": dependency_of,
        }
        if custom_task_ids:
            if not team_id:
                raise ValueError("team_id is required when custom_task_ids is True.")
            params["custom_task_ids"] = "true"
            params["team_id"] = team_id

        await self._request("DELETE", f"task/{task_id}/dependency", params=params)
        return True

    async def add_task_link(
        self,
        task_id: str,
        links_to: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> bool:
        """
        Link two tasks together.

        Args:
            task_id: ID of the task to link from.
            links_to: ID of the task to link to.
            custom_task_ids: Set to True to use custom task IDs for both tasks.
            team_id: Required workspace ID if custom_task_ids is True.

        Returns:
            True if successful.

        Raises:
            ValueError: If custom_task_ids is True but team_id is not provided.
            AuthenticationError: If authentication fails.
            ResourceNotFound: If a task doesn't exist.
            ClickUpError: For other API errors.
        """
        params = {}
        if custom_task_ids:
            if not team_id:
                raise ValueError("team_id is required when custom_task_ids is True.")
            params["custom_task_ids"] = "true"
            params["team_id"] = team_id

        await self._request("POST", f"task/{task_id}/link/{links_to}", params=params)
        return True

    async def delete_task_link(
        self,
        task_id: str,
        links_to: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> bool:
        """
        Remove the link between two tasks.

        Args:
            task_id: ID of the task linked from.
            links_to: ID of the task linked to.
            custom_task_ids: Set to True to use custom task IDs for both tasks.
            team_id: Required workspace ID if custom_task_ids is True.

        Returns:
            True if successful.

        Raises:
            ValueError: If custom_task_ids is True but team_id is not provided.
            AuthenticationError: If authentication fails.
            ResourceNotFound: If a task doesn't exist.
            ClickUpError: For other API errors.
        """
        params = {}
        if custom_task_ids:
            if not team_id:
                raise ValueError("team_id is required when custom_task_ids is True.")
            params["custom_task_ids"] = "true"
            params["team_id"] = team_id

        await self._request("DELETE", f"task/{task_id}/link/{links_to}", params=params)
        return True

    # --- Task Tags --- #

    async def add_tag_to_task(
        self,
        task_id: str,
        tag_name: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> None:
        """
        Add a tag to a task.

        Note: The API returns a 200 OK with an empty body on success.

        Args:
            task_id: ID of the task.
            tag_name: Name of the tag to add.
            custom_task_ids: Set to True to use custom task IDs.
            team_id: Required workspace ID if custom_task_ids is True.

        Raises:
            ValueError: If custom_task_ids is True but team_id is not provided.
            AuthenticationError: If authentication fails.
            ResourceNotFound: If the task or tag doesn't exist.
            ClickUpError: For other API errors.
        """
        params = {}
        if custom_task_ids:
            if not team_id:
                raise ValueError("team_id is required when custom_task_ids is True.")
            params["custom_task_ids"] = "true"
            params["team_id"] = team_id

        await self._request("POST", f"task/{task_id}/tag/{tag_name}", params=params)
        # No return value

    async def remove_tag_from_task(
        self,
        task_id: str,
        tag_name: str,
        custom_task_ids: bool = False,
        team_id: Optional[str] = None,
    ) -> None:
        """
        Remove a tag from a task.

        Note: The API returns a 200 OK with an empty body on success.

        Args:
            task_id: ID of the task.
            tag_name: Name of the tag to remove.
            custom_task_ids: Set to True to use custom task IDs.
            team_id: Required workspace ID if custom_task_ids is True.

        Raises:
            ValueError: If custom_task_ids is True but team_id is not provided.
            AuthenticationError: If authentication fails.
            ResourceNotFound: If the task or tag doesn't exist.
            ClickUpError: For other API errors.
        """
        params = {}
        if custom_task_ids:
            if not team_id:
                raise ValueError("team_id is required when custom_task_ids is True.")
            params["custom_task_ids"] = "true"
            params["team_id"] = team_id

        await self._request("DELETE", f"task/{task_id}/tag/{tag_name}", params=params)
        # No return value
