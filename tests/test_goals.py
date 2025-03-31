import asyncio
from datetime import datetime, timedelta

import pytest

from src.exceptions import ResourceNotFound
from src.models import KeyResultType


@pytest.mark.asyncio
async def test_goal_crud_operations(client, workspace):
    """Test creating, reading, updating, and deleting goals."""
    # Create a goal
    name = f"Test Goal {datetime.now()}"
    due_date = datetime.now() + timedelta(days=7)
    description = "Test goal description"

    created_goal = await client.create_goal(
        name=name,
        due_date=due_date,
        description=description,
        workspace_id=workspace.id,
    )

    assert created_goal.name == name
    assert created_goal.description == description

    # Get the goal and verify
    retrieved_goal = await client.get_goal(created_goal.id)
    assert retrieved_goal.id == created_goal.id
    assert retrieved_goal.name == name

    # Update the goal
    new_name = f"Updated Goal {datetime.now()}"
    updated_goal = await client.update_goal(
        goal_id=created_goal.id,
        name=new_name,
    )
    assert updated_goal.name == new_name

    # Get all goals and verify our goal is there
    goals = await client.get_goals(workspace_id=workspace.id)
    assert any(goal.id == created_goal.id for goal in goals)

    # Delete the goal
    assert await client.delete_goal(created_goal.id)

    # Verify deletion
    with pytest.raises(ResourceNotFound):
        await client.get_goal(created_goal.id)


@pytest.mark.asyncio
async def test_key_result_crud_operations(client, workspace):
    """Test creating, reading, updating, and deleting key results."""
    # First create a goal to add key results to
    goal = await client.create_goal(
        name=f"Test Goal for KR {datetime.now()}",
        due_date=datetime.now() + timedelta(days=7),
        description="Test goal for key results",
        workspace_id=workspace.id,
    )

    try:
        # Create a key result
        name = f"Test Key Result {datetime.now()}"
        kr_type = KeyResultType.NUMBER
        steps_start = 0
        steps_end = 100
        unit = "points"

        created_kr = await client.create_key_result(
            goal_id=goal.id,
            name=name,
            type=kr_type,
            steps_start=steps_start,
            steps_end=steps_end,
            unit=unit,
        )

        assert created_kr.name == name
        assert created_kr.type == kr_type
        assert created_kr.steps_start == steps_start
        assert created_kr.steps_end == steps_end
        assert created_kr.unit == unit

        # Update the key result
        new_steps_current = 50
        updated_kr = await client.update_key_result(
            key_result_id=created_kr.id,
            steps_current=new_steps_current,
        )
        assert updated_kr.steps_current == new_steps_current

        # Delete the key result
        assert await client.delete_key_result(created_kr.id)

        # Verify the goal still exists after key result deletion
        goal_after = await client.get_goal(goal.id)
        assert goal_after.id == goal.id

    finally:
        # Clean up by deleting the goal
        await client.delete_goal(goal.id)


@pytest.mark.asyncio
async def test_goal_with_multiple_key_results(client, workspace):
    """Test managing multiple key results for a single goal."""
    # Create a goal
    goal = await client.create_goal(
        name=f"Multi KR Goal {datetime.now()}",
        due_date=datetime.now() + timedelta(days=7),
        description="Goal with multiple key results",
        workspace_id=workspace.id,
    )

    try:
        # Create multiple key results of different types
        kr_configs = [
            {
                "name": "Number KR",
                "type": KeyResultType.NUMBER,
                "steps_start": 0,
                "steps_end": 100,
                "unit": "items",
            },
            {
                "name": "Percentage KR",
                "type": KeyResultType.PERCENTAGE,
                "steps_start": 0,
                "steps_end": 100,
                "unit": "%",
            },
            {
                "name": "Currency KR",
                "type": KeyResultType.CURRENCY,
                "steps_start": 0,
                "steps_end": 1000,
                "unit": "USD",
            },
        ]

        key_results = []
        for config in kr_configs:
            kr = await client.create_key_result(goal_id=goal.id, **config)
            key_results.append(kr)
            await asyncio.sleep(1)  # Small delay between creations

        # Verify all key results were created with correct types
        for kr, config in zip(key_results, kr_configs):
            assert kr.name == config["name"]
            assert kr.type == config["type"]
            assert kr.unit == config["unit"]

        # Update progress on all key results
        for kr in key_results:
            updated_kr = await client.update_key_result(
                key_result_id=kr.id,
                steps_current=kr.steps_end // 2,  # Set to 50% progress
            )
            assert updated_kr.steps_current == kr.steps_end // 2
            await asyncio.sleep(1)  # Small delay between updates

        # Delete all key results
        for kr in key_results:
            assert await client.delete_key_result(kr.id)
            await asyncio.sleep(1)  # Small delay between deletions

    finally:
        # Clean up by deleting the goal
        await client.delete_goal(goal.id)
