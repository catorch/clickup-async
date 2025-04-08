"""
Integration tests for ClickUp tag operations.
"""

import asyncio
import logging
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from src import ClickUp, Space, Task
from src.exceptions import ResourceNotFound, ValidationError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("clickup")

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def test_tag(client: ClickUp, test_space: Space) -> AsyncGenerator[str, None]:
    """Creates a temporary Space tag for testing and ensures cleanup."""
    tag_name = f"test-tag-{uuid.uuid4()}"
    logger.info(f"Creating test tag: {tag_name} in space {test_space.id}")
    try:
        await client.tags.create_space_tag(
            space_id=test_space.id, name=tag_name, tag_bg="#FF0000"
        )
        logger.info(f"Created test tag: {tag_name}")
    except ValidationError as e:
        # Handle potential race condition if tag somehow already exists (unlikely with UUID)
        if "Tag name already exists" in str(e):
            logger.warning(f"Tag '{tag_name}' already exists, proceeding.")
        else:
            raise e

    yield tag_name  # Yield the name as the primary identifier

    # Cleanup
    try:
        logger.info(f"Cleaning up test tag: {tag_name}")
        await client.tags.delete_space_tag(space_id=test_space.id, tag_name=tag_name)
    except ResourceNotFound:
        logger.info(f"Tag {tag_name} already deleted or not found during cleanup.")
    except Exception as cleanup_e:
        logger.error(f"Error cleaning up tag {tag_name}: {cleanup_e}", exc_info=True)


@pytest.mark.asyncio
async def test_get_space_tags(client: ClickUp, test_space: Space, test_tag: str):
    """Test getting tags for a space."""
    # Add sleep after fixture creation to ensure tag is available
    await asyncio.sleep(5)
    tags = await client.tags.get_space_tags(space_id=test_space.id)
    assert isinstance(tags, list)
    # Check if the created test tag is in the list
    assert any(tag.name.lower() == test_tag for tag in tags)


@pytest.mark.asyncio
async def test_create_and_delete_space_tag(client: ClickUp, test_space: Space):
    """Test creating and immediately deleting a space tag."""
    tag_name = f"create-delete-test-{uuid.uuid4()}"
    try:
        # Create
        await client.tags.create_space_tag(space_id=test_space.id, name=tag_name)
        # Verify creation by getting all tags - Add sleep before verify
        await asyncio.sleep(5)
        tags = await client.tags.get_space_tags(space_id=test_space.id)
        assert any(tag.name.lower() == tag_name for tag in tags)
    finally:
        # Delete
        await client.tags.delete_space_tag(space_id=test_space.id, tag_name=tag_name)
        # Verify deletion - Add sleep before verify
        await asyncio.sleep(5)
        tags_after_delete = await client.tags.get_space_tags(space_id=test_space.id)
        assert not any(tag.name.lower() == tag_name for tag in tags_after_delete)


@pytest.mark.asyncio
async def test_edit_space_tag(client: ClickUp, test_space: Space, test_tag: str):
    """Test editing a space tag."""
    new_name = f"edited-tag-{uuid.uuid4()}"
    new_bg = "#00FF00"

    await client.tags.edit_space_tag(
        space_id=test_space.id,
        original_tag_name=test_tag,
        new_name=new_name,
        new_tag_bg=new_bg,
    )

    # Verify edit by getting all tags - Add sleep before verify
    await asyncio.sleep(5)
    tags = await client.tags.get_space_tags(space_id=test_space.id)
    edited_tag = next((tag for tag in tags if tag.name.lower() == new_name), None)

    assert edited_tag is not None, f"Edited tag '{new_name}' not found."
    assert edited_tag.tag_bg == new_bg

    # Cleanup the edited tag within the test itself
    try:
        await client.tags.delete_space_tag(space_id=test_space.id, tag_name=new_name)
        logger.info(f"Cleaned up edited tag: {new_name}")
    except ResourceNotFound:
        logger.warning(f"Edited tag {new_name} not found during test cleanup.")


@pytest.mark.asyncio
async def test_add_remove_tag_from_task(
    client: ClickUp, test_task: Task, test_tag: str
):
    """Test adding and removing a tag from a task."""
    # Add tag
    await client.tasks.add_tag_to_task(task_id=test_task.id, tag_name=test_tag)

    # Verify tag is added (by fetching task) - Add sleep before verify
    await asyncio.sleep(5)
    fetched_task = await client.tasks.get(task_id=test_task.id)
    assert isinstance(fetched_task.tags, list)
    assert any(tag.name.lower() == test_tag for tag in fetched_task.tags)

    # Remove tag
    await client.tasks.remove_tag_from_task(task_id=test_task.id, tag_name=test_tag)

    # Verify tag is removed - Add sleep before verify
    await asyncio.sleep(5)
    fetched_task_after_remove = await client.tasks.get(task_id=test_task.id)
    assert isinstance(fetched_task_after_remove.tags, list)
    assert not any(
        tag.name.lower() == test_tag for tag in fetched_task_after_remove.tags
    )
