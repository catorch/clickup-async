"""
Tests for ClickUp comment operations.
"""

import asyncio
from datetime import datetime

import pytest

from src.models import Comment


@pytest.mark.asyncio
async def test_task_comments(client, test_space):
    """Test task comment operations."""
    # Create a test list using the resource interface
    test_list = await client.lists.create(
        name=f"Comment Test List {datetime.now().isoformat()}",
        space_id=test_space.id,
    )

    # Create a test task using the resource interface
    task = await client.tasks.create(
        name=f"Comment Test Task {datetime.now().isoformat()}",
        list_id=test_list.id,
        description="Test task for comments",
    )

    try:
        # Create a comment using the resource interface
        comment = await client.comments.create_task_comment(
            task_id=task.id,
            comment_text="Test comment",
            notify_all=False,
        )
        assert isinstance(comment, Comment)
        assert comment.content == "Test comment"

        # Get comments using the resource interface
        comments = await client.comments.get_task_comments(task.id)
        assert len(comments) > 0
        assert any(c.id == comment.id for c in comments)

        # Update comment using the resource interface
        updated_comment = await client.comments.update(
            comment_id=comment.id,
            comment_text="Updated test comment",
            resolved=True,
        )
        assert isinstance(updated_comment, Comment)
        assert updated_comment.content == "Updated test comment"
        assert updated_comment.resolved is True

        # Create a threaded comment using the resource interface
        reply = await client.comments.create_threaded_comment(
            comment_id=comment.id,
            comment_text="Test reply",
            notify_all=False,
        )
        assert isinstance(reply, Comment)
        assert reply.content == "Test reply"

        # Get threaded comments using the resource interface
        replies = await client.comments.get_threaded_comments(comment.id)
        assert len(replies) > 0
        assert any(r.id == reply.id for r in replies)

        # Delete comment using the resource interface
        result = await client.comments.delete(comment.id)
        assert result is True

        # Wait for deletion to propagate
        await asyncio.sleep(5)

        # Verify comment is deleted
        comments = await client.comments.get_task_comments(task.id)
        assert not any(c.id == comment.id for c in comments)

    finally:
        # Clean up using resource interface
        await client.tasks.delete(task.id)
        await client.lists.delete(test_list.id)


@pytest.mark.asyncio
async def test_list_comments(client, test_space):
    """Test list comment operations."""
    # Create a test list using the resource interface
    test_list = await client.lists.create(
        name=f"List Comment Test {datetime.now().isoformat()}",
        space_id=test_space.id,
    )

    try:
        # Create a comment using the resource interface
        comment = await client.comments.create_list_comment(
            list_id=test_list.id,
            comment_text="Test list comment",
            notify_all=False,
        )
        assert isinstance(comment, Comment)
        assert comment.content == "Test list comment"

        # Get comments using the resource interface
        comments = await client.comments.get_list_comments(test_list.id)
        assert len(comments) > 0
        assert any(c.id == comment.id for c in comments)

        # Update comment using the resource interface
        updated_comment = await client.comments.update(
            comment_id=comment.id,
            comment_text="Updated list comment",
        )
        assert isinstance(updated_comment, Comment)
        assert updated_comment.content == "Updated list comment"

        # Delete comment using the resource interface
        result = await client.comments.delete(comment.id)
        assert result is True

        # Wait for deletion to propagate
        await asyncio.sleep(5)

        # Verify comment is deleted
        comments = await client.comments.get_list_comments(test_list.id)
        assert not any(c.id == comment.id for c in comments)

    finally:
        # Clean up using resource interface
        await client.lists.delete(test_list.id)


@pytest.mark.asyncio
async def test_comment_pagination(client, test_space):
    """Test comment pagination functionality."""
    # Create a test list using the resource interface
    test_list = await client.lists.create(
        name=f"Pagination Test List {datetime.now().isoformat()}",
        space_id=test_space.id,
    )

    # Create a test task using the resource interface
    task = await client.tasks.create(
        name=f"Pagination Test Task {datetime.now().isoformat()}",
        list_id=test_list.id,
        description="Test task for comment pagination",
    )

    try:
        # Create multiple comments
        comment_ids = []
        for i in range(30):  # Create more than the default page size (25)
            comment = await client.comments.create_task_comment(
                task_id=task.id,
                comment_text=f"Test comment {i}",
                notify_all=False,
            )
            comment_ids.append(comment.id)
            await asyncio.sleep(0.1)  # Small delay to ensure different timestamps

        # Get first page of comments using resource interface
        first_page = await client.comments.get_task_comments(task.id)
        assert len(first_page) == 25  # Default page size

        # Get next page using the timestamp of the last comment
        if first_page:
            last_comment = first_page[-1]
            next_page = await client.comments.get_task_comments(
                task_id=task.id,
                start=int(last_comment.date),
                start_id=last_comment.id,
            )
            assert len(next_page) > 0
            assert all(c.id not in [fc.id for fc in first_page] for c in next_page)

        # Clean up comments
        for comment_id in comment_ids:
            await client.comments.delete(comment_id)
            # Short sleep to prevent rate limiting
            await asyncio.sleep(0.5)

    finally:
        # Clean up using resource interface
        await client.tasks.delete(task.id)
        await client.lists.delete(test_list.id)


@pytest.mark.asyncio
async def test_comment_with_assignee(client, test_space):
    """Test comment operations with assignees."""
    # Create a test list using the resource interface
    test_list = await client.lists.create(
        name=f"Assignee Test List {datetime.now().isoformat()}",
        space_id=test_space.id,
    )

    # Create a test task using the resource interface
    task = await client.tasks.create(
        name=f"Assignee Test Task {datetime.now().isoformat()}",
        list_id=test_list.id,
        description="Test task for comment assignees",
    )

    try:
        # Get workspace members to find an assignee using resource interface
        workspaces = await client.workspaces.get_workspaces()
        if not workspaces:
            pytest.skip("No workspaces found for assignee testing")

        workspace = workspaces[0]

        # Check if there are any members
        if not workspace.members:
            pytest.skip("No workspace members found for assignee testing")

        # Get the first member's user ID
        member = workspace.members[0]
        if (
            isinstance(member, dict)
            and "user" in member
            and isinstance(member["user"], dict)
        ):
            assignee = member["user"]["id"]
        else:
            # Skip if we can't find a valid assignee
            pytest.skip("Could not extract assignee ID from workspace members")

        # Create a comment with assignee using resource interface
        comment = await client.comments.create_task_comment(
            task_id=task.id,
            comment_text="Test comment with assignee",
            assignee=str(assignee),
            notify_all=False,
        )
        await asyncio.sleep(2)
        assert comment.content == "Test comment with assignee"

        # Update the comment using resource interface
        updated_comment = await client.comments.update(
            comment_id=comment.id,
            comment_text="Updated comment with assignee",
        )

        assert updated_comment.content == "Updated comment with assignee"

        # Delete the comment using resource interface
        await client.comments.delete(comment_id=comment.id)
        # Wait for deletion to propagate
        await asyncio.sleep(5)

    finally:
        # Clean up using resource interface
        await client.tasks.delete(task_id=task.id)
        await client.lists.delete(list_id=test_list.id)
