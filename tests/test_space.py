"""
Tests for ClickUp space operations.
"""

import uuid

import pytest

from src import Space
from src.exceptions import ClickUpError, ResourceNotFound


@pytest.mark.asyncio
async def test_get_spaces(client, workspace):
    """Test getting all spaces in a workspace."""
    # Test getting non-archived spaces
    spaces = await client.spaces.get_spaces(workspace.id)
    assert isinstance(spaces, list)
    assert all(isinstance(s, Space) for s in spaces)
    assert all(not s.archived for s in spaces)

    # Test getting archived spaces
    archived_spaces = await client.spaces.get_spaces(workspace.id, archived=True)
    assert isinstance(archived_spaces, list)
    assert all(isinstance(s, Space) for s in archived_spaces)


@pytest.mark.asyncio
async def test_get_space(client, test_space):
    """Test getting a specific space."""
    space_details = await client.spaces.get_space(test_space.id)
    assert isinstance(space_details, Space)
    assert space_details.id == test_space.id
    assert space_details.name == test_space.name
    assert hasattr(space_details, "features")
    assert hasattr(space_details, "members")
    assert hasattr(space_details, "statuses")


@pytest.mark.asyncio
async def test_space_fluent_interface(client, test_space):
    """Test the fluent interface for space operations."""
    # Test chaining space operations
    space_details = await client.space(test_space.id).spaces.get_space()
    assert isinstance(space_details, Space)
    assert space_details.id == test_space.id
    assert space_details.name == test_space.name

    # Test chaining with update
    new_name = f"Fluent Updated Space {uuid.uuid4()}"
    updated_space = await client.space(test_space.id).spaces.update_space(name=new_name)
    assert isinstance(updated_space, Space)
    assert updated_space.id == test_space.id
    assert updated_space.name == new_name


@pytest.mark.asyncio
async def test_delete_space(client, workspace):
    """Test creating and deleting a space."""
    space_name = f"Test Space to Delete {uuid.uuid4()}"

    try:
        # Create a space to delete
        space = await client.spaces.create_space(
            name=space_name,
            workspace_id=workspace.id,
            private=False,
            admin_can_manage=True,
            multiple_assignees=True,
        )
    except ClickUpError as e:
        if "Your plan is limited" in str(e):
            pytest.skip("Test skipped: Free plan has reached space limit")
        raise

    # Delete the space
    result = await client.spaces.delete_space(space.id)
    assert result is True

    # Verify the space is deleted
    with pytest.raises(ResourceNotFound):
        await client.spaces.get_space(space.id)


@pytest.mark.asyncio
async def test_update_space_name(client, test_space):
    """Test updating a space's name."""
    new_name = f"Updated Space Name {uuid.uuid4()}"

    # Update the space name
    updated_space = await client.spaces.update_space(
        space_id=test_space.id, name=new_name
    )

    # Verify the update
    assert isinstance(updated_space, Space)
    assert updated_space.id == test_space.id
    assert updated_space.name == new_name

    # Verify other properties remain unchanged
    assert updated_space.private == test_space.private
    assert updated_space.multiple_assignees == test_space.multiple_assignees
    assert updated_space.color == test_space.color
    assert updated_space.features == test_space.features
