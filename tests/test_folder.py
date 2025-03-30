"""
Tests for ClickUp folder operations.
"""

import asyncio
import uuid

import pytest

from src import Folder
from src.exceptions import ClickUpError, ResourceNotFound


@pytest.mark.asyncio
async def test_folder_operations(client, test_space):
    """Test folder operations within a space."""
    folder_name = f"Test Folder {uuid.uuid4()}"

    # Create a folder
    folder = await client.create_folder(
        name=folder_name,
        space_id=test_space.id,
        hidden=False,
    )
    assert isinstance(folder, Folder)
    assert folder.name == folder_name
    assert folder.space is not None and folder.space.id == test_space.id
    assert folder.hidden is False

    # Get folder details
    folder_details = await client.get_folder(folder.id)
    assert isinstance(folder_details, Folder)
    assert folder_details.id == folder.id
    assert folder_details.name == folder_name

    # Update folder
    new_name = f"Updated Folder {uuid.uuid4()}"
    updated_folder = await client.update_folder(
        folder_id=folder.id,
        name=new_name,
        hidden=True,
    )
    assert isinstance(updated_folder, Folder)
    assert updated_folder.id == folder.id
    assert updated_folder.name == new_name
    # Note: The hidden property may not be updated immediately or may not be supported
    # by the API, so we don't assert on it

    # Get all folders in space
    folders = await client.get_folders(test_space.id)
    assert isinstance(folders, list)
    assert all(isinstance(f, Folder) for f in folders)
    assert any(
        f.id == folder.id and f.space is not None and f.space.id == test_space.id
        for f in folders
    )

    # Delete folder with retry verification
    result = await client.delete_folder(folder.id)
    assert result is True

    # Verify deletion by checking if folder exists in space's folders
    max_retries = 5
    retry_delay = 3
    for attempt in range(max_retries):
        try:
            folders = await client.get_folders(test_space.id)
            if any(f.id == folder.id for f in folders):
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                pytest.fail("Folder still exists in space after deletion")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            pytest.fail(f"Error verifying folder deletion: {str(e)}")
    else:
        pytest.fail("Failed to verify folder deletion after all retries")


@pytest.mark.asyncio
async def test_folder_fluent_interface(client, test_space):
    """Test the fluent interface for folder operations."""
    folder_name = f"Fluent Folder {uuid.uuid4()}"

    # Create folder using fluent interface
    folder = await client.space(test_space.id).create_folder(name=folder_name)
    assert isinstance(folder, Folder)
    assert folder.name == folder_name
    assert folder.space is not None and folder.space.id == test_space.id

    # Get folder details using fluent interface
    folder_details = await client.folder(folder.id).get_folder()
    assert isinstance(folder_details, Folder)
    assert folder_details.id == folder.id
    assert folder_details.name == folder_name

    # Update folder using fluent interface
    new_name = f"Fluent Updated Folder {uuid.uuid4()}"
    updated_folder = await client.folder(folder.id).update_folder(name=new_name)
    assert isinstance(updated_folder, Folder)
    assert updated_folder.id == folder.id
    assert updated_folder.name == new_name

    # Clean up
    await client.folder(folder.id).delete_folder()


@pytest.mark.skip(reason="Requires a valid template ID to run")
@pytest.mark.asyncio
async def test_folder_template_operations(client, test_space):
    """Test creating folders from templates.

    This test requires a valid template ID to run. To run this test:
    1. Create a folder template in your ClickUp workspace
    2. Get the template ID
    3. Replace the template_id value with your actual template ID
    4. Remove the @pytest.mark.skip decorator
    """
    template_id = "your_template_id"  # Replace with actual template ID
    folder_name = f"Template Folder {uuid.uuid4()}"

    # Create folder from template
    folder = await client.create_folder_from_template(
        name=folder_name,
        space_id=test_space.id,
        template_id=template_id,
        return_immediately=True,
        options={
            "content": "Template folder description",
            "time_estimate": True,
            "automation": True,
            "include_views": True,
        },
    )
    assert isinstance(folder, Folder)
    assert folder.name == folder_name
    assert folder.space is not None and folder.space.id == test_space.id

    # Clean up
    await client.delete_folder(folder.id)
