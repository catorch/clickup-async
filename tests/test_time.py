"""
Integration tests for ClickUp time tracking operations.

These tests verify that the client works correctly with the real ClickUp API.
To run these tests, you need to set up the following environment variables:
- CLICKUP_API_TOKEN: Your ClickUp API token
- CLICKUP_WORKSPACE_ID: ID of a workspace to test with
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator, List
from uuid import uuid4

import pytest
import pytest_asyncio

from src import ClickUp, Task, TimeEntry
from src.exceptions import ClickUpError, ResourceNotFound, ValidationError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("clickup")

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def sample_time_entry(
    client: ClickUp, test_task: Task
) -> AsyncGenerator[TimeEntry, None]:
    """Creates a sample time entry for testing and cleans up afterwards."""
    description = f"test_time_entry_{uuid4()}"
    logger.info(f"Creating test time entry '{description}' for task {test_task.id}")

    created_entry = await client.time.create_entry(
        task_id=str(test_task.id),
        workspace_id=str(test_task.team_id),
        description=description,
        start=int(datetime.now().timestamp() * 1000),
        duration=60000,  # 1 minute
        billable=True,
    )
    assert isinstance(created_entry, TimeEntry)
    assert created_entry.description == description
    logger.info(f"Created time entry {created_entry.id}")

    yield created_entry

    # Cleanup
    try:
        logger.info(f"Cleaning up time entry {created_entry.id}")
        await client.time.delete_entry(
            time_entry_id=str(created_entry.id), workspace_id=str(test_task.team_id)
        )
    except (ResourceNotFound, ValidationError):
        logger.info(f"Time entry {created_entry.id} already deleted")
        pass


async def test_create_time_entry(client: ClickUp, test_task: Task):
    """Test creating a time entry."""
    description = f"test_create_{uuid4()}"
    created_entry = None

    try:
        created_entry = await client.time.create_entry(
            task_id=str(test_task.id),
            workspace_id=str(test_task.team_id),
            description=description,
            start=int(datetime.now().timestamp() * 1000),
            duration=60000,  # 1 minute
            billable=True,
            tags=[{"name": "Testing", "tag_bg": "#ff0000", "tag_fg": "#ffffff"}],
        )
        assert isinstance(created_entry, TimeEntry)
        assert created_entry.description == description
        assert str(created_entry.task_id) == str(test_task.id)
        assert created_entry.billable is True
    finally:
        if created_entry:
            try:
                await client.time.delete_entry(
                    time_entry_id=str(created_entry.id),
                    workspace_id=str(test_task.team_id),
                )
            except (ResourceNotFound, ValidationError):
                pass


async def test_start_stop_timer(client: ClickUp, test_task: Task):
    """Test starting and stopping a timer."""
    # Start timer
    started_entry = await client.time.start_timer(
        task_id=str(test_task.id), workspace_id=str(test_task.team_id)
    )
    assert isinstance(started_entry, TimeEntry)
    assert str(started_entry.task_id) == str(test_task.id)

    # Wait briefly to ensure timer runs
    await asyncio.sleep(2)

    # Stop timer
    stopped_entry = await client.time.stop_timer(workspace_id=str(test_task.team_id))
    assert isinstance(stopped_entry, TimeEntry)
    assert stopped_entry.end is not None

    # Cleanup
    try:
        await client.time.delete_entry(
            time_entry_id=str(stopped_entry.id), workspace_id=str(test_task.team_id)
        )
    except (ResourceNotFound, ValidationError):
        pass


async def test_get_time_entries(
    client: ClickUp, test_task: Task, sample_time_entry: TimeEntry
):
    """Test getting time entries with various filters."""
    # Get entries for last 24 hours
    now = datetime.now()
    yesterday = now - timedelta(days=1)

    entries = await client.time.get_entries(
        workspace_id=str(test_task.team_id),
        start_date=int(yesterday.timestamp() * 1000),
        end_date=int(now.timestamp() * 1000),
        task_id=str(test_task.id),
        include_task_tags=True,
        include_location_names=True,
    )

    assert isinstance(entries, list)
    assert len(entries) > 0
    assert any(str(entry.id) == str(sample_time_entry.id) for entry in entries)


async def test_update_time_entry(
    client: ClickUp, sample_time_entry: TimeEntry, test_task: Task
):
    """Test updating a time entry."""
    new_description = f"updated_{uuid4()}"

    updated_entry = await client.time.update_entry(
        time_entry_id=str(sample_time_entry.id),
        workspace_id=str(test_task.team_id),
        description=new_description,
        billable=False,
    )

    assert isinstance(updated_entry, TimeEntry)
    assert str(updated_entry.id) == str(sample_time_entry.id)
    assert updated_entry.description == new_description
    assert updated_entry.billable is False


async def test_get_single_time_entry(
    client: ClickUp, sample_time_entry: TimeEntry, test_task: Task
):
    """Test getting a single time entry."""
    entry = await client.time.get_entry(
        time_entry_id=str(sample_time_entry.id),
        workspace_id=str(test_task.team_id),
        include_task_tags=True,
        include_location_names=True,
    )

    assert isinstance(entry, TimeEntry)
    assert str(entry.id) == str(sample_time_entry.id)
    assert entry.description == sample_time_entry.description


async def test_get_time_entry_history(
    client: ClickUp, sample_time_entry: TimeEntry, test_task: Task
):
    """Test getting time entry history."""
    # First make a change to have some history
    await client.time.update_entry(
        time_entry_id=str(sample_time_entry.id),
        workspace_id=str(test_task.team_id),
        description=f"history_test_{uuid4()}",
    )

    # Get history
    history = await client.time.get_entry_history(
        time_entry_id=str(sample_time_entry.id), workspace_id=str(test_task.team_id)
    )
    assert isinstance(history, list)
    assert len(history) > 0


async def test_get_running_entry(client: ClickUp, test_task: Task):
    """Test getting the currently running time entry."""
    # Start a timer
    started_entry = await client.time.start_timer(
        task_id=str(test_task.id), workspace_id=str(test_task.team_id)
    )

    try:
        # Get running entry
        running_entry = await client.time.get_running_entry(
            workspace_id=str(test_task.team_id)
        )
        assert isinstance(running_entry, TimeEntry)
        assert str(running_entry.id) == str(started_entry.id)
        assert str(running_entry.task_id) == str(test_task.id)
    finally:
        # Stop and cleanup
        stopped_entry = await client.time.stop_timer(
            workspace_id=str(test_task.team_id)
        )
        try:
            await client.time.delete_entry(
                time_entry_id=str(stopped_entry.id), workspace_id=str(test_task.team_id)
            )
        except (ResourceNotFound, ValidationError):
            pass


async def test_tag_operations(
    client: ClickUp, sample_time_entry: TimeEntry, test_task: Task
):
    """Test associating and removing existing workspace time tags from an entry."""
    # 1. Get existing tags from the workspace
    logger.info("Fetching existing workspace time tags...")
    all_workspace_tags = await client.time.get_all_tags(
        workspace_id=str(test_task.team_id)
    )
    assert isinstance(all_workspace_tags, list)

    if not all_workspace_tags:
        logger.warning(
            "Workspace has no time tags defined. Skipping tag association/removal test."
        )
        pytest.skip("No existing workspace time tags found to test association.")
        return

    # 2. Select the first existing tag for testing
    tag_to_test = all_workspace_tags[0]
    logger.info(f"Using existing tag for testing: {tag_to_test['name']}")

    # 3. Associate the existing tag with the time entry
    await client.time.add_tags(
        time_entry_ids=[str(sample_time_entry.id)],
        tags=[tag_to_test],  # Pass the selected existing tag
        workspace_id=str(test_task.team_id),
    )

    # Allow time for potential API eventual consistency
    await asyncio.sleep(3)  # Increased sleep slightly just in case

    # 4. Verify Association
    logger.info("Verifying tag association...")
    entry_after_add = await client.time.get_entry(
        time_entry_id=str(sample_time_entry.id),
        workspace_id=str(test_task.team_id),
    )
    assert isinstance(
        entry_after_add.tags, list
    ), f"Expected tags to be a list, got: {type(entry_after_add.tags)}"
    associated_tag_names = {tag["name"] for tag in entry_after_add.tags}
    assert (
        tag_to_test["name"] in associated_tag_names
    ), f"Tag '{tag_to_test['name']}' not found in associated tags: {associated_tag_names}"
    logger.info(f"Tag '{tag_to_test['name']}' successfully associated.")

    # 5. Remove the associated tag
    logger.info(f"Removing associated tag: {tag_to_test['name']}")
    await client.time.remove_tags(
        time_entry_ids=[str(sample_time_entry.id)],
        tags=[tag_to_test],  # Remove the same tag
        workspace_id=str(test_task.team_id),
    )

    await asyncio.sleep(3)  # Increased sleep slightly just in case

    # 6. Verify Removal
    logger.info("Verifying tag removal...")
    entry_after_remove = await client.time.get_entry(
        time_entry_id=str(sample_time_entry.id),
        workspace_id=str(test_task.team_id),
    )
    # Assert that the specific tag is no longer present
    if entry_after_remove.tags:
        removed_tag_names = {tag["name"] for tag in entry_after_remove.tags}
        assert (
            tag_to_test["name"] not in removed_tag_names
        ), f"Tag '{tag_to_test['name']}' should have been removed, but found in: {removed_tag_names}"
    else:
        # If tags list is None or empty, removal is implicitly verified
        assert True
    logger.info(f"Tag '{tag_to_test['name']}' successfully removed.")


async def test_delete_time_entry(client: ClickUp, test_task: Task):
    """Test deleting a time entry."""
    # Create an entry to delete
    entry = await client.time.create_entry(
        task_id=str(test_task.id),
        workspace_id=str(test_task.team_id),
        description=f"to_delete_{uuid4()}",
        start=int(datetime.now().timestamp() * 1000),
        duration=60000,
    )

    # Delete it
    deleted = await client.time.delete_entry(
        time_entry_id=str(entry.id), workspace_id=str(test_task.team_id)
    )
    assert deleted is True

    # Verify deletion
    with pytest.raises(ResourceNotFound):
        await client.time.get_entry(
            time_entry_id=str(entry.id), workspace_id=str(test_task.team_id)
        )
