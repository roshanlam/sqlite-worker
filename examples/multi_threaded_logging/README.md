# Multi-threaded Data Logging

A high-performance multi-threaded logging system demonstrating thread-safe concurrent logging with sqlite-worker.

## Features

- **Thread-Safe Logging**: Multiple threads can log simultaneously
- **High Performance**: WAL mode and batched commits
- **Structured Logging**: Organized log levels and metadata
- **Performance Metrics**: Track application performance
- **Fast Queries**: Indexed for quick log retrieval
- **Real-time Monitoring**: Hooks for live monitoring

## Installation

```bash
pip install sqlite-worker
```

## Running the Example

```bash
python logger.py
```

## Key Features

### 1. Thread-Safe Concurrent Logging

```python
# Multiple threads logging simultaneously
logger = MultiThreadedLogger()

def worker_thread():
    logger.log('INFO', 'worker', 'Processing task')
    logger.log_metric('task_duration', 123.45, 'ms')

# Start multiple threads
threads = [threading.Thread(target=worker_thread) for _ in range(10)]
for t in threads:
    t.start()
```

### 2. Structured Log Levels

```python
# Standard log levels
logger.log('DEBUG', 'module', 'Debug message')
logger.log('INFO', 'module', 'Info message')
logger.log('WARNING', 'module', 'Warning message')
logger.log('ERROR', 'module', 'Error message')
logger.log('CRITICAL', 'module', 'Critical message')
```

### 3. Performance Metrics

```python
# Log performance metrics
logger.log_metric('response_time', 45.2, 'ms')
logger.log_metric('memory_usage', 512, 'MB')
logger.log_metric('requests_per_second', 1250, 'req/s')
```

### 4. Rich Metadata

```python
# Include extra data with logs
logger.log('INFO', 'api', 'Request processed', extra={
    'user_id': 12345,
    'endpoint': '/api/users',
    'status_code': 200,
    'duration_ms': 23.4
})
```

### 5. Fast Queries

```python
# Get logs by level
error_logs = logger.get_logs(level='ERROR', limit=100)

# Get specific metrics
cpu_metrics = logger.get_metrics(metric_name='cpu_usage', limit=50)

# Get statistics
stats = logger.get_log_statistics()
```

## Use Cases

### 1. Application Logging

```python
class MyApplication:
    def __init__(self):
        self.logger = MultiThreadedLogger('app.db')
    
    def process_request(self, request):
        self.logger.log('INFO', 'api', f'Processing {request.path}')
        
        start_time = time.time()
        result = self.handle_request(request)
        duration = time.time() - start_time
        
        self.logger.log_metric('request_duration', duration * 1000, 'ms')
        return result
```

### 2. System Monitoring

```python
import psutil

def monitor_system(logger):
    while True:
        # Log system metrics
        logger.log_metric('cpu_percent', psutil.cpu_percent(), '%')
        logger.log_metric('memory_percent', psutil.virtual_memory().percent, '%')
        logger.log_metric('disk_usage', psutil.disk_usage('/').percent, '%')
        
        time.sleep(60)  # Every minute
```

### 3. Distributed System Logging

```python
# Log from multiple services
logger = MultiThreadedLogger('distributed_logs.db')

# Service A
logger.log('INFO', 'service_a', 'Request received', {
    'service': 'a',
    'request_id': 'req_123'
})

# Service B
logger.log('INFO', 'service_b', 'Processing request', {
    'service': 'b',
    'request_id': 'req_123'
})
```

### 4. Performance Profiling

```python
def profile_function(logger, func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        
        logger.log_metric(
            f'function_{func.__name__}_duration',
            duration,
            'ms'
        )
        
        return result
    return wrapper

@profile_function(logger)
def expensive_operation():
    # ... complex logic ...
    pass
```

## Performance Characteristics

### Benchmark Results

Running the example with 8 threads for 5 seconds:

```
✅ All workers completed in 5.12s

📊 Summary:
   Total Logs: 3,456
   Total Metrics: 3,456
   Logs per second: 675.29

📈 Logs by Level:
   DEBUG       864 ( 25.0%)
   INFO        864 ( 25.0%)
   WARNING     864 ( 25.0%)
   ERROR       864 ( 25.0%)
```

