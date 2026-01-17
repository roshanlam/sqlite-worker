# Task Queue System with sqlite-worker

This example demonstrates how to build a distributed task queue system using sqlite-worker for reliable task scheduling and execution.

## Features

- **Priority-based Task Scheduling**: Tasks are executed based on priority (CRITICAL > HIGH > NORMAL > LOW)
- **Scheduled Tasks**: Schedule tasks to run at specific times
- **Automatic Retries**: Configurable retry logic for failed tasks
- **Multi-worker Support**: Multiple workers can process tasks concurrently
- **Task Status Tracking**: Monitor task lifecycle (pending, running, completed, failed)
- **Thread-safe Operations**: Safe concurrent access with sqlite-worker
- **Task Persistence**: Tasks survive process restarts

## Installation

```bash
pip install sqlite-worker
```

## Running the Example

```bash
python task_queue.py
```

## Architecture

### Task States

```
PENDING → RUNNING → COMPLETED
    ↓         ↓
CANCELLED  FAILED (with retry)
```

### Key Components

1. **TaskQueue Class**: Manages task lifecycle and queue operations
2. **Worker Threads**: Poll queue and execute tasks
3. **Task Handlers**: Functions that perform actual work
4. **Status Tracking**: Monitor task progress and statistics

## Usage Examples

### Basic Task Enqueueing

```python
from task_queue import TaskQueue, TaskPriority

queue = TaskQueue()

# Add a task
task_id = queue.enqueue(
    name="Send welcome email",
    task_type="send_email",
    payload={"to": "user@example.com", "subject": "Welcome!"},
    priority=TaskPriority.HIGH
)
```

### Scheduled Tasks

```python
from datetime import datetime, timedelta

# Schedule task for 1 hour from now
scheduled_time = datetime.now() + timedelta(hours=1)
queue.enqueue(
    name="Daily cleanup",
    task_type="cleanup",
    scheduled_at=scheduled_time
)
```

### Processing Tasks

```python
# Start a worker
def worker_process(queue):
    while True:
        task = queue.dequeue()
        if task:
            # Process task
            result = process_task(task)
            queue.complete_task(task['id'], result)
```

### Monitoring Queue

```python
# Get queue statistics
stats = queue.get_queue_stats()
print(f"Pending: {stats['pending']}")
print(f"Running: {stats['running']}")
print(f"Completed: {stats['completed']}")

# Get tasks by status
completed_tasks = queue.get_tasks_by_status(TaskStatus.COMPLETED, limit=10)
```

## Use Cases

### 1. Background Job Processing
- Email sending
- Report generation
- Data synchronization
- File processing

### 2. Scheduled Tasks
- Daily backups
- Periodic cleanups
- Scheduled reports
- Reminder notifications

### 3. Distributed Work
- Image processing pipeline
- Video encoding
- Data ETL jobs
- Batch operations

### 4. Rate Limiting
- API request queuing
- Resource-intensive operations
- Throttled external API calls

## Configuration Options

### Task Priority

```python
TaskPriority.CRITICAL  # 4 - Highest priority
TaskPriority.HIGH      # 3
TaskPriority.NORMAL    # 2 - Default
TaskPriority.LOW       # 1
```

### Retry Configuration

```python
queue.enqueue(
    name="Flaky task",
    task_type="external_api",
    max_retries=5,  # Will retry up to 5 times
    payload={...}
)
```

## Performance Tips

1. **Worker Scaling**: Add more workers for higher throughput
2. **Batch Operations**: Use `max_count` for efficient commits
3. **Indexing**: Pre-created indexes on status and priority
4. **WAL Mode**: Enabled for better concurrent performance
5. **Connection Pooling**: Each worker maintains its own connection

## Expected Output

```
============================================================
Task Queue System Demo
============================================================

📝 Enqueueing tasks...
📝 Enqueued task #1: Send welcome email (priority: HIGH)
📝 Enqueued task #2: Generate sales report (priority: HIGH)
📝 Enqueued task #3: Process image 1 (priority: NORMAL)
...

📊 Initial Queue Stats:
   pending: 8

🚀 Starting workers...

🔧 Worker started: Worker-1
🔧 Worker started: Worker-2
🔧 Worker started: Worker-3

⚙️  Processing task #1: Send welcome email
   📧 Sending email to user@example.com
   Subject: Welcome!
✅ Task #1 completed

⚙️  Processing task #2: Generate sales report
   📊 Generating sales report
✅ Task #2 completed

...

============================================================
📊 Final Queue Stats:
   completed: 7
   pending: 1

✅ Recently Completed Tasks:
   #8: Scheduled cleanup
   #7: Send newsletter
   ...

✅ Demo completed successfully!
```

## Advanced Features

### Custom Task Handlers

```python
def custom_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Your custom logic here
    result = do_something(payload)
    return {"success": True, "data": result}

# Register handler
TASK_HANDLERS['custom_task'] = custom_handler
```

### Error Handling

```python
try:
    result = handler(task['payload'])
    queue.complete_task(task['id'], result)
except Exception as e:
    queue.fail_task(task['id'], str(e))
```

## Integration Examples

- Integrate with web frameworks (Flask, FastAPI)
- Use as a message queue alternative
- Build distributed systems
- Create job processing pipelines

## Production Considerations

1. **Monitoring**: Add logging and metrics
2. **Graceful Shutdown**: Handle worker termination
3. **Dead Letter Queue**: Handle permanently failed tasks
4. **Rate Limiting**: Implement task throttling
5. **Task Timeouts**: Add execution time limits
