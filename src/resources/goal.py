"""
Goal resources for ClickUp API.

This module contains resource classes for interacting with goal-related endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..exceptions import ClickUpError
from ..models import Goal, KeyResult, KeyResultType
from ..utils import convert_to_timestamp
from .base import BaseResource


class GoalResource(BaseResource):
    """Goal-related API endpoints."""

    async def get_all(
        self,
        workspace_id: Optional[str] = None,
        include_completed: bool = True,
    ) -> List[Goal]:
        """
        Get all goals in a workspace.

        Args:
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            include_completed: Whether to include completed goals

        Returns:
            List of Goal objects

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        params = {"include_completed": "true" if include_completed else "false"}
        response = await self._request(
            "GET", f"team/{workspace_id}/goal", params=params
        )

        # Handle both possible response structures
        goals_data = response.get("goals", [])
        if not goals_data and "goal" in response:
            goals_data = [response["goal"]]

        # Ensure each goal has a color
        for goal in goals_data:
            if "color" not in goal or goal["color"] is None:
                goal["color"] = "#000000"  # Default color

        return [Goal.model_validate(goal) for goal in goals_data]

    async def get(self, goal_id: str) -> Goal:
        """
        Get details of a specific goal.

        Args:
            goal_id: ID of the goal to fetch

        Returns:
            Goal object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the goal doesn't exist
            ClickUpError: For other API errors
        """
        response = await self._request("GET", f"goal/{goal_id}")
        if "goal" not in response:
            raise ClickUpError(
                "Unexpected response format from ClickUp API", response=response
            )
        return Goal.model_validate(response["goal"])

    async def create(
        self,
        name: str,
        due_date: Union[str, int, datetime],
        workspace_id: Optional[str] = None,
        description: str = "",
        multiple_owners: bool = False,
        owners: Optional[List[str]] = None,
        color: Optional[str] = None,
    ) -> Goal:
        """
        Create a new goal in a workspace.

        Args:
            name: Name of the goal
            due_date: Due date for the goal (string, timestamp, or datetime)
            workspace_id: ID of the workspace (uses the one set in the client context if not provided)
            description: Description of the goal
            multiple_owners: Whether the goal can have multiple owners
            owners: List of user IDs who own this goal
            color: Color for the goal (hex code)

        Returns:
            The created Goal object

        Raises:
            ValueError: If workspace_id is not provided and not set in context
            AuthenticationError: If authentication fails
            ResourceNotFound: If the workspace doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        workspace_id = self._get_context_id("_workspace_id", workspace_id)
        if not workspace_id:
            raise ValueError("Workspace ID must be provided")

        # Convert due_date to millisecond timestamp
        due_date_ts = convert_to_timestamp(due_date)

        data = {
            "name": name,
            "due_date": due_date_ts,
            "description": description,
            "multiple_owners": multiple_owners,
            "owners": owners or [],
            "color": color or "#000000",
        }

        response = await self._request("POST", f"team/{workspace_id}/goal", data=data)

        try:
            if "goal" in response:
                goal_data = response["goal"]
                # Add team_id if not present in response
                if "team_id" not in goal_data:
                    goal_data["team_id"] = workspace_id
                return Goal.model_validate(goal_data)
            else:
                raise ClickUpError(f"Unexpected response format: {response}")
        except Exception as e:
            raise ClickUpError(f"Failed to validate goal data: {e}")

    async def update(
        self,
        goal_id: str,
        name: Optional[str] = None,
        due_date: Optional[Union[str, int, datetime]] = None,
        description: Optional[str] = None,
        add_owners: Optional[List[str]] = None,
        rem_owners: Optional[List[str]] = None,
        color: Optional[str] = None,
    ) -> Goal:
        """
        Update an existing goal.

        Args:
            goal_id: ID of the goal to update
            name: New name for the goal
            due_date: New due date for the goal
            description: New description for the goal
            add_owners: List of user IDs to add as owners
            rem_owners: List of user IDs to remove as owners
            color: New color for the goal

        Returns:
            The updated Goal object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the goal doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {}
        if name is not None:
            data["name"] = name
        if due_date is not None:
            data["due_date"] = str(convert_to_timestamp(due_date))
        if description is not None:
            data["description"] = description
        if add_owners is not None:
            data["add_owners"] = add_owners
        if rem_owners is not None:
            data["rem_owners"] = rem_owners
        if color is not None:
            data["color"] = color

        response = await self._request("PUT", f"goal/{goal_id}", data=data)
        if "goal" not in response:
            raise ClickUpError(
                "Unexpected response format from ClickUp API", response=response
            )
        return Goal.model_validate(response["goal"])

    async def delete(self, goal_id: str) -> bool:
        """
        Delete a goal.

        Args:
            goal_id: ID of the goal to delete

        Returns:
            True if successful

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the goal doesn't exist
            ClickUpError: For other API errors
        """
        await self._request("DELETE", f"goal/{goal_id}")
        return True

    async def create_key_result(
        self,
        goal_id: str,
        name: str,
        type: Union[str, KeyResultType],
        steps_start: int = 0,
        steps_end: int = 0,
        unit: str = "points",
        owners: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
        list_ids: Optional[List[str]] = None,
        note: Optional[str] = None,
    ) -> KeyResult:
        """
        Create a new key result for a goal.

        Args:
            goal_id: ID of the goal to add the key result to
            name: Name of the key result
            type: Type of the key result (number, percentage, currency, boolean, automatic)
            steps_start: Starting value for the key result
            steps_end: Target value for the key result
            unit: Unit of measurement (e.g., "points", "%", "USD")
            owners: List of user IDs who own this key result
            task_ids: List of task IDs linked to this key result
            list_ids: List of list IDs linked to this key result
            note: Note about the key result

        Returns:
            The created KeyResult object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the goal doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data = {
            "name": name,
            "type": type.value if isinstance(type, KeyResultType) else type,
            "steps_start": steps_start,
            "steps_end": steps_end,
            "unit": unit,
            "owners": owners or [],
            "task_ids": task_ids or [],
            "list_ids": list_ids or [],
        }
        if note is not None:
            data["note"] = note

        response = await self._request("POST", f"goal/{goal_id}/key_result", data=data)

        if "key_result" not in response:
            raise ClickUpError("Unexpected response format: missing 'key_result' key")

        # Merge the request data with the response data to ensure all required fields are present
        key_result_data = response["key_result"]
        key_result_data.update(
            {
                "name": name,
                "type": type.value if isinstance(type, KeyResultType) else type,
                "steps_start": steps_start,
                "steps_end": steps_end,
                "unit": unit,
                "owners": owners or [],
                "task_ids": task_ids or [],
                "list_ids": list_ids or [],
            }
        )

        return KeyResult.model_validate(key_result_data)

    async def update_key_result(
        self,
        key_result_id: str,
        name: Optional[str] = None,
        type: Optional[Union[str, KeyResultType]] = None,
        steps_start: Optional[int] = None,
        steps_end: Optional[int] = None,
        steps_current: Optional[int] = None,
        unit: Optional[str] = None,
        owners: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
        list_ids: Optional[List[str]] = None,
        note: Optional[str] = None,
    ) -> KeyResult:
        """
        Update an existing key result.

        Args:
            key_result_id: ID of the key result to update
            name: New name for the key result
            type: New type for the key result
            steps_start: New starting value
            steps_end: New target value
            steps_current: Current progress value
            unit: New unit of measurement
            owners: New list of owner user IDs
            task_ids: New list of linked task IDs
            list_ids: New list of linked list IDs
            note: Note about the update

        Returns:
            The updated KeyResult object

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the key result doesn't exist
            ValidationError: If the request data is invalid
            ClickUpError: For other API errors
        """
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if type is not None:
            data["type"] = type.value if isinstance(type, KeyResultType) else type
        if steps_start is not None:
            data["steps_start"] = steps_start
        if steps_end is not None:
            data["steps_end"] = steps_end
        if steps_current is not None:
            data["steps_current"] = steps_current
        if unit is not None:
            data["unit"] = unit
        if owners is not None:
            data["owners"] = owners
        if task_ids is not None:
            data["task_ids"] = task_ids
        if list_ids is not None:
            data["list_ids"] = list_ids
        if note is not None:
            data["note"] = note

        response = await self._request("PUT", f"key_result/{key_result_id}", data=data)

        if "key_result" not in response:
            raise ClickUpError("Unexpected response format: missing 'key_result' key")

        # Merge the request data with the response data to ensure all required fields are present
        key_result_data = response["key_result"]
        for key, value in data.items():
            if key in key_result_data and key_result_data[key] is None:
                key_result_data[key] = value

        return KeyResult.model_validate(key_result_data)

    async def delete_key_result(self, key_result_id: str) -> bool:
        """
        Delete a key result.

        Args:
            key_result_id: ID of the key result to delete

        Returns:
            True if successful

        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFound: If the key result doesn't exist
            ClickUpError: For other API errors
        """
        await self._request("DELETE", f"key_result/{key_result_id}")
        return True
