"""
Integration tests for ClickUp list operations.

These tests verify that the client works correctly with the real ClickUp API.
To run these tests, you need to set up the following environment variables:
- CLICKUP_API_TOKEN: Your ClickUp API token
- CLICKUP_SPACE_ID: ID of a space to test with
"""

import asyncio
import logging
import os
from datetime import datetime

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from src import ClickUp, TaskList
from src.exceptions import ResourceNotFound, ValidationError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("clickup")

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
SPACE_ID = os.getenv("CLICKUP_SPACE_ID")

# Skip all tests if required environment variables are not set
pytestmark = pytest.mark.skipif(
    not all([API_TOKEN, SPACE_ID]),
    reason="Required environment variables are not set",
)


@pytest_asyncio.fixture
async def client():
    """Create a ClickUp client instance for testing."""
    if not API_TOKEN:
        pytest.skip("API token not set")
    client = ClickUp(API_TOKEN)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_list_crud_operations(client):
    """Test CRUD operations for lists."""
    # First create a folder
    folder_name = f"Test Folder {datetime.now().isoformat()}"
    folder = await client.create_folder(
        name=folder_name,
        space_id=SPACE_ID,
    )

    try:
        # Create a test list in the folder
        list_name = f"Test List {datetime.now().isoformat()}"
        created_list = await client.create_list(
            name=list_name,
            folder_id=folder.id,
        )
        assert isinstance(created_list, TaskList)
        assert created_list.name == list_name
        assert created_list.folder is not None and created_list.folder.id == folder.id

        # Wait a moment for the list to be fully created
        await asyncio.sleep(2)

        # Get list details
        retrieved_list = await client.get_list(created_list.id)
        assert isinstance(retrieved_list, TaskList)
        assert retrieved_list.id == created_list.id
        assert retrieved_list.name == list_name

        # Update list
        new_name = f"Updated List {datetime.now().isoformat()}"
        updated_list = await client.update_list(
            list_id=created_list.id,
            name=new_name,
            content="Updated list description",
        )
        assert isinstance(updated_list, TaskList)
        assert updated_list.id == created_list.id
        assert updated_list.name == new_name
        assert updated_list.content == "Updated list description"

        # Wait a moment for the update to propagate
        await asyncio.sleep(2)

        # Verify update
        retrieved_list = await client.get_list(created_list.id)
        assert retrieved_list.name == new_name
        assert retrieved_list.content == "Updated list description"

        # Delete list
        result = await client.delete_list(created_list.id)
        assert result is True

        # Wait for deletion to propagate
        await asyncio.sleep(2)

        # Check what we actually get back after deletion
        deleted_list = await client.get_list(created_list.id)
        print(f"List after deletion: {deleted_list}")
    finally:
        # Clean up the folder
        await client.delete_folder(folder.id)


@pytest.mark.asyncio
async def test_list_markdown_support(client):
    """Test list operations with markdown support."""
    # Create a test list with markdown content
    list_name = f"Markdown Test List {datetime.now().isoformat()}"
    task_list = await client.create_list(
        name=list_name,
        space_id=SPACE_ID,
        content="# Test List\n\nThis is a **markdown** description.",
    )
    assert task_list is not None
    assert task_list.name == list_name

    # Get list with markdown support
    list_with_md = await client.get_list_with_markdown(
        list_id=task_list.id,
        include_markdown_description=True,
    )
    assert list_with_md is not None
    assert list_with_md.id == task_list.id
    assert "# Test List" in list_with_md.content

    # Clean up
    await client.delete_list(task_list.id)


@pytest.mark.asyncio
async def test_multiple_list_operations(client):
    """Test operations related to Tasks in Multiple Lists feature."""
    # Create two test lists
    list1_name = f"Multiple List Test 1 {datetime.now().isoformat()}"
    list2_name = f"Multiple List Test 2 {datetime.now().isoformat()}"

    list1 = await client.create_list(
        name=list1_name,
        space_id=SPACE_ID,
    )
    list2 = await client.create_list(
        name=list2_name,
        space_id=SPACE_ID,
    )

    # Create a test task in the first list
    task = await client.create_task(
        name=f"Multiple List Test Task {datetime.now().isoformat()}",
        list_id=list1.id,
        description="Test task for multiple list operations",
    )

    try:
        # Add task to second list
        try:
            result = await client.add_task_to_list(task.id, list2.id)
            assert result is True

            # Remove task from second list
            result = await client.remove_task_from_list(task.id, list2.id)
            assert result is True
        except ValidationError as e:
            if "Tasks in multiple lists limit exceeded" in str(e):
                pytest.skip(
                    "Workspace has reached the limit for tasks in multiple lists"
                )
            raise
    finally:
        # Clean up
        await client.delete_task(task.id)
        await client.delete_list(list1.id)
        await client.delete_list(list2.id)


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

    # Create list from template
    list_from_template = await client.create_list_from_template(
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
    await client.delete_list(list_from_template.id)


@pytest.mark.asyncio
async def test_list_fluent_interface(client):
    """Test the fluent interface for list operations."""
    # Create a test list using fluent interface
    list_name = f"Fluent Test List {datetime.now().isoformat()}"
    task_list = await client.space(SPACE_ID).create_list(name=list_name)
    assert task_list is not None
    assert task_list.name == list_name
    assert task_list.space is not None and task_list.space.id == SPACE_ID

    # Get list details using fluent interface
    list_details = await client.list(task_list.id).get_list()
    assert list_details is not None
    assert list_details.id == task_list.id
    assert list_details.name == list_name

    # Update list using fluent interface
    new_name = f"Fluent Updated List {datetime.now().isoformat()}"
    updated_list = await client.list(task_list.id).update_list(name=new_name)
    assert updated_list is not None
    assert updated_list.id == task_list.id
    assert updated_list.name == new_name

    # Clean up using fluent interface
    await client.list(task_list.id).delete_list()


@pytest.mark.asyncio
async def test_list_archived_operations(client):
    """Test operations with archived lists."""
    # Create a test list
    list_name = f"Archive Test List {datetime.now().isoformat()}"
    task_list = await client.create_list(
        name=list_name,
        space_id=SPACE_ID,
    )
    assert task_list is not None
    assert task_list.name == list_name

    # Get non-archived lists
    active_lists = await client.get_lists(space_id=SPACE_ID, archived=False)
    assert any(l.id == task_list.id for l in active_lists)

    # Get archived lists
    archived_lists = await client.get_lists(space_id=SPACE_ID, archived=True)
    assert not any(l.id == task_list.id for l in archived_lists)

    # Clean up
    await client.delete_list(task_list.id)
