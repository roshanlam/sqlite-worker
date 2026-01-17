"""
Task Queue System using sqlite-worker

This example demonstrates how to build a distributed task queue system
using sqlite-worker for reliable task scheduling and execution.
"""

from sqlite_worker import SqliteWorker
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import enum


class TaskStatus(enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(enum.Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskQueue:
    """A distributed task queue system using sqlite-worker"""
    
    def __init__(self, db_path: str = "taskqueue.db"):
        """Initialize the task queue"""
        self.worker = SqliteWorker(
            db_path,
            execute_init=[
                "PRAGMA journal_mode=WAL;",
                "PRAGMA synchronous=NORMAL;",
                "PRAGMA temp_store=MEMORY;"
            ],
            max_count=50
        )
        self._initialize_schema()
        self._worker_id = threading.current_thread().name
        self._running = False
    
    def _initialize_schema(self):
        """Create database schema for task queue"""
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                payload TEXT,
                priority INTEGER DEFAULT 2,
                status TEXT DEFAULT 'pending',
                worker_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                max_retries INTEGER DEFAULT 3,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                result TEXT
            )
        """)
        
        # Create indexes for performance
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
            ON tasks(status)
        """)
        
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_priority 
            ON tasks(priority DESC, created_at ASC)
        """)
        
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_scheduled 
            ON tasks(scheduled_at)
        """)
    
    def enqueue(
        self,
        name: str,
        task_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3
    ) -> int:
        """
        Add a task to the queue
        
        Args:
            name: Human-readable task name
            task_type: Type of task (for routing to handlers)
            payload: Task data as dictionary
            priority: Task priority level
            scheduled_at: When to execute (None for immediate)
            max_retries: Maximum retry attempts
            
        Returns:
            Task ID
        """
        task_data = {
            "name": name,
            "task_type": task_type,
            "payload": json.dumps(payload or {}),
            "priority": priority.value,
            "max_retries": max_retries
        }
        
        if scheduled_at:
            task_data["scheduled_at"] = scheduled_at.isoformat()
        
        token = self.worker.insert("tasks", task_data)
        result = self.worker.fetch_results(token)
        
        # Get the task ID
        token = self.worker.execute(
            "SELECT id FROM tasks WHERE rowid = last_insert_rowid()"
        )
        task_id = self.worker.fetch_results(token)[0][0]
        
        print(f"📝 Enqueued task #{task_id}: {name} (priority: {priority.name})")
        return task_id
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get the next available task to process
        
        Returns:
            Task dictionary or None if no tasks available
        """
        current_time = datetime.now().isoformat()
        
        # Find pending task with highest priority
        token = self.worker.execute("""
            SELECT id, name, task_type, payload, retry_count, max_retries
            FROM tasks
            WHERE status = 'pending'
            AND (scheduled_at IS NULL OR scheduled_at <= ?)
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        """, (current_time,))
        
        tasks = self.worker.fetch_results(token)
        
        if not tasks:
            return None
        
        task = tasks[0]
        task_id = task[0]
        
        # Mark task as running
        self.worker.update(
            "tasks",
            {
                "status": TaskStatus.RUNNING.value,
                "worker_id": self._worker_id,
                "started_at": datetime.now().isoformat()
            },
            {"id": task_id}
        )
        
        return {
            "id": task_id,
            "name": task[1],
            "task_type": task[2],
            "payload": json.loads(task[3]),
            "retry_count": task[4],
            "max_retries": task[5]
        }
    
    def complete_task(self, task_id: int, result: Optional[Dict[str, Any]] = None):
        """Mark task as completed"""
        self.worker.update(
            "tasks",
            {
                "status": TaskStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat(),
                "result": json.dumps(result or {})
            },
            {"id": task_id}
        )
        print(f"✅ Task #{task_id} completed")
    
    def fail_task(self, task_id: int, error_message: str):
        """Mark task as failed or retry if retries available"""
        # Get current task info
        token = self.worker.select("tasks", conditions={"id": task_id})
        tasks = self.worker.fetch_results(token)
        
        if not tasks:
            return
        
        task = tasks[0]
        retry_count = task[11]
        max_retries = task[10]
        
        if retry_count < max_retries:
            # Retry the task
            self.worker.update(
                "tasks",
                {
                    "status": TaskStatus.PENDING.value,
                    "retry_count": retry_count + 1,
                    "error_message": error_message,
                    "worker_id": None,
                    "started_at": None
                },
                {"id": task_id}
            )
            print(f"🔄 Task #{task_id} retry {retry_count + 1}/{max_retries}")
        else:
            # Mark as failed
            self.worker.update(
                "tasks",
                {
                    "status": TaskStatus.FAILED.value,
                    "completed_at": datetime.now().isoformat(),
                    "error_message": error_message
                },
                {"id": task_id}
            )
            print(f"❌ Task #{task_id} failed: {error_message}")
    
    def cancel_task(self, task_id: int):
        """Cancel a pending task"""
        token = self.worker.select("tasks", conditions={"id": task_id})
        tasks = self.worker.fetch_results(token)
        
        if tasks and tasks[0][5] == TaskStatus.PENDING.value:
            self.worker.update(
                "tasks",
                {"status": TaskStatus.CANCELLED.value},
                {"id": task_id}
            )
            print(f"🚫 Task #{task_id} cancelled")
            return True
        return False
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        token = self.worker.execute("""
            SELECT status, COUNT(*) as count
            FROM tasks
            GROUP BY status
        """)
        results = self.worker.fetch_results(token)
        
        stats = {status.value: 0 for status in TaskStatus}
        for status, count in results:
            stats[status] = count
        
        return stats
    
    def get_tasks_by_status(self, status: TaskStatus, limit: int = 10) -> List[Dict]:
        """Get tasks by status"""
        token = self.worker.select(
            "tasks",
            conditions={"status": status.value},
            order_by="created_at DESC",
            limit=limit
        )
        tasks = self.worker.fetch_results(token)
        
        return [
            {
                "id": task[0],
                "name": task[1],
                "task_type": task[2],
                "status": task[5],
                "created_at": task[7]
            }
            for task in tasks
        ]
    
    def close(self):
        """Close the database connection"""
        self.worker.close()


# Task handler functions
def send_email_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate sending an email"""
    print(f"   📧 Sending email to {payload['to']}")
    print(f"   Subject: {payload['subject']}")
    time.sleep(0.5)  # Simulate email sending
    return {"sent": True, "message_id": f"msg_{int(time.time())}"}


