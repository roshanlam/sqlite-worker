import sqlite3
import threading
import time
import uuid
import random
import concurrent.futures
import os
import statistics
import matplotlib.pyplot as plt
import numpy as np
from contextlib import contextmanager

# Import your SqliteWorker class
# Assuming SqliteWorker.py is in the same directory
from sqlite_worker.main import SqliteWorker

# Constants for testing
DB_FILE_STANDARD = "standard_test.db"
DB_FILE_WORKER = "worker_test.db"
NUM_THREADS = [1, 2, 4, 8, 16, 32]  # Test with different thread counts
NUM_QUERIES_PER_THREAD = 1000
TEST_RUNS = 3  # Number of times to run each test for reliable results

# Test data
def generate_random_data(num_records=100):
    data = []
    for _ in range(num_records):
        data.append((
            uuid.uuid4().hex,
            random.randint(1, 1000),
            f"Item {random.randint(1, 1000)}",
            random.random() * 100
        ))
    return data

# Clean up database files before testing
def cleanup():
    for file in [DB_FILE_STANDARD, DB_FILE_WORKER]:
        if os.path.exists(file):
            os.remove(file)

# Set up the databases
def setup_databases():
    # Standard SQLite setup
    conn = sqlite3.connect(DB_FILE_STANDARD)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE items (
        id TEXT PRIMARY KEY,
        quantity INTEGER,
        name TEXT,
        price REAL
    )
    ''')
    conn.commit()
    conn.close()
    
    # SqliteWorker setup
    worker = SqliteWorker(DB_FILE_WORKER, execute_init=[
        '''
        CREATE TABLE items (
            id TEXT PRIMARY KEY,
            quantity INTEGER,
            name TEXT,
            price REAL
        )
        '''
    ])
    worker.close()

# Thread-safe connection for standard SQLite
@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_FILE_STANDARD)
    try:
        yield conn
    finally:
        conn.close()

# Standard SQLite worker function
def standard_worker(thread_id, lock, queries_per_thread):
    results = []
    
    for i in range(queries_per_thread):
        if i % 4 == 0:  # 25% are inserts
            item_id = f"{thread_id}-{i}-{uuid.uuid4().hex}"
            quantity = random.randint(1, 100)
            name = f"Item {thread_id}-{i}"
            price = random.random() * 100
            
            with get_connection() as conn:
                c = conn.cursor()
                start_time = time.time()
                try:
                    with lock:
                        c.execute(
                            "INSERT INTO items VALUES (?, ?, ?, ?)",
                            (item_id, quantity, name, price)
                        )
                        conn.commit()
                except sqlite3.Error as e:
                    print(f"Insert error: {e}")
                duration = time.time() - start_time
                results.append(duration)
        else:  # 75% are selects
            with get_connection() as conn:
                c = conn.cursor()
                start_time = time.time()
                try:
                    with lock:
                        c.execute("SELECT * FROM items ORDER BY RANDOM() LIMIT 10")
                        data = c.fetchall()
                except sqlite3.Error as e:
                    print(f"Select error: {e}")
                duration = time.time() - start_time
                results.append(duration)
    
    return results

# SqliteWorker worker function
def worker_worker(thread_id, worker, queries_per_thread):
    results = []
    
    for i in range(queries_per_thread):
        if i % 4 == 0:  # 25% are inserts
            item_id = f"{thread_id}-{i}-{uuid.uuid4().hex}"
            quantity = random.randint(1, 100)
            name = f"Item {thread_id}-{i}"
            price = random.random() * 100
            
            start_time = time.time()
            worker.execute(
                "INSERT INTO items VALUES (?, ?, ?, ?)",
                (item_id, quantity, name, price)
            )
            duration = time.time() - start_time
            results.append(duration)
        else:  # 75% are selects
            start_time = time.time()
            token = worker.execute(
                "SELECT * FROM items ORDER BY RANDOM() LIMIT 10"
            )
            data = worker.fetch_results(token)
            duration = time.time() - start_time
            results.append(duration)
    
    return results

# Preload the databases with some data
def preload_databases():
    data = generate_random_data(1000)
    
    # Preload standard SQLite
    conn = sqlite3.connect(DB_FILE_STANDARD)
    c = conn.cursor()
    c.executemany("INSERT INTO items VALUES (?, ?, ?, ?)", data)
    conn.commit()
    conn.close()
    
    # Preload SqliteWorker
    worker = SqliteWorker(DB_FILE_WORKER)
    for row in data:
        worker.execute("INSERT INTO items VALUES (?, ?, ?, ?)", row)
    worker.close()

def run_standard_test(num_threads, queries_per_thread):
    lock = threading.Lock()
    all_durations = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(standard_worker, i, lock, queries_per_thread) 
            for i in range(num_threads)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            all_durations.extend(future.result())
    
    return all_durations

def run_worker_test(num_threads, queries_per_thread):
    worker = SqliteWorker(DB_FILE_WORKER, max_queue_size=100000)
    all_durations = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(worker_worker, i, worker, queries_per_thread) 
            for i in range(num_threads)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            all_durations.extend(future.result())
    
    worker.close()
    return all_durations

def run_tests():
    results = {
        "standard": {},
        "worker": {},
        "improvement": {}
    }
    
    for thread_count in NUM_THREADS:
        standard_times = []
        worker_times = []
        
        for run in range(TEST_RUNS):
            print(f"Run {run+1}/{TEST_RUNS} with {thread_count} threads")
            cleanup()
            setup_databases()
            preload_databases()
            
            # Run standard SQLite test
            print(f"  Testing standard SQLite...")
            standard_durations = run_standard_test(thread_count, NUM_QUERIES_PER_THREAD)
            standard_total = sum(standard_durations)
            standard_times.append(standard_total)
            
            # Run SqliteWorker test
            print(f"  Testing SqliteWorker...")
            worker_durations = run_worker_test(thread_count, NUM_QUERIES_PER_THREAD)
            worker_total = sum(worker_durations)
            worker_times.append(worker_total)
        
        # Calculate average time across test runs
        avg_standard = statistics.mean(standard_times)
        avg_worker = statistics.mean(worker_times)
        
        # Calculate improvement percentage
        improvement = ((avg_standard - avg_worker) / avg_worker) * 100
        
        results["standard"][thread_count] = avg_standard
        results["worker"][thread_count] = avg_worker
        results["improvement"][thread_count] = improvement
        
        print(f"\nResults for {thread_count} threads:")
        print(f"  Standard SQLite: {avg_standard:.4f} seconds")
        print(f"  SqliteWorker: {avg_worker:.4f} seconds")
        print(f"  Improvement: {improvement:.2f}%")
        print(f"  Speed multiplier: {avg_standard/avg_worker:.2f}x\n")
    
    return results

def plot_results(results):
    plt.figure(figsize=(12, 10))
    
    # Plot 1: Execution Time Comparison
    plt.subplot(2, 1, 1)
    x = np.array(NUM_THREADS)
    width = 0.35
    
    standard_times = [results["standard"][t] for t in NUM_THREADS]
    worker_times = [results["worker"][t] for t in NUM_THREADS]
    
    plt.bar(x - width/2, standard_times, width, label='Standard SQLite')
    plt.bar(x + width/2, worker_times, width, label='SqliteWorker')
    
    plt.xlabel('Number of Threads')
    plt.ylabel('Total Execution Time (seconds)')
    plt.title('Execution Time Comparison')
    plt.xticks(x)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Plot 2: Performance Improvement
    plt.subplot(2, 1, 2)
    improvements = [results["improvement"][t] for t in NUM_THREADS]
    speedups = [results["standard"][t]/results["worker"][t] for t in NUM_THREADS]
    
    plt.plot(x, improvements, 'o-', label='Improvement %')
    plt.axhline(y=300, color='r', linestyle='--', label='300% Improvement Threshold')
    
    plt.xlabel('Number of Threads')
    plt.ylabel('Performance Improvement (%)')
    plt.title('Performance Improvement with SqliteWorker')
    plt.xticks(x)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add a text annotation with the speedup for each thread count
    for i, threads in enumerate(NUM_THREADS):
        plt.annotate(f"{speedups[i]:.2f}x faster", 
                    (x[i], improvements[i]),
                    textcoords="offset points",
                    xytext=(0,10), 
                    ha='center')
    
    plt.tight_layout()
    plt.savefig('sqlite_performance_comparison.png')
    plt.show()
    
    # Print the final analysis
    max_improvement = max(improvements)
    max_threads = NUM_THREADS[improvements.index(max_improvement)]
    avg_improvement = sum(improvements) / len(improvements)
    
    print("\nFinal Analysis:")
    print(f"Maximum improvement: {max_improvement:.2f}% with {max_threads} threads")
    print(f"Average improvement across all thread counts: {avg_improvement:.2f}%")
    
    for i, threads in enumerate(NUM_THREADS):
        print(f"With {threads} threads: {speedups[i]:.2f}x faster ({improvements[i]:.2f}% improvement)")
    
    if max_improvement >= 300:
        print("\nThe 300% performance improvement claim is verified!")
    else:
        print(f"\nThe actual maximum improvement is {max_improvement:.2f}%, not 300%")

if __name__ == "__main__":
    print("Starting SQLiteWorker Performance Test")
    results = run_tests()
    plot_results(results)
