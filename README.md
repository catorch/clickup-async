# ClickUp Async ✨

[![PyPI Version](https://img.shields.io/pypi/v/clickup-async.svg)](https://pypi.org/project/clickup-async/)
[![Python Versions](https://img.shields.io/pypi/pyversions/clickup-async.svg)](https://pypi.org/project/clickup-async/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/clickup-async/month)](https://pepy.tech/project/clickup-async)

A modern, high-performance Python client for the ClickUp API with first-class async support.

## Why Choose ClickUp Async?

| Feature | ClickUp Async | Other Libraries |
|---------|--------------|-----------------|
| **Async Support** | ✅ Full async/await | ❌ Synchronous only |
| **Type Safety** | ✅ Full type hints & validation | ❌ Limited or none |
| **Rate Limiting** | ✅ Intelligent handling | ❌ Basic or none |
| **Fluent Interface** | ✅ Clean, chainable API | ❌ Verbose calls |
| **Modern Python** | ✅ Python 3.9+ features | ❌ Legacy compatibility |
| **Error Handling** | ✅ Comprehensive | ❌ Basic exceptions |
| **Pagination** | ✅ Automatic | ❌ Manual handling |
| **Maintenance** | ✅ Active development | ❌ Limited updates |

## Installation

```bash
pip install clickup-async
```

## Quick Start

```python
import asyncio
from clickup_async import ClickUp
from clickup_async.models import Priority

async def main():
    # Use as a context manager for automatic cleanup
    async with ClickUp(api_token="your_token_here") as client:
        # Get authenticated user
        user = await client.get_authenticated_user()
        print(f"Authenticated as: {user.username}")
        
        # Get all workspaces
        workspaces = await client.workspaces.get_workspaces()
        
        # Create a task with fluent interface
        task = await client.list("your_list_id").tasks.create_task(
            name="Implement new feature",
            description="Add the awesome new feature",
            priority=Priority.HIGH,
            due_date="next Friday"
        )
        
        print(f"Created task: {task.name} (ID: {task.id})")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Features

### ⚡ Async First

All API operations use `httpx` for non-blocking I/O, making your applications more efficient and responsive.

```python
# Concurrent API calls
tasks = await asyncio.gather(
    client.get_task("task1"),
    client.get_task("task2"),
    client.get_task("task3")
)
```

### 🔄 Smart Rate Limiting

Automatically handles ClickUp API rate limits with exponential backoff and proactive throttling.

```python
# Configure rate limiting behavior
client = ClickUp(
    api_token="your_token",
    retry_rate_limited_requests=True,  # Auto retry when rate limited
    rate_limit_buffer=5                # Buffer seconds before hitting limits
)
```

### 🔍 Type Safety

Comprehensive type hints for better IDE integration and Pydantic models for runtime validation.

```python
# Full type hints
from clickup_async.models import Task, Workspace, Space

async def process_task(task: Task) -> None:
    # IDE auto-completion works!
    print(f"Task: {task.name}, Status: {task.status.status}")
```

### 📝 Fluent Interface

Intuitive, chainable API design that reflects ClickUp's resource hierarchy.

```python
# Access resources through the fluent interface
workspaces = await client.workspaces.get_workspaces()
spaces = await client.workspace("workspace_id").spaces.get_spaces()
folders = await client.space("space_id").folders.get_folders()
lists = await client.folder("folder_id").lists.get_lists()
tasks = await client.list("list_id").tasks.get_tasks()

# Create a comment on a task
comment = await client.task("task_id").comments.create_comment("Great work!")

# Work with docs
doc = await client.docs.create_doc(
    title="Project Requirements", 
    content="# Requirements\n\n...", 
    parent={"id": "folder_id", "type": "folder"}
)
```

### Working with Tasks

```python
from datetime import datetime, timedelta
from clickup_async.models import Priority

# Create a task
task = await client.list("list_id").tasks.create_task(
    name="New task",
    description="Task description with **markdown** support",
    priority=Priority.HIGH,
    due_date=datetime.now() + timedelta(days=7),
    assignees=["user_id"],
    tags=["feature", "backend"]
)

# Update a task
updated_task = await client.task("task_id").update(
    name="Updated task name",
    status="In Progress"
)

# Get tasks with filtering
tasks = await client.list("list_id").tasks.get_tasks(
    due_date_gt="today",
    due_date_lt="next week",
    assignees=["user_id"],
    include_closed=False
)
```

### Pagination Handling

```python
# Get first page of tasks
tasks_page = await client.list("list_id").tasks.get_tasks()

# Process all tasks across all pages
all_tasks = []
while True:
    all_tasks.extend(tasks_page.items)
    if not tasks_page.has_more:
        break
    tasks_page = await tasks_page.next_page()
```

## Development

1. Clone the repository
   ```bash
   git clone https://github.com/catorch/clickup-async.git
   cd clickup-async
   ```

2. Set up a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies
   ```bash
   pip install -e ".[dev,test]"
   ```

4. Run tests (requires a ClickUp API token in the environment)
   ```bash
   export CLICKUP_API_KEY=your_token_here
   pytest
   ```

## License

MIT License - See [LICENSE](LICENSE) for details.

---

⭐ If you find this library helpful, please consider starring it on GitHub!