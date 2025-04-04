"""
Tests for ClickUp task operations.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import cast

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from src import ClickUp, Task
from src.exceptions import ClickUpError, ResourceNotFound
from src.models import PaginatedResponse, Priority, TaskList

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clickup.tests.tasks")

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
WORKSPACE_ID = os.getenv("CLICKUP_WORKSPACE_ID")
SPACE_ID = os.getenv("CLICKUP_SPACE_ID")
LIST_ID = os.getenv("CLICKUP_LIST_ID")

# Skip all tests if required environment variables are not set
pytestmark = pytest.mark.skipif(
    not all([API_TOKEN, WORKSPACE_ID, SPACE_ID, LIST_ID]),
    reason="Required environment variables (API_TOKEN, WORKSPACE_ID, SPACE_ID, LIST_ID) are not set",
)

# At this point, we know these variables are not None
API_TOKEN = cast(str, API_TOKEN)
WORKSPACE_ID = cast(str, WORKSPACE_ID)
SPACE_ID = cast(str, SPACE_ID)
LIST_ID = cast(str, LIST_ID)


@pytest_asyncio.fixture(scope="module")
async def client():
    """Create a ClickUp client instance for testing."""
    # Ensure API_TOKEN is not None before proceeding (for type checker)
    assert API_TOKEN is not None, "API_TOKEN must be set"
    async with ClickUp(API_TOKEN) as client_instance:
        yield client_instance


@pytest_asyncio.fixture(scope="module")
async def test_list(client: ClickUp):
    """Provides a test list, either existing or temporarily created."""
    try:
        # Attempt to get the list specified by LIST_ID
        list_obj = await client.lists.get(LIST_ID)
        logger.info(f"Using existing list: {list_obj.name} (ID: {list_obj.id})")
        yield cast(TaskList, list_obj)
        # No cleanup needed if using existing list
    except ResourceNotFound:
        # If LIST_ID is invalid or not found, create a temporary list
        list_name = f"Test List - Tasks - {uuid.uuid4()}"
        logger.info(f"Creating temporary list: {list_name}")
        list_obj = await client.lists.create(name=list_name, space_id=SPACE_ID)
        yield cast(TaskList, list_obj)
        # Clean up the temporary list
        logger.info(f"Deleting temporary list: {list_name} (ID: {list_obj.id})")
        await client.lists.delete(list_obj.id)
    except Exception as e:
        pytest.fail(f"Failed to set up test list: {e}")


@pytest.mark.asyncio
async def test_task_crud_operations(client: ClickUp, test_list: TaskList):
    """Test basic Create, Read, Update, Delete operations for tasks."""
    task_name = f"Test Task - CRUD - {uuid.uuid4()}"
    task_description = "This is a CRUD test task."
    task_id = None

    try:
        # CREATE
        logger.info(f"Creating task: {task_name} in list {test_list.id}")
        task = await client.tasks.create(
            name=task_name,
            list_id=test_list.id,
            description=task_description,
            priority=Priority.NORMAL,
            due_date=datetime.now() + timedelta(days=1),
        )
        task_id = task.id
        assert isinstance(task, Task)
        assert task.name == task_name
        assert task.description == task_description
        assert task.priority_value == Priority.NORMAL
        assert task.list is not None
        assert task.list.id == test_list.id
        logger.info(f"Task created successfully: {task.id}")

        # Allow some time for propagation if needed (optional)
        await asyncio.sleep(1)

        # READ
        logger.info(f"Reading task: {task_id}")
        retrieved_task = await client.tasks.get(task_id)
        assert isinstance(retrieved_task, Task)
        assert retrieved_task.id == task_id
        assert retrieved_task.name == task_name
        logger.info(f"Task read successfully: {retrieved_task.id}")

        # UPDATE
        updated_name = f"Updated Task - {uuid.uuid4()}"
        updated_description = "Updated description."
        logger.info(f"Updating task: {task_id}")
        updated_task = await client.tasks.update(
            task_id=task_id,
            name=updated_name,
            description=updated_description,
            priority=Priority.HIGH,
        )
        assert isinstance(updated_task, Task)
        assert updated_task.id == task_id
        assert updated_task.name == updated_name
        assert updated_task.description == updated_description
        assert updated_task.priority_value == Priority.HIGH
        logger.info(f"Task updated successfully: {updated_task.id}")

        # Allow some time for propagation if needed (optional)
        await asyncio.sleep(1)

        # Verify update by reading again
        verified_task = await client.tasks.get(task_id)
        assert verified_task.name == updated_name
        assert verified_task.priority_value == Priority.HIGH

    finally:
        # DELETE / CLEANUP
        if task_id:
            logger.info(f"Deleting task: {task_id}")
            try:
                delete_result = await client.tasks.delete(task_id)
                # Successful delete should return True
                assert delete_result is True
                logger.info(f"Task deleted successfully: {task_id}")

                # Verify deletion
                with pytest.raises(ResourceNotFound):
                    await client.tasks.get(task_id)
                logger.info(f"Verified task deletion: {task_id}")

            except ResourceNotFound:
                logger.warning(
                    f"Task {task_id} already deleted or not found for cleanup."
                )
            except Exception as e:
                logger.error(f"Error deleting task {task_id}: {e}")
                pytest.fail(f"Failed to clean up task {task_id}")


@pytest.mark.asyncio
async def test_get_all_tasks_in_list(client: ClickUp, test_list: TaskList):
    """Test retrieving all tasks within a specific list."""
    task_ids = set()
    try:
        # Create a few tasks
        for i in range(3):
            task = await client.tasks.create(
                name=f"Task for Get All {i} - {uuid.uuid4()}", list_id=test_list.id
            )
            task_ids.add(task.id)
            await asyncio.sleep(0.5)  # Small delay between creations

        # Retrieve all tasks (response acts like a sequence)
        tasks_response: PaginatedResponse[Task] = await client.tasks.get_all(
            list_id=test_list.id
        )

        # Get retrieved IDs by iterating over the response
        retrieved_ids = {t.id for t in tasks_response}

        # Check if all created task IDs are in the retrieved IDs
        assert task_ids.issubset(retrieved_ids)  # Ensure our created tasks are present

        # Log the number of retrieved tasks using len()
        logger.info(f"Retrieved {len(tasks_response)} tasks from list {test_list.id}")

    finally:
        # Clean up created tasks
        for task_id in task_ids:
            try:
                await client.tasks.delete(task_id)
            except ResourceNotFound:
                pass  # Ignore if already deleted
            except Exception as e:
                logger.error(f"Error cleaning up task {task_id} in get_all test: {e}")
