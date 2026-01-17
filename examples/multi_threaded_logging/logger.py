"""
Multi-threaded Data Logging System

This example demonstrates how to use sqlite-worker for high-performance
multi-threaded logging with proper thread safety.
"""

import threading
import time
import random
from datetime import datetime
from sqlite_worker import SqliteWorker
from typing import Dict, List
import logging
import sys


class MultiThreadedLogger:
    """High-performance multi-threaded logging system using sqlite-worker"""
    
    def __init__(self, db_path: str = "system_logs.db", max_workers: int = 5):
        """Initialize the logging system"""
        self.worker = SqliteWorker(
            db_path,
            execute_init=[
                "PRAGMA journal_mode=WAL;",
                "PRAGMA synchronous=NORMAL;",
                "PRAGMA cache_size=-64000;",  # 64MB cache
            ],
            max_count=100  # Commit every 100 inserts
        )
        
        self.max_workers = max_workers
        self._initialize_schema()
        
        # Setup hook for monitoring
        self.log_count = 0
        self.worker.register_hook('on_insert', self._count_logs)
    
    def _count_logs(self, query, values):
        """Hook to count log inserts"""
        if 'logs' in query.lower():
            self.log_count += 1
    
    def _initialize_schema(self):
        """Create logging tables with indexes"""
        # Main logs table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                thread_id INTEGER NOT NULL,
                module TEXT NOT NULL,
                message TEXT NOT NULL,
                extra_data TEXT
            )
        """)
        
        # Performance metrics table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT
            )
        """)
        
        # Create indexes for fast queries
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp 
            ON logs(timestamp)
        """)
        
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_level 
            ON logs(level)
        """)
        
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_thread 
            ON logs(thread_id)
        """)
        
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_name 
            ON metrics(metric_name, timestamp)
        """)
    
    def log(self, level: str, module: str, message: str, extra: Dict = None):
        """
        Log a message (thread-safe)
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            module: Module name
            message: Log message
            extra: Extra data as dictionary
        """
        import json
        
        self.worker.insert('logs', {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'thread_id': threading.get_ident(),
            'module': module,
            'message': message,
            'extra_data': json.dumps(extra) if extra else None
        })
    
    def log_metric(self, name: str, value: float, unit: str = None):
        """
        Log a performance metric (thread-safe)
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
        """
        self.worker.insert('metrics', {
            'timestamp': datetime.now().isoformat(),
            'metric_name': name,
            'value': value,
            'unit': unit
        })
    
    def get_logs(self, level: str = None, limit: int = 100) -> List[tuple]:
        """Get recent logs with optional level filter"""
        if level:
            token = self.worker.select(
                'logs',
                conditions={'level': level},
                order_by='timestamp DESC',
                limit=limit
            )
        else:
            token = self.worker.select(
                'logs',
                order_by='timestamp DESC',
                limit=limit
            )
        
        return self.worker.fetch_results(token)
    
    def get_metrics(self, metric_name: str = None, limit: int = 100) -> List[tuple]:
        """Get recent metrics with optional name filter"""
        if metric_name:
            token = self.worker.select(
                'metrics',
                conditions={'metric_name': metric_name},
                order_by='timestamp DESC',
                limit=limit
            )
        else:
            token = self.worker.select(
                'metrics',
                order_by='timestamp DESC',
                limit=limit
            )
        
        return self.worker.fetch_results(token)
    
    def get_log_statistics(self) -> Dict:
        """Get statistics about logged data"""
        # Total logs by level
        token = self.worker.execute("""
            SELECT level, COUNT(*) as count
            FROM logs
            GROUP BY level
            ORDER BY count DESC
        """)
        logs_by_level = self.worker.fetch_results(token)
        
        # Logs by thread
        token = self.worker.execute("""
            SELECT thread_id, COUNT(*) as count
            FROM logs
            GROUP BY thread_id
            ORDER BY count DESC
        """)
        logs_by_thread = self.worker.fetch_results(token)
        
        # Total count
        token = self.worker.execute("SELECT COUNT(*) FROM logs")
        total_logs = self.worker.fetch_results(token)[0][0]
        
        token = self.worker.execute("SELECT COUNT(*) FROM metrics")
        total_metrics = self.worker.fetch_results(token)[0][0]
        
        return {
            'total_logs': total_logs,
            'total_metrics': total_metrics,
            'logs_by_level': logs_by_level,
            'logs_by_thread': logs_by_thread
        }
    
    def close(self):
        """Close the database connection"""
        self.worker.close()


