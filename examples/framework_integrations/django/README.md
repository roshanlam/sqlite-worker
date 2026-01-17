# Django Integration with sqlite-worker

This example demonstrates how to integrate sqlite-worker with Django for specialized use cases where you need direct database control alongside Django's ORM.

## Use Case

While Django has its own excellent ORM, you might want to use sqlite-worker for:
- Background task processing
- High-performance bulk operations
- Direct SQL for complex queries
- Separate analytics database
- Migration from legacy systems

## Setup

1. Install dependencies:
```bash
pip install django sqlite-worker
```

2. Create Django project (already done in this example):
```bash
django-admin startproject blog_project
cd blog_project
python manage.py startapp blog
```

3. Run migrations:
```bash
python manage.py migrate
python manage.py runserver
```

## Architecture

This example shows two database approaches:

### 1. Django ORM (Primary)
Used for main application models with all Django features:
- Automatic admin interface
- Form handling
- Authentication
- Migrations

### 2. sqlite-worker (Specialized)
Used for specific use cases:
- Analytics and statistics
- Background job queue
- Logging and audit trails
- High-performance reads

## Example Structure

```
django/
├── README.md
├── requirements.txt
└── blog_project/
    ├── manage.py
    ├── blog_project/
    │   ├── settings.py
    │   └── urls.py
    └── blog/
        ├── models.py
        ├── views.py
        ├── worker.py          # sqlite-worker integration
        └── management/
            └── commands/
                └── process_analytics.py
```

## Key Integration Points

### 1. Worker Singleton (worker.py)

```python
from sqlite_worker import SqliteWorker
import os
from django.conf import settings

class WorkerManager:
    _instance = None
    
    @classmethod
    def get_worker(cls):
        if cls._instance is None:
            db_path = os.path.join(settings.BASE_DIR, 'analytics.db')
            cls._instance = SqliteWorker(
                db_path,
                execute_init=[
                    "PRAGMA journal_mode=WAL;",
                    "PRAGMA synchronous=NORMAL;",
                ]
            )
        return cls._instance

worker = WorkerManager.get_worker()
```

### 2. Views Integration (views.py)

```python
from django.http import JsonResponse
from .worker import worker

def analytics_api(request):
    # Use sqlite-worker for analytics queries
    token = worker.execute("""
        SELECT date, COUNT(*) as views
        FROM page_views
        GROUP BY date
        ORDER BY date DESC
        LIMIT 30
    """)
    results = worker.fetch_results(token)
    
    return JsonResponse({
        'analytics': [
            {'date': r[0], 'views': r[1]}
            for r in results
        ]
    })
```

### 3. Management Commands

```python
# blog/management/commands/process_analytics.py
from django.core.management.base import BaseCommand
from blog.worker import worker
from blog.models import Post

class Command(BaseCommand):
    help = 'Process analytics data'
    
    def handle(self, *args, **options):
        # Get data from Django ORM
        posts = Post.objects.all()
        
        # Process with sqlite-worker
        with worker.transaction():
            for post in posts:
                worker.insert('analytics', {
                    'post_id': post.id,
                    'views': post.view_count,
                    'date': str(post.created_at.date())
                })
        
        self.stdout.write(
            self.style.SUCCESS('Analytics processed')
        )
```

## Use Cases

### 1. Analytics Dashboard

Store analytics in a separate database for better performance:

```python
# Log page views
worker.insert('page_views', {
    'url': request.path,
    'user_id': request.user.id,
    'timestamp': datetime.now().isoformat()
})

# Query for dashboard
token = worker.execute("""
    SELECT url, COUNT(*) as views
    FROM page_views
    WHERE date(timestamp) = date('now')
    GROUP BY url
    ORDER BY views DESC
    LIMIT 10
""")
```

### 2. Background Task Queue

