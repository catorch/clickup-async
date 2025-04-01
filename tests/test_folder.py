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
    """Test basic folder operations."""
    folder_name = f"Test Folder {uuid.uuid4()}"

    # Create folder
    folder = await client.folders.create(name=folder_name, space_id=test_space.id)
    assert isinstance(folder, Folder)
    assert folder.name == folder_name

    # Get folder
    folder_details = await client.folders.get(folder.id)
    assert isinstance(folder_details, Folder)
    assert folder_details.id == folder.id

    # Update folder
    new_name = f"Updated Folder {uuid.uuid4()}"
    updated_folder = await client.folders.update(folder.id, name=new_name)
    assert isinstance(updated_folder, Folder)
    assert updated_folder.name == new_name

    # Delete folder
    result = await client.folders.delete(folder.id)
    assert result is True

    # Verify folder is deleted by checking if it exists in the space's folders
    folders = await client.folders.get_all(space_id=test_space.id)
    assert not any(f.id == folder.id for f in folders)


@pytest.mark.asyncio
async def test_folder_fluent_interface(client, test_space):
    """Test the fluent interface for folder operations."""
    folder_name = f"Fluent Folder {uuid.uuid4()}"

    # Create folder using fluent interface
    folder = await client.folders.create(name=folder_name, space_id=test_space.id)
    assert isinstance(folder, Folder)
    assert folder.name == folder_name

    # Get folder using fluent interface
    folder_details = await client.folder(folder.id).get()
    assert isinstance(folder_details, Folder)
    assert folder_details.id == folder.id

    # Update folder using fluent interface
    new_name = f"Updated Folder {uuid.uuid4()}"
    updated_folder = await client.folder(folder.id).update(name=new_name)
    assert isinstance(updated_folder, Folder)
    assert updated_folder.name == new_name

    # Delete folder using fluent interface
    result = await client.folder(folder.id).delete()
    assert result is True

    # Verify folder is deleted by checking if it exists in the space's folders
    folders = await client.folders.get_all(space_id=test_space.id)
    assert not any(f.id == folder.id for f in folders)


@pytest.mark.asyncio
async def test_folder_template_operations(client, test_space):
    """Test folder template operations."""
    pytest.skip("Requires a valid template ID to run")

    folder_name = f"Template Folder {uuid.uuid4()}"
    template_id = "template_id"  # Replace with a valid template ID

    # Create folder from template
    folder = await client.folders.create_from_template(
        name=folder_name,
        space_id=test_space.id,
        template_id=template_id,
    )
    assert isinstance(folder, Folder)
    assert folder.name == folder_name

    # Clean up
    await client.folders.delete(folder.id)