### Optimization Features

1. **WAL Mode**: Better concurrent write performance
2. **Batched Commits**: Commit every 100 inserts
3. **Large Cache**: 64MB cache for faster queries
4. **Indexed Queries**: Fast lookups by level, timestamp, thread

## Configuration Options

### Customize Batch Size

```python
logger = MultiThreadedLogger(
    db_path='logs.db',
    max_workers=10  # Number of worker threads
)

# Worker initialized with custom max_count
worker = SqliteWorker(
    db_path,
    max_count=500  # Commit every 500 inserts
)
```

### Custom Schema

```python
# Add custom fields to logs table
worker.execute("""
    ALTER TABLE logs ADD COLUMN hostname TEXT
""")

# Log with custom field
worker.execute("""
    INSERT INTO logs (timestamp, level, module, message, hostname)
    VALUES (?, ?, ?, ?, ?)
""", (timestamp, level, module, message, socket.gethostname()))
```

## Query Examples

### Find All Errors in Last Hour

```python
token = worker.execute("""
    SELECT timestamp, module, message
    FROM logs
    WHERE level = 'ERROR'
    AND timestamp >= datetime('now', '-1 hour')
    ORDER BY timestamp DESC
""")
errors = worker.fetch_results(token)
```

### Get Average Response Time

```python
token = worker.execute("""
    SELECT AVG(value) as avg_response_time
    FROM metrics
    WHERE metric_name = 'request_duration'
    AND timestamp >= datetime('now', '-1 hour')
""")
avg_time = worker.fetch_results(token)[0][0]
```

### Logs by Thread

```python
token = worker.execute("""
    SELECT thread_id, COUNT(*) as log_count
    FROM logs
    GROUP BY thread_id
    ORDER BY log_count DESC
""")
thread_stats = worker.fetch_results(token)
```

### Top 10 Slowest Operations

```python
token = worker.execute("""
    SELECT metric_name, MAX(value) as max_duration
    FROM metrics
    WHERE metric_name LIKE 'operation_duration_%'
    GROUP BY metric_name
    ORDER BY max_duration DESC
    LIMIT 10
""")
slowest = worker.fetch_results(token)
```

## Integration with Standard Logging

```python
import logging

class SqliteHandler(logging.Handler):
    def __init__(self, logger: MultiThreadedLogger):
        super().__init__()
        self.logger = logger
    
    def emit(self, record):
        self.logger.log(
            record.levelname,
            record.name,
            record.getMessage(),
            extra={
                'filename': record.filename,
                'lineno': record.lineno
            }
        )

# Use with Python's logging
handler = SqliteHandler(logger)
logging.getLogger().addHandler(handler)

logging.info("This goes to SQLite!")
```

## Production Considerations

1. **Log Rotation**
   - Implement periodic archival
   - Delete old logs based on retention policy

2. **Monitoring**
   - Set up alerts for ERROR/CRITICAL logs
   - Monitor database size
   - Track logging performance

3. **Backup**
   - Regular database backups
   - Export critical logs to external systems

4. **Performance**
   - Tune `max_count` based on volume
   - Create additional indexes for common queries
   - Consider partitioning for very large datasets

## Testing

```python
import unittest

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.logger = MultiThreadedLogger(':memory:')
    
    def test_logging(self):
        self.logger.log('INFO', 'test', 'Test message')
        logs = self.logger.get_logs(limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0][2], 'INFO')
    
    def test_metrics(self):
        self.logger.log_metric('test_metric', 123.45, 'ms')
        metrics = self.logger.get_metrics(limit=1)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0][2], 'test_metric')
```

## Resources

- [sqlite-worker Documentation](https://github.com/roshanlam/sqlite-worker)
- [Python Threading](https://docs.python.org/3/library/threading.html)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [Python Logging](https://docs.python.org/3/library/logging.html)

## Summary

This example demonstrates:
- ✅ Thread-safe concurrent logging
- ✅ High-performance write operations
- ✅ Structured log data with metadata
- ✅ Performance metric tracking
- ✅ Fast querying and reporting
- ✅ Production-ready patterns

Perfect for applications that need reliable, high-performance logging across multiple threads or processes.