def process_image_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate image processing"""
    print(f"   🖼️  Processing image: {payload['filename']}")
    time.sleep(1.0)  # Simulate image processing
    return {"processed": True, "output": f"processed_{payload['filename']}"}


def generate_report_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate report generation"""
    print(f"   📊 Generating {payload['report_type']} report")
    time.sleep(0.8)  # Simulate report generation
    return {"generated": True, "report_url": f"/reports/{payload['report_type']}.pdf"}


# Task handlers registry
TASK_HANDLERS = {
    "send_email": send_email_task,
    "process_image": process_image_task,
    "generate_report": generate_report_task,
}


def worker_process(queue: TaskQueue, duration: int = 10):
    """Process tasks from the queue"""
    print(f"\n🔧 Worker started: {threading.current_thread().name}")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        task = queue.dequeue()
        
        if task:
            print(f"\n⚙️  Processing task #{task['id']}: {task['name']}")
            
            try:
                # Get the handler for this task type
                handler = TASK_HANDLERS.get(task['task_type'])
                
                if not handler:
                    raise ValueError(f"Unknown task type: {task['task_type']}")
                
                # Execute the task
                result = handler(task['payload'])
                queue.complete_task(task['id'], result)
                
            except Exception as e:
                queue.fail_task(task['id'], str(e))
        else:
            # No tasks available, wait a bit
            time.sleep(0.5)
    
    print(f"\n🛑 Worker stopped: {threading.current_thread().name}")


def main():
    """Main demonstration"""
    print("=" * 60)
    print("Task Queue System Demo")
    print("=" * 60)
    
    # Initialize queue
    queue = TaskQueue()
    
    # Enqueue various tasks with different priorities
    print("\n📝 Enqueueing tasks...")
    
    # High priority tasks
    queue.enqueue(
        "Send welcome email",
        "send_email",
        {"to": "user@example.com", "subject": "Welcome!"},
        priority=TaskPriority.HIGH
    )
    
    queue.enqueue(
        "Generate sales report",
        "generate_report",
        {"report_type": "sales", "period": "monthly"},
        priority=TaskPriority.HIGH
    )
    
    # Normal priority tasks
    for i in range(5):
        queue.enqueue(
            f"Process image {i+1}",
            "process_image",
            {"filename": f"photo_{i+1}.jpg"},
            priority=TaskPriority.NORMAL
        )
    
    # Low priority tasks
    queue.enqueue(
        "Send newsletter",
        "send_email",
        {"to": "subscribers@example.com", "subject": "Monthly Newsletter"},
        priority=TaskPriority.LOW
    )
    
    # Scheduled task (5 seconds from now)
    scheduled_time = datetime.now() + timedelta(seconds=5)
    queue.enqueue(
        "Scheduled cleanup",
        "generate_report",
        {"report_type": "cleanup", "period": "daily"},
        priority=TaskPriority.NORMAL,
        scheduled_at=scheduled_time
    )
    
    # Show initial stats
    print("\n📊 Initial Queue Stats:")
    stats = queue.get_queue_stats()
    for status, count in stats.items():
        if count > 0:
            print(f"   {status}: {count}")
    
    # Start worker threads
    print("\n🚀 Starting workers...")
    workers = []
    for i in range(3):
        worker = threading.Thread(
            target=worker_process,
            args=(queue, 10),
            name=f"Worker-{i+1}"
        )
        worker.start()
        workers.append(worker)
    
    # Wait for all workers to complete
    for worker in workers:
        worker.join()
    
    # Show final stats
    print("\n" + "=" * 60)
    print("📊 Final Queue Stats:")
    stats = queue.get_queue_stats()
    for status, count in stats.items():
        if count > 0:
            print(f"   {status}: {count}")
    
    # Show completed tasks
    print("\n✅ Recently Completed Tasks:")
    completed = queue.get_tasks_by_status(TaskStatus.COMPLETED, limit=5)
    for task in completed:
        print(f"   #{task['id']}: {task['name']}")
    
    # Cleanup
    queue.close()
    
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    main()
