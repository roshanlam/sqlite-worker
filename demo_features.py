#!/usr/bin/env python3
"""
Demonstration of all new sqlite-worker features.
This script showcases migrations, ORM, transactions, hooks, and auto-reconnection.
"""

import time
from sqlite_worker import SqliteWorker


def demo_migrations(worker):
    """Demonstrate database migration functionality."""
    print("\n=== Database Migrations Demo ===")
    
    # Apply migration to create users table
    migration_v1 = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT
        )
    """
    
    result = worker.apply_migration('001', 'create_users_table', migration_v1)
    print(f"Migration 001 applied: {result}")
    
    # Apply another migration to add posts table
    migration_v2 = """
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    
    result = worker.apply_migration('002', 'create_posts_table', migration_v2)
    print(f"Migration 002 applied: {result}")
    
    # Show applied migrations
    migrations = worker.get_applied_migrations()
    print(f"\nApplied migrations:")
    for version, name, applied_at in migrations:
        print(f"  - {version}: {name} (applied at {applied_at})")


def demo_orm_operations(worker):
    """Demonstrate ORM-like CRUD operations."""
    print("\n=== ORM Operations Demo ===")
    
    # Insert users
    print("\nInserting users...")
    token = worker.insert('users', {
        'username': 'alice',
        'email': 'alice@example.com'
    })
    worker.fetch_results(token)
    
    token = worker.insert('users', {
        'username': 'bob',
        'email': 'bob@example.com'
    })
    worker.fetch_results(token)
    
    token = worker.insert('users', {
        'username': 'charlie',
        'email': 'charlie@example.com'
    })
    worker.fetch_results(token)
    
    time.sleep(1)
    
    # Select all users
    print("\nSelecting all users:")
    token = worker.select('users', order_by='username')
    results = worker.fetch_results(token)
    for row in results:
        print(f"  - ID: {row[0]}, Username: {row[1]}, Email: {row[2]}")
    
    # Update a user
    print("\nUpdating Bob's email...")
    token = worker.update('users', 
        {'email': 'bob.updated@example.com'},
        {'username': 'bob'}
    )
    worker.fetch_results(token)
    time.sleep(1)
    
    # Select specific user
    token = worker.select('users', 
        columns=['username', 'email'],
        conditions={'username': 'bob'}
    )
    results = worker.fetch_results(token)
    print(f"  Updated user: {results[0]}")
    
    # Insert posts
    print("\nInserting posts...")
    token = worker.insert('posts', {
        'user_id': 1,
        'title': 'Alice First Post',
        'content': 'Hello World!'
    })
    worker.fetch_results(token)
    
    token = worker.insert('posts', {
        'user_id': 2,
        'title': 'Bob First Post',
        'content': 'Hi everyone!'
    })
    worker.fetch_results(token)
    
    time.sleep(1)
    
    # Select with limit
    print("\nSelecting posts (limited to 1):")
    token = worker.select('posts', limit=1, order_by='id')
    results = worker.fetch_results(token)
    for row in results:
        print(f"  - Post: {row[2]} by user_id {row[1]}")


def demo_transactions(worker):
    """Demonstrate transaction support."""
    print("\n=== Transactions Demo ===")
    
    # Successful transaction with context manager
    print("\nCommitting transaction (context manager)...")
    with worker.transaction():
        worker.insert('users', {
            'username': 'david',
            'email': 'david@example.com'
        })
        worker.insert('posts', {
            'user_id': 4,
            'title': 'David First Post',
            'content': 'Transaction test'
        })
    
    time.sleep(1)
    token = worker.select('users', conditions={'username': 'david'})
    results = worker.fetch_results(token)
    print(f"  User 'david' created: {len(results) > 0}")
    
    # Failed transaction (rollback)
    print("\nRolling back transaction due to error...")
    try:
        with worker.transaction():
            worker.insert('users', {
                'username': 'eve',
                'email': 'eve@example.com'
            })
            # This will cause a rollback
            raise ValueError("Simulated error")
    except ValueError:
        pass
    
    time.sleep(1)
    token = worker.select('users', conditions={'username': 'eve'})
    results = worker.fetch_results(token)
    print(f"  User 'eve' not created (rollback worked): {len(results) == 0}")


def demo_hooks(worker):
    """Demonstrate observable queries with hooks."""
    print("\n=== Observable Queries (Hooks) Demo ===")
    
    insert_count = {'count': 0}
    select_count = {'count': 0}
    
    def on_insert_hook(query, values):
        insert_count['count'] += 1
        print(f"  [Hook] INSERT detected: {values}")
    
    def on_select_hook(query, values):
        select_count['count'] += 1
        print(f"  [Hook] SELECT detected")
    
    # Register hooks
    print("\nRegistering hooks...")
    worker.register_hook('on_insert', on_insert_hook)
    worker.register_hook('on_select', on_select_hook)
    
    # Execute some queries
    print("\nExecuting queries (hooks will be triggered)...")
    token = worker.insert('users', {
        'username': 'frank',
        'email': 'frank@example.com'
    })
    worker.fetch_results(token)
    time.sleep(0.5)
    
    token = worker.select('users', conditions={'username': 'frank'})
    worker.fetch_results(token)
    time.sleep(0.5)
    
    print(f"\nHook statistics:")
    print(f"  - INSERT hooks triggered: {insert_count['count']}")
    print(f"  - SELECT hooks triggered: {select_count['count']}")
    
    # Unregister hooks
    worker.unregister_hook('on_insert', on_insert_hook)
    worker.unregister_hook('on_select', on_select_hook)
    print("\nHooks unregistered")


def demo_auto_reconnect(worker):
    """Demonstrate auto-reconnection capability."""
    print("\n=== Auto-Reconnection Demo ===")
    
    print(f"Auto-reconnect enabled: {worker.auto_reconnect}")
    print(f"Max retries: {worker.max_retries}")
    print(f"Retry delay: {worker.retry_delay}s")
    
    # Perform operations that benefit from auto-reconnect
    print("\nPerforming operations with auto-reconnect protection...")
    for i in range(3):
        token = worker.insert('posts', {
            'user_id': 1,
            'title': f'Post {i+1}',
            'content': f'Content {i+1}'
        })
        worker.fetch_results(token)
    
    time.sleep(1)
    print("  All operations completed successfully!")


def main():
    """Run all feature demonstrations."""
    print("=" * 60)
    print("SQLite-Worker Enhanced Features Demonstration")
    print("=" * 60)
    
    # Create worker with auto-reconnect enabled
    worker = SqliteWorker(
        'demo.db',
        auto_reconnect=True,
        max_retries=3,
        retry_delay=1.0
    )
    
    try:
        time.sleep(1)  # Wait for initialization
        
        # Run all demos
        demo_migrations(worker)
        demo_orm_operations(worker)
        demo_transactions(worker)
        demo_hooks(worker)
        demo_auto_reconnect(worker)
        
        print("\n" + "=" * 60)
        print("All demonstrations completed successfully!")
        print("=" * 60)
        
    finally:
        worker.close()
        print("\nWorker closed cleanly")


if __name__ == '__main__':
    main()
