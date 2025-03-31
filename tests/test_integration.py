"""
Integration tests for the ClickUp client.

These tests verify that the client works correctly with the real ClickUp API.
To run these tests, you need to set up the following environment variables:
- CLICKUP_API_TOKEN: Your ClickUp API token
- CLICKUP_WORKSPACE_ID: ID of a workspace to test with
- CLICKUP_SPACE_ID: ID of a space to test with
- CLICKUP_LIST_ID: ID of a list to test with
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import cast

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from src import ClickUp
from src.models import Priority

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("clickup")

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
    reason="Required environment variables are not set",
)

# At this point, we know these variables are not None
API_TOKEN = cast(str, API_TOKEN)
WORKSPACE_ID = cast(str, WORKSPACE_ID)
SPACE_ID = cast(str, SPACE_ID)
LIST_ID = cast(str, LIST_ID)


@pytest_asyncio.fixture
async def client():
    """Create a ClickUp client instance for testing."""
    if not API_TOKEN:
        pytest.skip("API token not set")
    client = ClickUp(API_TOKEN)  # type: ignore
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_workspace_operations(client):
    """Test workspace-related operations."""
    # Get workspace details
    workspace = await client.get_workspace(WORKSPACE_ID)
    assert workspace is not None
    assert workspace.id == WORKSPACE_ID
    assert workspace.name is not None

    # Get all workspaces
    workspaces = await client.get_workspaces()
    assert len(workspaces) > 0
    assert any(w.id == WORKSPACE_ID for w in workspaces)


@pytest.mark.asyncio
async def test_space_operations(client):
    """Test space-related operations."""
    # Get space details
    space = await client.get_space(SPACE_ID)
    assert space is not None
    assert space.id == SPACE_ID
    assert space.name is not None

    # Get all spaces in workspace
    spaces = await client.get_spaces(WORKSPACE_ID)
    assert len(spaces) > 0
    assert any(s.id == SPACE_ID for s in spaces)


@pytest.mark.asyncio
async def test_list_operations(client):
    """Test list-related operations."""
    # Get list details
    task_list = await client.get_list(LIST_ID)
    assert task_list is not None
    assert task_list.id == LIST_ID
    assert task_list.name is not None

    # Get all lists in space
    lists = await client.get_lists(space_id=SPACE_ID)
    assert len(lists) > 0
    assert any(l.id == LIST_ID for l in lists)


@pytest.mark.asyncio
async def test_task_operations(client):
    """Test task-related operations."""
    # Create a test task
    task_name = f"Integration Test Task {datetime.now().isoformat()}"
    task = await client.create_task(
        name=task_name,
        list_id=LIST_ID,
        description="This is a test task created by integration tests",
        priority=Priority.NORMAL,
        due_date=datetime.now() + timedelta(days=1),
    )
    assert task is not None
    assert task.name == task_name
    assert task.description == "This is a test task created by integration tests"
    assert task.priority_value == Priority.NORMAL

    # Get task details
    task_details = await client.get_task(task.id)
    assert task_details is not None
    assert task_details.id == task.id
    assert task_details.name == task_name

    # Update task
    updated_name = f"Updated Integration Test Task {datetime.now().isoformat()}"
    updated_task = await client.update_task(
        task_id=task.id,
        name=updated_name,
        description="Updated test task description",
        priority=Priority.HIGH,
    )
    assert updated_task is not None
    assert updated_task.id == task.id
    assert updated_task.name == updated_name
    assert updated_task.description == "Updated test task description"
    assert updated_task.priority_value == Priority.HIGH

    # Get tasks from list
    tasks = await client.get_tasks(list_id=LIST_ID)
    assert len(tasks) > 0
    assert any(t.id == task.id for t in tasks)

    # Delete task
    result = await client.delete_task(task.id)
    assert result is True


@pytest.mark.asyncio
async def test_task_pagination(client):
    """Test task pagination functionality."""
    # Create multiple test tasks
    task_ids = []
    for i in range(5):
        task = await client.create_task(
            name=f"Pagination Test Task {i} {datetime.now().isoformat()}",
            list_id=LIST_ID,
            description=f"Test task {i} for pagination testing",
        )
        task_ids.append(task.id)

    # Get first page of tasks
    tasks = await client.get_tasks(
        list_id=LIST_ID,
        page=0,
        order_by="created",
        reverse=True,
    )
    assert len(tasks) > 0

    # Clean up test tasks
    for task_id in task_ids:
        await client.delete_task(task_id)


@pytest.mark.asyncio
async def test_task_filtering(client):
    """Test task filtering functionality."""
    # Create a test task with specific properties
    task = await client.create_task(
        name=f"Filter Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for filtering",
        priority=Priority.HIGH,
        due_date=datetime.now() + timedelta(days=1),
    )

    # Test various filters
    high_priority_tasks = await client.get_tasks(
        list_id=LIST_ID,
        priority=Priority.HIGH,
    )
    assert any(t.id == task.id for t in high_priority_tasks)

    # Clean up
    await client.delete_task(task.id)


@pytest.mark.asyncio
async def test_task_comments(client):
    """Test task comment operations."""
    # Create a test task
    task = await client.create_task(
        name=f"Comment Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for comments",
    )

    # Add a comment
    comment = await client.create_task_comment(
        task_id=task.id,
        comment_text="This is a test comment",
        notify_all=False,
    )
    assert comment is not None
    assert comment.text == "This is a test comment"

    # Get comments
    comments = await client.get_task_comments(task.id)
    assert len(comments) > 0
    assert any(c.id == comment.id for c in comments)

    # Clean up
    await client.delete_task(task.id)


@pytest.mark.asyncio
async def test_task_time_tracking(client):
    """Test time tracking operations."""
    # Create a test task
    task = await client.create_task(
        name=f"Time Tracking Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for time tracking",
    )

    # Start timer with a 1-hour duration
    time_entry = await client.start_timer(
        task_id=task.id,
        workspace_id=WORKSPACE_ID,
        duration=3600000,  # 1 hour in milliseconds
    )
    assert time_entry is not None
    assert time_entry.task_id == task.id

    # Clean up
    await client.delete_task(task.id)
