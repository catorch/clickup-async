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
from src.exceptions import ValidationError
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

# Debug log the environment variables
logger.debug("Environment variables loaded:")
logger.debug(f"WORKSPACE_ID: {WORKSPACE_ID}")
logger.debug(f"SPACE_ID: {SPACE_ID}")
logger.debug(f"LIST_ID: {LIST_ID}")

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
    # Print environment variables
    print("\nEnvironment variables:")
    print(f"WORKSPACE_ID: {WORKSPACE_ID}")
    print(f"SPACE_ID: {SPACE_ID}")
    print(f"LIST_ID: {LIST_ID}")

    # Get workspace details
    workspace = await client.workspaces.get_workspace(WORKSPACE_ID)
    assert workspace is not None
    assert workspace.id == WORKSPACE_ID
    assert workspace.name is not None

    # Get all workspaces
    workspaces = await client.workspaces.get_workspaces()
    assert len(workspaces) > 0
    assert any(w.id == WORKSPACE_ID for w in workspaces)


@pytest.mark.asyncio
async def test_space_operations(client):
    """Test space-related operations."""
    # Get space details
    space = await client.spaces.get_space(SPACE_ID)
    assert space is not None
    assert space.id == SPACE_ID
    assert space.name is not None

    # Get all spaces in workspace
    spaces = await client.spaces.get_spaces(WORKSPACE_ID)
    assert len(spaces) > 0
    assert any(s.id == SPACE_ID for s in spaces)


@pytest.mark.asyncio
async def test_list_operations(client):
    """Test list-related operations."""
    # Get list details
    task_list = await client.lists.get(LIST_ID)
    assert task_list is not None
    assert task_list.id == LIST_ID
    assert task_list.name is not None

    # Get all lists in space
    lists = await client.lists.get_all(space_id=SPACE_ID)
    assert len(lists) > 0
    assert any(l.id == LIST_ID for l in lists)

    # Test markdown support
    list_with_markdown = await client.lists.get_with_markdown(LIST_ID)
    assert list_with_markdown is not None
    assert list_with_markdown.id == LIST_ID
    assert hasattr(list_with_markdown, "content")

    # Create a test task for multiple list operations
    task = await client.tasks.create(
        name=f"Multiple List Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for multiple list operations",
    )

    # Create another list to test multiple list operations
    another_list = await client.lists.create(
        name=f"Another Test List {datetime.now().isoformat()}",
        space_id=SPACE_ID,
    )

    try:
        # Test adding task to another list
        try:
            result = await client.lists.add_task(
                task_id=task.id, list_id=another_list.id
            )
            assert result is True

            # Test removing task from the additional list
            result = await client.lists.remove_task(
                task_id=task.id, list_id=another_list.id
            )
            assert result is True
        except ValidationError as e:
            if "Tasks in multiple lists limit exceeded" in str(e):
                pytest.skip("Tasks in Multiple Lists feature is not enabled")
            raise
    finally:
        # Clean up
        await client.tasks.delete(task.id)
        await client.lists.delete(another_list.id)


@pytest.mark.skip(reason="Requires a valid template ID to run")
@pytest.mark.asyncio
async def test_list_template_operations(client):
    """Test creating lists from templates.

    This test requires a valid template ID to run. To run this test:
    1. Create a list template in your ClickUp workspace
    2. Get the template ID
    3. Replace the template_id value with your actual template ID
    4. Remove the @pytest.mark.skip decorator
    """
    template_id = "your_template_id"  # Replace with actual template ID
    list_name = f"Template List {datetime.now().isoformat()}"

    # Create list from template in space
    list_from_template = await client.lists.create_from_template(
        name=list_name,
        space_id=SPACE_ID,
        template_id=template_id,
        return_immediately=True,
        options={
            "content": "Template list description",
            "time_estimate": True,
            "automation": True,
            "include_views": True,
        },
    )
    assert list_from_template is not None
    assert list_from_template.name == list_name
    assert (
        list_from_template.space is not None and list_from_template.space.id == SPACE_ID
    )

    # Clean up
    await client.lists.delete(list_from_template.id)