```python
# Enqueue task
worker.insert('tasks', {
    'task_type': 'send_email',
    'payload': json.dumps({'to': user.email}),
    'status': 'pending'
})

# Worker process
def process_tasks():
    token = worker.select(
        'tasks',
        conditions={'status': 'pending'},
        limit=10
    )
    tasks = worker.fetch_results(token)
    
    for task in tasks:
        # Process task
        send_email(task)
        worker.update(
            'tasks',
            {'status': 'completed'},
            {'id': task[0]}
        )
```

### 3. Audit Logging

```python
# Log all model changes
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save)
def log_model_change(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    worker.insert('audit_log', {
        'model': sender.__name__,
        'object_id': instance.pk,
        'action': action,
        'timestamp': datetime.now().isoformat()
    })
```

### 4. Bulk Operations

```python
# Efficient bulk inserts
with worker.transaction():
    for record in large_dataset:
        worker.insert('bulk_data', {
            'field1': record['field1'],
            'field2': record['field2']
        })
```

## Configuration

### settings.py

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'blog',
]

# Optional: Configure worker database path
WORKER_DB_PATH = os.path.join(BASE_DIR, 'worker.db')

# Cleanup on shutdown
import atexit
from blog.worker import worker
atexit.register(lambda: worker.close())
```

## Running the Example

Since this is a documentation example, here's how to create a minimal working setup:

```bash
# Create and setup project
django-admin startproject myproject
cd myproject
python manage.py startapp myapp

# Add sqlite-worker integration
# (Copy code from examples above)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Best Practices

1. **Use Django ORM for Primary Data**
   - Models, relationships, authentication
   - Admin interface
   - Standard CRUD operations

2. **Use sqlite-worker for Specialized Cases**
   - High-volume logging
   - Analytics queries
   - Background processing
   - Temporary data

3. **Keep Databases Separate**
   - Don't mix Django models with worker tables
   - Use worker for auxiliary data
   - Maintain clear separation of concerns

4. **Handle Cleanup**
   - Close worker connections on shutdown
   - Use context managers for transactions
   - Implement proper error handling

## Performance Tips

1. **Connection Management**
   - Use singleton pattern for worker instance
   - Don't create new workers per request

2. **Query Optimization**
   - Create indexes on worker tables
   - Use transactions for bulk operations
   - Enable WAL mode

3. **Background Processing**
   - Use Celery with sqlite-worker for task queue
   - Process in batches
   - Implement retry logic

## Testing

```python
from django.test import TestCase
from blog.worker import worker

class WorkerTestCase(TestCase):
    def setUp(self):
        # Initialize test tables
        worker.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """)
    
    def test_insert(self):
        token = worker.insert('test_data', {'value': 'test'})
        result = worker.fetch_results(token)
        self.assertIsNotNone(result)
    
    def tearDown(self):
        worker.execute("DROP TABLE IF EXISTS test_data")
```

## Production Considerations

1. **Database Files**
   - Keep worker database separate from Django DB
   - Regular backups
   - Monitor database size

2. **Concurrency**
   - WAL mode for better concurrency
   - Handle database locks gracefully
   - Use worker pool for high load

3. **Monitoring**
   - Log worker operations
   - Monitor database performance
   - Track task queue depth

## Alternative: Celery Integration

For production task queues, consider using Celery with sqlite-worker:

```python
# tasks.py
from celery import shared_task
from .worker import worker

@shared_task
def process_analytics():
    # Use sqlite-worker in Celery task
    token = worker.execute("SELECT * FROM analytics")
    results = worker.fetch_results(token)
    # Process results...
```

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [sqlite-worker Documentation](https://github.com/roshanlam/sqlite-worker)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)
- [Celery Integration](https://docs.celeryproject.org/en/stable/django/)

## Summary

This integration pattern is ideal when you need:
- Django's ORM for primary application data
- sqlite-worker for specialized high-performance operations
- Separation of concerns between app data and auxiliary data
- Background task processing with simple queue

Choose this approach when you want the best of both worlds: Django's ecosystem and sqlite-worker's simplicity.