def simulate_worker_thread(logger: MultiThreadedLogger, worker_id: int, duration: int):
    """Simulate a worker thread doing work and logging"""
    thread_name = f"Worker-{worker_id}"
    start_time = time.time()
    
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    modules = ['database', 'api', 'auth', 'cache', 'worker']
    
    operations = 0
    
    while time.time() - start_time < duration:
        # Simulate some work
        work_duration = random.uniform(0.01, 0.1)
        time.sleep(work_duration)
        
        # Log the operation
        level = random.choice(log_levels)
        module = random.choice(modules)
        message = f"{thread_name} performed operation {operations + 1}"
        
        logger.log(level, module, message, {
            'worker_id': worker_id,
            'operation_id': operations,
            'duration_ms': work_duration * 1000
        })
        
        # Log performance metric
        logger.log_metric(
            f'operation_duration_{module}',
            work_duration * 1000,
            'ms'
        )
        
        operations += 1
    
    logger.log('INFO', thread_name, f'Completed {operations} operations')


def main():
    """Main demonstration"""
    print("=" * 60)
    print("Multi-threaded Data Logging Demo")
    print("=" * 60)
    
    # Initialize logger
    logger = MultiThreadedLogger(max_workers=5)
    
    logger.log('INFO', 'main', 'Logging system initialized')
    
    # Start worker threads
    num_workers = 8
    duration = 5  # seconds
    
    print(f"\nStarting {num_workers} worker threads...")
    print(f"Each worker will run for {duration} seconds")
    print("\nWorkers are logging operations concurrently...")
    
    threads = []
    start_time = time.time()
    
    for i in range(num_workers):
        thread = threading.Thread(
            target=simulate_worker_thread,
            args=(logger, i + 1, duration),
            name=f"Worker-{i + 1}"
        )
        thread.start()
        threads.append(thread)
    
    # Monitor progress
    while any(t.is_alive() for t in threads):
        time.sleep(0.5)
        print(f"  Logs written: {logger.log_count}", end='\r')
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    print(f"\n\n✅ All workers completed in {elapsed:.2f}s")
    
    # Display statistics
    print("\n" + "=" * 60)
    print("Logging Statistics")
    print("=" * 60)
    
    stats = logger.get_log_statistics()
    
    print(f"\n📊 Summary:")
    print(f"   Total Logs: {stats['total_logs']}")
    print(f"   Total Metrics: {stats['total_metrics']}")
    print(f"   Logs per second: {stats['total_logs'] / elapsed:.2f}")
    
    print(f"\n📈 Logs by Level:")
    for level, count in stats['logs_by_level']:
        percentage = (count / stats['total_logs']) * 100
        print(f"   {level:10} {count:6} ({percentage:5.1f}%)")
    
    print(f"\n🧵 Logs by Thread:")
    for thread_id, count in stats['logs_by_thread'][:5]:
        print(f"   Thread {thread_id}: {count} logs")
    
    # Show sample logs
    print(f"\n📝 Sample Logs (last 5):")
    recent_logs = logger.get_logs(limit=5)
    for log in recent_logs:
        timestamp = log[1].split('T')[1][:8]
        level = log[2]
        module = log[4]
        message = log[5]
        print(f"   [{timestamp}] {level:8} [{module:8}] {message}")
    
    # Show error logs specifically
    error_logs = logger.get_logs(level='ERROR', limit=5)
    if error_logs:
        print(f"\n❌ Recent Error Logs:")
        for log in error_logs[:3]:
            timestamp = log[1].split('T')[1][:8]
            module = log[4]
            message = log[5]
            print(f"   [{timestamp}] [{module}] {message}")
    
    # Show performance metrics
    print(f"\n⚡ Performance Metrics (sample):")
    metrics = logger.get_metrics(limit=5)
    for metric in metrics:
        timestamp = metric[1].split('T')[1][:8]
        name = metric[2]
        value = metric[3]
        unit = metric[4] or ''
        print(f"   [{timestamp}] {name}: {value:.2f} {unit}")
    
    # Cleanup
    logger.close()
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("=" * 60)
    print(f"\nDatabase file: system_logs.db")
    print("You can query the logs using any SQLite client")


if __name__ == "__main__":
    main()