@pytest.mark.asyncio
async def test_task_operations(client):
    """Test task-related operations."""
    # Create a test task
    task_name = f"Integration Test Task {datetime.now().isoformat()}"
    task = await client.tasks.create(
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
    task_details = await client.tasks.get(task.id)
    assert task_details is not None
    assert task_details.id == task.id
    assert task_details.name == task_name

    # Update task
    updated_name = f"Updated Integration Test Task {datetime.now().isoformat()}"
    updated_task = await client.tasks.update(
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

    # Get tasks from list (PaginatedResponse acts as sequence)
    tasks_response = await client.tasks.get_all(list_id=LIST_ID)
    assert len(tasks_response) > 0
    assert any(t.id == task.id for t in tasks_response)

    # Delete task
    # Successful delete should return True
    delete_result = await client.tasks.delete(task.id)
    assert delete_result is True


@pytest.mark.asyncio
async def test_task_pagination(client):
    """Test task pagination functionality."""
    # Create multiple test tasks
    task_ids = []
    for i in range(5):
        task = await client.tasks.create(
            name=f"Pagination Test Task {i} {datetime.now().isoformat()}",
            list_id=LIST_ID,
            description=f"Test task {i} for pagination testing",
        )
        task_ids.append(task.id)
        await asyncio.sleep(0.5)  # Small delay

    # Get first page of tasks (PaginatedResponse acts as sequence)
    tasks_response = await client.tasks.get_all(
        list_id=LIST_ID,
        page=0,
        order_by="created",
        reverse=True,
    )
    assert len(tasks_response) > 0

    # Clean up test tasks
    for task_id in task_ids:
        await client.tasks.delete(task_id)


@pytest.mark.asyncio
async def test_task_filtering(client):
    """Test task filtering functionality."""
    # Create a test task with specific properties
    task = await client.tasks.create(
        name=f"Filter Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for filtering",
        priority=Priority.HIGH,
        due_date=datetime.now() + timedelta(days=1),
    )

    # Test various filters (PaginatedResponse acts as sequence)
    high_priority_tasks_response = await client.tasks.get_all(
        list_id=LIST_ID,
        priority=Priority.HIGH,
    )
    assert any(t.id == task.id for t in high_priority_tasks_response)

    # Clean up
    await client.tasks.delete(task.id)


@pytest.mark.asyncio
async def test_task_comments(client):
    """Test task comment operations."""
    # Create a test task
    task = await client.tasks.create(
        name=f"Comment Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for comments",
    )

    # Add a comment
    comment = await client.comments.create_task_comment(
        task_id=task.id,
        comment_text="This is a test comment",
        notify_all=False,
    )
    assert comment is not None
    assert comment.content == "This is a test comment"  # Check content attribute

    # Get comments
    comments = await client.comments.get_task_comments(task.id)
    assert len(comments) > 0
    assert any(c.id == comment.id for c in comments)

    # Clean up
    await client.tasks.delete(task.id)


@pytest.mark.asyncio
async def test_task_time_tracking(client):
    """Test time tracking operations."""
    # Create a test task
    task = await client.tasks.create(
        name=f"Time Tracking Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for time tracking",
    )

    # Start timer with a 1-hour duration
    time_entry = await client.time.start_timer(
        task_id=task.id,
        workspace_id=WORKSPACE_ID,
        duration=3600000,  # 1 hour in milliseconds
    )
    assert time_entry is not None
    assert time_entry.task_id == task.id

    # Clean up
    await client.tasks.delete(task.id)


@pytest.mark.asyncio
async def test_task_attachments(client):
    """Test task attachment operations."""
    # Create a test task
    task = await client.tasks.create(
        name=f"Attachment Test Task {datetime.now().isoformat()}",
        list_id=LIST_ID,
        description="Test task for attachments",
    )

    try:
        # Create a temporary test file
        test_file_path = "test_attachment.txt"
        test_content = b"Test attachment content"
        with open(test_file_path, "wb") as f:
            f.write(test_content)

        # Test uploading file by path
        attachment = await client.tasks.create_attachment(
            task_id=task.id,
            file_path=test_file_path,
        )
        assert attachment is not None
        assert "id" in attachment
        assert "title" in attachment
        assert attachment["title"] == "test_attachment.txt"

        # Test uploading file with raw data
        attachment2 = await client.tasks.create_attachment(
            task_id=task.id,
            file_data=b"Another test attachment",
            file_name="test_attachment2.txt",
        )
        assert attachment2 is not None
        assert "id" in attachment2
        assert "title" in attachment2
        assert attachment2["title"] == "test_attachment2.txt"

        # Test error cases
        with pytest.raises(
            ValueError, match="Either file_path or file_data must be provided"
        ):
            await client.tasks.create_attachment(task_id=task.id)

        with pytest.raises(
            ValueError, match="Cannot provide both file_path and file_data"
        ):
            await client.tasks.create_attachment(
                task_id=task.id,
                file_path=test_file_path,
                file_data=b"test",
            )

        with pytest.raises(
            ValueError, match="file_name is required when using file_data"
        ):
            await client.tasks.create_attachment(
                task_id=task.id,
                file_data=b"test",
            )

        with pytest.raises(ValueError, match="File not found"):
            await client.tasks.create_attachment(
                task_id=task.id,
                file_path="nonexistent_file.txt",
            )

    finally:
        # Clean up
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        await client.tasks.delete(task.id)
